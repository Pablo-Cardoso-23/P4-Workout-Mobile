from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import selectinload

from core.database import get_db_session
from models.nutrition_models import RegistroBiometria
from models.workout_models import (
    Exercicio,
    Ficha,
    FichaExercicio,
    SerieExecutada,
    SessaoTreino,
)


def _formatar_duracao(segundos: int | None) -> str:
    if not segundos or segundos <= 0:
        return "-- min"
    minutos_totais = max(1, int(round(segundos / 60.0)))
    horas, mins = divmod(minutos_totais, 60)
    if horas > 0:
        return f"{horas}h {mins:02d}min"
    return f"{mins} min"


def _classificar_intensidade_sessao(
    kcal_por_min: float,
    fc_media: int | None,
    percepcao_esforco: int | None,
) -> str:
    """Deriva o índice de intensidade combinando densidade calórica, FC média e RPE."""
    score = 0.0
    if kcal_por_min >= 9.0:
        score += 3.0
    elif kcal_por_min >= 7.0:
        score += 2.0
    elif kcal_por_min >= 5.0:
        score += 1.0

    if fc_media is not None and fc_media > 0:
        if fc_media >= 155:
            score += 3.0
        elif fc_media >= 135:
            score += 2.0
        elif fc_media >= 115:
            score += 1.0
    else:
        score += 1.5

    rpe = percepcao_esforco if percepcao_esforco is not None else 7
    if rpe >= 9:
        score += 3.0
    elif rpe >= 8:
        score += 2.0
    elif rpe >= 6:
        score += 1.0

    if score >= 7.5:
        return "Extrema"
    if score >= 5.5:
        return "Alta"
    if score >= 3.5:
        return "Moderada"
    return "Leve"


def _obter_peso_referencia(session: Any, peso_sessao: float | None = None) -> float:
    if peso_sessao is not None and peso_sessao > 0:
        return float(peso_sessao)
    peso_bio = session.scalar(
        select(RegistroBiometria.peso_kg)
        .order_by(desc(RegistroBiometria.data), desc(RegistroBiometria.id))
        .limit(1)
    )
    return float(peso_bio) if peso_bio is not None else 77.6


def obter_metricas_resumo() -> dict[str, int]:
    """Retorna os contadores gerais do banco SQLite local."""
    with get_db_session() as session:
        total_exercicios = session.scalar(select(func.count(Exercicio.id))) or 0
        total_fichas = (
            session.scalar(
                select(func.count(Ficha.id)).where(Ficha.ativa.is_(True))
            )
            or 0
        )
        total_sessoes = (
            session.scalar(
                select(func.count(SessaoTreino.id)).where(
                    SessaoTreino.data_fim.is_not(None)
                )
            )
            or 0
        )
        return {
            "total_exercicios": total_exercicios,
            "total_fichas": total_fichas,
            "total_sessoes": total_sessoes,
        }


def listar_exercicios(grupo_muscular: str | None = None) -> list[Exercicio]:
    """Lista os exercícios do catálogo local, opcionalmente filtrados por grupo muscular."""
    with get_db_session() as session:
        stmt = select(Exercicio).order_by(Exercicio.grupo_muscular, Exercicio.nome)
        if grupo_muscular:
            stmt = stmt.where(Exercicio.grupo_muscular == grupo_muscular)
        return list(session.scalars(stmt).all())


def criar_exercicio(nome: str, grupo_muscular: str, equipamento: str) -> Exercicio:
    """Cadastra um novo exercício no catálogo local."""
    nome_limpo = nome.strip()
    if not nome_limpo:
        raise ValueError("O nome do exercício é obrigatório.")

    with get_db_session() as session:
        existente = session.scalar(
            select(Exercicio).where(func.lower(Exercicio.nome) == nome_limpo.lower())
        )
        if existente:
            raise ValueError(f"O exercício '{nome_limpo}' já existe no catálogo.")

        novo = Exercicio(
            nome=nome_limpo,
            grupo_muscular=grupo_muscular.strip(),
            equipamento=equipamento.strip(),
        )
        session.add(novo)
        session.flush()
        return novo


def listar_fichas(apenas_ativas: bool = True) -> list[Ficha]:
    """Lista as fichas de treino com seus exercícios ordenados."""
    with get_db_session() as session:
        stmt = (
            select(Ficha)
            .options(selectinload(Ficha.itens).joinedload(FichaExercicio.exercicio))
            .order_by(Ficha.id)
        )
        if apenas_ativas:
            stmt = stmt.where(Ficha.ativa.is_(True))
        return list(session.scalars(stmt).all())


