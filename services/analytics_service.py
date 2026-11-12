from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import desc, func, select

from core.database import get_db_session
from models.nutrition_models import RegistroBiometria
from models.workout_models import Exercicio, SerieExecutada, SessaoTreino


def calcular_epley_1rm(carga_kg: float, repeticoes: int) -> float:
    """Calcula 1RM estimado pela Fórmula de Epley: 1RM = Carga * (1 + Reps / 30)."""
    if carga_kg <= 0 or repeticoes <= 0:
        return 0.0
    if repeticoes == 1:
        return round(float(carga_kg), 1)
    return round(float(carga_kg) * (1.0 + (float(repeticoes) / 30.0)), 1)


def _classificar_imc(imc: float) -> str:
    if imc < 18.5:
        return "Abaixo do Peso"
    if imc < 25.0:
        return "Peso Normal"
    if imc < 30.0:
        return "Sobrepeso"
    return "Obesidade"


def obter_metricas_gerais() -> dict[str, Any]:
    """Retorna KPIs gerais acumulados das sessões finalizadas e peso atual."""
    with get_db_session() as session:
        total_sessoes = (
            session.scalar(
                select(func.count(SessaoTreino.id)).where(
                    SessaoTreino.data_fim.is_not(None)
                )
            )
            or 0
        )

        tonelagem_total = (
            session.scalar(
                select(
                    func.coalesce(
                        func.sum(SerieExecutada.carga_kg * SerieExecutada.repeticoes),
                        0.0,
                    )
                )
                .join(SessaoTreino, SerieExecutada.sessao_id == SessaoTreino.id)
                .where(
                    SessaoTreino.data_fim.is_not(None),
                    SerieExecutada.tipo_serie.in_(["W", "F"]),
                )
            )
            or 0.0
        )

        total_series_validas = (
            session.scalar(
                select(func.count(SerieExecutada.id))
                .join(SessaoTreino, SerieExecutada.sessao_id == SessaoTreino.id)
                .where(
                    SessaoTreino.data_fim.is_not(None),
                    SerieExecutada.tipo_serie.in_(["W", "F"]),
                )
            )
            or 0
        )

        ultimo_peso = session.scalar(
            select(RegistroBiometria.peso_kg)
            .order_by(desc(RegistroBiometria.data), desc(RegistroBiometria.id))
            .limit(1)
        )
        if ultimo_peso is None:
            ultimo_peso = session.scalar(
                select(SessaoTreino.peso_corporal_kg)
                .where(
                    SessaoTreino.data_fim.is_not(None),
                    SessaoTreino.peso_corporal_kg.is_not(None),
                )
                .order_by(desc(SessaoTreino.data_fim), desc(SessaoTreino.id))
                .limit(1)
            )

        return {
            "total_sessoes": int(total_sessoes),
            "tonelagem_total_kg": round(float(tonelagem_total), 1),
            "total_series_validas": int(total_series_validas),
            "ultimo_peso_corporal_kg": (
                round(float(ultimo_peso), 1) if ultimo_peso is not None else None
            ),
        }


def obter_evolucao_exercicio(exercicio_id: int) -> list[dict[str, Any]]:
    """Retorna o histórico cronológico das sessões do exercício com PR, volume e 1RM (Epley)."""
    with get_db_session() as session:
        stmt = (
            select(SessaoTreino, SerieExecutada)
            .join(SerieExecutada, SerieExecutada.sessao_id == SessaoTreino.id)
            .where(
                SessaoTreino.data_fim.is_not(None),
                SerieExecutada.exercicio_id == exercicio_id,
                SerieExecutada.tipo_serie.in_(["W", "F"]),
            )
            .order_by(SessaoTreino.data_inicio.asc(), SerieExecutada.numero_serie.asc())
        )
        linhas = session.execute(stmt).all()

        agrupado_por_sessao: dict[int, dict[str, Any]] = {}
        for sessao, serie in linhas:
            sid = sessao.id
            data_ref = sessao.data_fim or sessao.data_inicio
            if sid not in agrupado_por_sessao:
                agrupado_por_sessao[sid] = {
                    "sessao_id": sid,
                    "data": data_ref.strftime("%d/%m"),
                    "data_completa": data_ref.strftime("%d/%m/%Y"),
                    "carga_maxima_kg": 0.0,
                    "volume_sessao_kg": 0.0,
                    "one_rm_estimado": 0.0,
                }

            registro = agrupado_por_sessao[sid]
            carga = float(serie.carga_kg)
            reps = int(serie.repeticoes)
            volume_serie = carga * reps
            epley_serie = calcular_epley_1rm(carga, reps)

            if carga > registro["carga_maxima_kg"]:
                registro["carga_maxima_kg"] = round(carga, 1)
            registro["volume_sessao_kg"] = round(
                registro["volume_sessao_kg"] + volume_serie, 1
            )
            if epley_serie > registro["one_rm_estimado"]:
                registro["one_rm_estimado"] = epley_serie

        return list(agrupado_por_sessao.values())


