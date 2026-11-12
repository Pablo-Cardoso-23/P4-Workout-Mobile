from datetime import datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import selectinload

from core.database import get_db_session
from models.workout_models import (
    Exercicio,
    Ficha,
    FichaExercicio,
    SerieExecutada,
    SessaoTreino,
)


def obter_metricas_resumo() -> dict[str, int]:
    """Retorna os contadores gerais do banco SQLite local."""
    with get_db_session() as session:
        total_exercicios = session.scalar(select(func.count(Exercicio.id))) or 0
        total_fichas = session.scalar(
            select(func.count(Ficha.id)).where(Ficha.ativa.is_(True))
        ) or 0
        total_sessoes = session.scalar(
            select(func.count(SessaoTreino.id)).where(SessaoTreino.data_fim.is_not(None))
        ) or 0
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


def finalizar_sessao(sessao_id: int, notas: str | None = None) -> SessaoTreino:
    """Encerra a sessão de treino gravando o timestamp de término e observações."""
    with get_db_session() as session:
        sessao = session.get(SessaoTreino, sessao_id)
        if sessao is None:
            raise ValueError(f"Sessão #{sessao_id} não encontrada.")
        sessao.data_fim = datetime.now()
        if notas is not None and notas.strip():
            sessao.notas = notas.strip()
        session.flush()
        return sessao