def obter_ficha_por_id(ficha_id: int) -> Ficha | None:
    """Busca uma ficha específica com seus itens carregados."""
    with get_db_session() as session:
        stmt = (
            select(Ficha)
            .where(Ficha.id == ficha_id)
            .options(selectinload(Ficha.itens).joinedload(FichaExercicio.exercicio))
        )
        return session.scalar(stmt)


def criar_ficha(nome: str, descricao: str, itens: list[dict[str, Any]]) -> Ficha:
    """Cria uma nova ficha de treino com a lista ordenada de exercícios."""
    nome_limpo = nome.strip()
    if not nome_limpo:
        raise ValueError("O nome da ficha é obrigatório.")
    if not itens:
        raise ValueError("Adicione pelo menos 1 exercício na ficha.")

    with get_db_session() as session:
        nova_ficha = Ficha(
            nome=nome_limpo,
            descricao=descricao.strip() if descricao else None,
            ativa=True,
        )
        session.add(nova_ficha)
        session.flush()

        for idx, item in enumerate(itens, start=1):
            vinculo = FichaExercicio(
                ficha_id=nova_ficha.id,
                exercicio_id=int(item["exercicio_id"]),
                ordem=int(item.get("ordem", idx)),
                series_alvo=int(item.get("series_alvo", 4)),
                reps_alvo=str(item.get("reps_alvo", "8-12")).strip() or "8-12",
                descanso_segundos=int(item.get("descanso_segundos", 90)),
            )
            session.add(vinculo)

        session.flush()
        stmt = (
            select(Ficha)
            .where(Ficha.id == nova_ficha.id)
            .options(selectinload(Ficha.itens).joinedload(FichaExercicio.exercicio))
        )
        return session.scalar(stmt) or nova_ficha


def excluir_ficha(ficha_id: int) -> None:
    """Remove uma ficha de treino do banco de dados."""
    with get_db_session() as session:
        ficha = session.get(Ficha, ficha_id)
        if ficha is not None:
            session.delete(ficha)


def mover_exercicio_ficha(ficha_exercicio_id: int, direcao: str) -> None:
    """Move um exercício para cima ('subir') ou para baixo ('descer') na ficha e reindexa 1..N."""
    dir_limpa = direcao.strip().lower()
    if dir_limpa not in {"subir", "descer"}:
        raise ValueError("A direção deve ser 'subir' ou 'descer'.")

    with get_db_session() as session:
        alvo = session.get(FichaExercicio, ficha_exercicio_id)
        if alvo is None:
            raise ValueError(f"Item de ficha #{ficha_exercicio_id} não encontrado.")

        stmt = (
            select(FichaExercicio)
            .where(FichaExercicio.ficha_id == alvo.ficha_id)
            .order_by(FichaExercicio.ordem.asc(), FichaExercicio.id.asc())
        )
        itens = list(session.scalars(stmt).all())

        # Normaliza índices sequenciais 1..N
        indice_alvo = -1
        for idx, item in enumerate(itens):
            item.ordem = idx + 1
            if item.id == ficha_exercicio_id:
                indice_alvo = idx

        if indice_alvo == -1:
            return

        if dir_limpa == "subir" and indice_alvo > 0:
            vizinho = itens[indice_alvo - 1]
            alvo.ordem, vizinho.ordem = vizinho.ordem, alvo.ordem
        elif dir_limpa == "descer" and indice_alvo < len(itens) - 1:
            vizinho = itens[indice_alvo + 1]
            alvo.ordem, vizinho.ordem = vizinho.ordem, alvo.ordem

        session.flush()


def remover_exercicio_ficha(ficha_exercicio_id: int) -> None:
    """Remove um exercício de uma ficha existente e reindexa a ordem dos restantes (1..N)."""
    with get_db_session() as session:
        alvo = session.get(FichaExercicio, ficha_exercicio_id)
        if alvo is None:
            return
        fid = alvo.ficha_id
        session.delete(alvo)
        session.flush()

        restantes = list(
            session.scalars(
                select(FichaExercicio)
                .where(FichaExercicio.ficha_id == fid)
                .order_by(FichaExercicio.ordem.asc(), FichaExercicio.id.asc())
            ).all()
        )
        for idx, item in enumerate(restantes, start=1):
            item.ordem = idx
        session.flush()