def obter_volume_por_grupo_muscular(dias: int = 30) -> dict[str, float]:
    """Soma a tonelagem válida (séries W e F) por grupo muscular nos últimos X dias."""
    data_corte = datetime.now() - timedelta(days=max(1, dias))
    with get_db_session() as session:
        stmt = (
            select(
                Exercicio.grupo_muscular,
                func.coalesce(
                    func.sum(SerieExecutada.carga_kg * SerieExecutada.repeticoes),
                    0.0,
                ),
            )
            .join(SerieExecutada, SerieExecutada.exercicio_id == Exercicio.id)
            .join(SessaoTreino, SerieExecutada.sessao_id == SessaoTreino.id)
            .where(
                SessaoTreino.data_fim.is_not(None),
                SessaoTreino.data_inicio >= data_corte,
                SerieExecutada.tipo_serie.in_(["W", "F"]),
            )
            .group_by(Exercicio.grupo_muscular)
            .order_by(
                desc(
                    func.coalesce(
                        func.sum(SerieExecutada.carga_kg * SerieExecutada.repeticoes),
                        0.0,
                    )
                )
            )
        )
        resultados = session.execute(stmt).all()
        return {str(grupo): round(float(vol), 1) for grupo, vol in resultados}


def listar_exercicios_para_analise() -> list[Exercicio]:
    """Lista os exercícios já treinados primeiro, seguidos pelos demais do catálogo."""
    with get_db_session() as session:
        ids_treinados = list(
            session.scalars(
                select(SerieExecutada.exercicio_id)
                .join(SessaoTreino, SerieExecutada.sessao_id == SessaoTreino.id)
                .where(SessaoTreino.data_fim.is_not(None))
                .distinct()
            ).all()
        )
        todos = list(
            session.scalars(
                select(Exercicio).order_by(Exercicio.grupo_muscular, Exercicio.nome)
            ).all()
        )
        treinados = [ex for ex in todos if ex.id in ids_treinados]
        nao_treinados = [ex for ex in todos if ex.id not in ids_treinados]
        return treinados + nao_treinados


def registrar_biometria(
    peso_kg: float,
    altura_cm: float,
    percentual_gordura: float | None = None,
    cintura_cm: float | None = None,
    braco_cm: float | None = None,
) -> RegistroBiometria:
    """Registra uma nova pesagem e medidas corporais no histórico biométrico."""
    if peso_kg <= 0 or altura_cm <= 0:
        raise ValueError("Peso e altura devem ser maiores que zero.")

    with get_db_session() as session:
        novo = RegistroBiometria(
            data=date.today(),
            peso_kg=round(float(peso_kg), 1),
            altura_cm=round(float(altura_cm), 1),
            percentual_gordura=(
                round(float(percentual_gordura), 1)
                if percentual_gordura is not None
                else None
            ),
            cintura_cm=(
                round(float(cintura_cm), 1) if cintura_cm is not None else None
            ),
            braco_cm=round(float(braco_cm), 1) if braco_cm is not None else None,
        )
        session.add(novo)
        session.flush()
        return novo


def obter_historico_biometria() -> dict[str, Any]:
    """Retorna o histórico cronológico de biometria e os indicadores calculados."""
    with get_db_session() as session:
        registros = list(
            session.scalars(
                select(RegistroBiometria).order_by(
                    RegistroBiometria.data.asc(), RegistroBiometria.id.asc()
                )
            ).all()
        )

        if not registros:
            peso_atual = 77.6
            altura_cm = 190.0
            variacao_peso = 0.0
            bf_atual = None
            cintura_atual = None
            braco_atual = None
            pontos_historico: list[dict[str, Any]] = []
        else:
            primeiro = registros[0]
            ultimo = registros[-1]
            peso_atual = float(ultimo.peso_kg)
            altura_cm = float(ultimo.altura_cm)
            variacao_peso = round(peso_atual - float(primeiro.peso_kg), 1)
            bf_atual = ultimo.percentual_gordura
            cintura_atual = ultimo.cintura_cm
            braco_atual = ultimo.braco_cm
            pontos_historico = [
                {
                    "id": r.id,
                    "data": r.data.strftime("%d/%m"),
                    "peso_kg": round(float(r.peso_kg), 1),
                }
                for r in registros
            ]

        altura_m = max(0.5, altura_cm / 100.0)
        imc = round(peso_atual / (altura_m * altura_m), 1)
        classificacao_imc = _classificar_imc(imc)

        # Fórmula de Mifflin-St Jeor (21 anos, masculino): 10*peso + 6.25*altura_cm - 5*21 + 5
        tmb_kcal = int(round((10.0 * peso_atual) + (6.25 * altura_cm) - (5.0 * 21.0) + 5.0))

        # Melhor carga em Supino ou Agachamento para relação Força/Peso
        melhor_carga_composto = (
            session.scalar(
                select(func.max(SerieExecutada.carga_kg))
                .join(Exercicio, SerieExecutada.exercicio_id == Exercicio.id)
                .join(SessaoTreino, SerieExecutada.sessao_id == SessaoTreino.id)
                .where(
                    SessaoTreino.data_fim.is_not(None),
                    SerieExecutada.tipo_serie.in_(["W", "F"]),
                    (
                        Exercicio.nome.ilike("%Supino%")
                        | Exercicio.nome.ilike("%Agachamento%")
                    ),
                )
            )
            or 0.0
        )
        forca_relativa = (
            round(float(melhor_carga_composto) / max(1.0, peso_atual), 2)
            if melhor_carga_composto > 0
            else 0.0
        )

        return {
            "historico": pontos_historico,
            "peso_atual_kg": round(peso_atual, 1),
            "altura_cm": round(altura_cm, 1),
            "imc": imc,
            "classificacao_imc": classificacao_imc,
            "tmb_kcal": tmb_kcal,
            "forca_relativa": forca_relativa,
            "melhor_carga_composto_kg": round(float(melhor_carga_composto), 1),
            "variacao_peso_kg": variacao_peso,
            "percentual_gordura": bf_atual,
            "cintura_cm": cintura_atual,
            "braco_cm": braco_atual,
        }