def obter_ultima_execucao_exercicio(exercicio_id: int) -> list[SerieExecutada]:
    """Retorna as séries da última sessão finalizada daquele exercício para Auto-fill."""
    with get_db_session() as session:
        stmt_ultima_sessao = (
            select(SessaoTreino.id)
            .join(SerieExecutada, SerieExecutada.sessao_id == SessaoTreino.id)
            .where(
                SerieExecutada.exercicio_id == exercicio_id,
                SessaoTreino.data_fim.is_not(None),
            )
            .order_by(desc(SessaoTreino.data_fim), desc(SessaoTreino.id))
            .limit(1)
        )
        ultima_sessao_id = session.scalar(stmt_ultima_sessao)
        if ultima_sessao_id is None:
            return []

        stmt_series = (
            select(SerieExecutada)
            .where(
                SerieExecutada.sessao_id == ultima_sessao_id,
                SerieExecutada.exercicio_id == exercicio_id,
            )
            .order_by(SerieExecutada.numero_serie, SerieExecutada.id)
        )
        return list(session.scalars(stmt_series).all())


def iniciar_sessao(
    ficha_id: int | None, peso_corporal_kg: float | None = None
) -> SessaoTreino:
    """Abre uma nova sessão de treino no banco de dados."""
    with get_db_session() as session:
        nova_sessao = SessaoTreino(
            ficha_id=ficha_id,
            data_inicio=datetime.now(),
            peso_corporal_kg=peso_corporal_kg,
        )
        session.add(nova_sessao)
        session.flush()
        stmt = (
            select(SessaoTreino)
            .where(SessaoTreino.id == nova_sessao.id)
            .options(selectinload(SessaoTreino.series))
        )
        return session.scalar(stmt) or nova_sessao


def registrar_serie(
    sessao_id: int,
    exercicio_id: int,
    numero_serie: int,
    carga_kg: float,
    repeticoes: int,
    rir: int | None,
    tipo_serie: str,
) -> SerieExecutada:
    """Salva ou atualiza uma série executada durante a sessão ativa."""
    with get_db_session() as session:
        existente = session.scalar(
            select(SerieExecutada).where(
                SerieExecutada.sessao_id == sessao_id,
                SerieExecutada.exercicio_id == exercicio_id,
                SerieExecutada.numero_serie == numero_serie,
            )
        )
        if existente is not None:
            existente.carga_kg = float(carga_kg)
            existente.repeticoes = int(repeticoes)
            existente.rir = int(rir) if rir is not None else None
            existente.tipo_serie = tipo_serie.strip().upper() or "W"
            session.flush()
            return existente

        serie = SerieExecutada(
            sessao_id=sessao_id,
            exercicio_id=exercicio_id,
            numero_serie=numero_serie,
            carga_kg=float(carga_kg),
            repeticoes=int(repeticoes),
            rir=int(rir) if rir is not None else None,
            tipo_serie=tipo_serie.strip().upper() or "W",
        )
        session.add(serie)
        session.flush()
        return serie


def finalizar_sessao(
    sessao_id: int,
    notas: str | None = None,
    fc_media: int | None = None,
    percepcao_esforco: int | None = None,
    calorias_manuais: int | None = None,
) -> SessaoTreino:
    """Encerra a sessão de treino calculando duração, calorias (manual ou 6.0 METs), FC e RPE."""
    with get_db_session() as session:
        sessao = session.get(SessaoTreino, sessao_id)
        if sessao is None:
            raise ValueError(f"Sessão #{sessao_id} não encontrada.")

        agora = datetime.now()
        sessao.data_fim = agora
        duracao_seg = max(
            60, int(round((agora - sessao.data_inicio).total_seconds()))
        )
        sessao.duracao_segundos = duracao_seg

        if calorias_manuais is not None and int(calorias_manuais) > 0:
            sessao.calorias_estimadas = int(calorias_manuais)
        else:
            peso_ref = _obter_peso_referencia(session, sessao.peso_corporal_kg)
            horas = duracao_seg / 3600.0
            sessao.calorias_estimadas = max(1, int(round(6.0 * peso_ref * horas)))

        if fc_media is not None and fc_media > 0:
            sessao.fc_media = int(fc_media)
        if percepcao_esforco is not None:
            sessao.percepcao_esforco = min(10, max(1, int(percepcao_esforco)))
        if notas is not None and notas.strip():
            sessao.notas = notas.strip()

        session.flush()
        return sessao


def registrar_treino_muscular_manual(
    ficha_id: int | None,
    data_treino: datetime,
    duracao_minutos: int,
    fc_media: int | None = None,
    percepcao_esforco: int = 8,
    notas: str | None = None,
    series_manuais: list[dict[str, Any]] | None = None,
    calorias_manuais: int | None = None,
) -> SessaoTreino:
    """Registra manualmente uma sessão de musculação já finalizada com duração, FC, RPE, calorias e séries."""
    if duracao_minutos <= 0:
        raise ValueError("A duração em minutos deve ser maior que zero.")

    duracao_seg = int(duracao_minutos) * 60
    data_fim = data_treino
    data_inicio = data_treino - timedelta(seconds=duracao_seg)

    with get_db_session() as session:
        peso_ref = _obter_peso_referencia(session)
        if calorias_manuais is not None and int(calorias_manuais) > 0:
            calorias = int(calorias_manuais)
        else:
            calorias = max(1, int(round(6.0 * peso_ref * (duracao_seg / 3600.0))))

        nova_sessao = SessaoTreino(
            ficha_id=ficha_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            peso_corporal_kg=peso_ref,
            duracao_segundos=duracao_seg,
            fc_media=int(fc_media) if (fc_media is not None and fc_media > 0) else None,
            calorias_estimadas=calorias,
            percepcao_esforco=min(10, max(1, int(percepcao_esforco))),
            notas=notas.strip() if (notas and notas.strip()) else None,
        )
        session.add(nova_sessao)
        session.flush()

        if series_manuais:
            for idx, item in enumerate(series_manuais, start=1):
                serie = SerieExecutada(
                    sessao_id=nova_sessao.id,
                    exercicio_id=int(item["exercicio_id"]),
                    numero_serie=int(item.get("numero_serie", idx)),
                    carga_kg=float(item.get("carga_kg", 0.0)),
                    repeticoes=int(item.get("repeticoes", 0)),
                    rir=int(item["rir"]) if item.get("rir") is not None else None,
                    tipo_serie=str(item.get("tipo_serie", "W")).upper(),
                )
                session.add(serie)
            session.flush()

        stmt = (
            select(SessaoTreino)
            .where(SessaoTreino.id == nova_sessao.id)
            .options(selectinload(SessaoTreino.series))
        )
        return session.scalar(stmt) or nova_sessao


def listar_historico_sessoes(limite: int = 20) -> list[dict[str, Any]]:
    """Retorna as sessões finalizadas ordenadas da mais recente para a mais antiga."""
    with get_db_session() as session:
        stmt = (
            select(SessaoTreino)
            .where(SessaoTreino.data_fim.is_not(None))
            .options(
                selectinload(SessaoTreino.ficha),
                selectinload(SessaoTreino.series).joinedload(SerieExecutada.exercicio),
            )
            .order_by(desc(SessaoTreino.data_fim), desc(SessaoTreino.id))
            .limit(max(1, limite))
        )
        sessoes = list(session.scalars(stmt).all())

        resultado: list[dict[str, Any]] = []
        for s in sessoes:
            nome_ficha = s.ficha.nome if s.ficha is not None else "Treino Livre"
            data_ref = s.data_fim or s.data_inicio
            duracao_seg = s.duracao_segundos
            if duracao_seg is None and s.data_fim is not None:
                duracao_seg = max(
                    60, int(round((s.data_fim - s.data_inicio).total_seconds()))
                )

            tonelagem = round(
                sum(float(sr.carga_kg) * int(sr.repeticoes) for sr in s.series),
                1,
            )
            total_series = len(s.series)
            calorias = s.calorias_estimadas
            if calorias is None and duracao_seg:
                calorias = max(1, int(round(6.0 * 77.6 * (duracao_seg / 3600.0))))

            calorias_finais = int(calorias or 0)
            minutos_duracao = (duracao_seg / 60.0) if (duracao_seg and duracao_seg > 0) else 0.0
            kcal_por_min = (
                round(calorias_finais / minutos_duracao, 1)
                if minutos_duracao > 0
                else 0.0
            )
            intensidade_sessao = _classificar_intensidade_sessao(
                kcal_por_min=kcal_por_min,
                fc_media=s.fc_media,
                percepcao_esforco=s.percepcao_esforco,
            )

            resumo_exercicios = [
                f"{sr.exercicio.nome if sr.exercicio else 'Ex'}: {sr.carga_kg:g}kg x {sr.repeticoes}"
                for sr in s.series[:4]
            ]

            resultado.append(
                {
                    "id": s.id,
                    "nome_ficha": nome_ficha,
                    "data_fmt": data_ref.strftime("%d/%m/%Y %H:%M"),
                    "duracao_fmt": _formatar_duracao(duracao_seg),
                    "tonelagem_kg": tonelagem,
                    "total_series": total_series,
                    "fc_media": s.fc_media,
                    "calorias_estimadas": calorias_finais,
                    "kcal_por_min": kcal_por_min,
                    "intensidade_sessao": intensidade_sessao,
                    "percepcao_esforco": s.percepcao_esforco,
                    "notas": s.notas,
                    "resumo_exercicios": resumo_exercicios,
                }
            )
        return resultado


def excluir_sessao(sessao_id: int) -> None:
    """Remove uma sessão de treino muscular do banco de dados."""
    with get_db_session() as session:
        sessao = session.get(SessaoTreino, sessao_id)
        if sessao is not None:
            session.delete(sessao)
