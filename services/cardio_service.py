from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc, func, select

from core.database import get_db_session
from models.cardio_models import SessaoCardio
from models.nutrition_models import RegistroBiometria

MODALIDADES_CARDIO = [
    "Corrida Rua",
    "Esteira",
    "Ciclismo",
    "Escada",
    "Elíptico",
    "Caminhada",
    "HIIT",
]

TABELA_METS: dict[str, float] = {
    "Corrida Rua": 9.8,
    "Esteira": 9.0,
    "Ciclismo": 7.5,
    "Escada": 8.8,
    "Elíptico": 7.0,
    "Caminhada": 4.3,
    "HIIT": 10.5,
}


def formatar_tempo_segundos(segundos_totais: int) -> str:
    """Formata segundos em hh:mm:ss ou mm:ss."""
    segs = max(0, int(segundos_totais))
    horas, resto = divmod(segs, 3600)
    minutos, segundos = divmod(resto, 60)
    if horas > 0:
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
    return f"{minutos:02d}:{segundos:02d}"


def _obter_peso_atual_usuario() -> float:
    with get_db_session() as session:
        peso = session.scalar(
            select(RegistroBiometria.peso_kg)
            .order_by(desc(RegistroBiometria.data), desc(RegistroBiometria.id))
            .limit(1)
        )
        return float(peso) if peso is not None else 77.6


def calcular_metricas_cardio(
    modalidade: str,
    duracao_segundos: int,
    distancia_km: float,
    peso_usuario_kg: float = 77.6,
) -> dict[str, Any]:
    """Calcula Pace Médio (mm:ss /km), Velocidade Média (km/h) e Calorias via METs."""
    duracao = max(1, int(duracao_segundos))
    dist = max(0.0, float(distancia_km))
    horas = duracao / 3600.0

    if dist > 0.0:
        velocidade_kmh = round(dist / horas, 1)
        segundos_por_km = int(round(duracao / dist))
        pace_min, pace_seg = divmod(segundos_por_km, 60)
        pace_str = f"{pace_min}:{pace_seg:02d} /km"
    else:
        velocidade_kmh = 0.0
        pace_str = None

    met_base = TABELA_METS.get(modalidade, 8.0)
    if modalidade in {"Corrida Rua", "Esteira"} and velocidade_kmh >= 12.0:
        met_base = 11.5
    elif modalidade in {"Corrida Rua", "Esteira"} and 0.0 < velocidade_kmh < 8.0:
        met_base = 7.5

    calorias = max(1, int(round(met_base * float(peso_usuario_kg) * horas)))

    return {
        "pace_medio_str": pace_str,
        "velocidade_media_kmh": velocidade_kmh,
        "calorias_estimadas": calorias,
    }


def registrar_sessao_cardio(
    modalidade: str,
    duracao_segundos: int,
    distancia_km: float = 0.0,
    fc_media: int | None = None,
    percepcao_esforco: int = 7,
    notas: str | None = None,
) -> SessaoCardio:
    """Registra uma sessão de cardio calculando pace, velocidade e calorias automaticamente."""
    if duracao_segundos <= 0:
        raise ValueError("A duração do treino cardio deve ser maior que zero.")

    mod_limpa = modalidade.strip() if modalidade else "Corrida Rua"
    peso_atual = _obter_peso_atual_usuario()
    metricas = calcular_metricas_cardio(
        modalidade=mod_limpa,
        duracao_segundos=duracao_segundos,
        distancia_km=distancia_km,
        peso_usuario_kg=peso_atual,
    )

    rpe_val = min(10, max(1, int(percepcao_esforco)))

    with get_db_session() as session:
        nova = SessaoCardio(
            data=datetime.now(),
            modalidade=mod_limpa,
            duracao_segundos=int(duracao_segundos),
            distancia_km=round(max(0.0, float(distancia_km)), 2),
            pace_medio_str=metricas["pace_medio_str"],
            velocidade_media_kmh=metricas["velocidade_media_kmh"],
            calorias_estimadas=metricas["calorias_estimadas"],
            fc_media=int(fc_media) if (fc_media is not None and fc_media > 0) else None,
            percepcao_esforco=rpe_val,
            notas=notas.strip() if (notas and notas.strip()) else None,
        )
        session.add(nova)
        session.flush()
        return nova


def listar_sessoes_cardio(limite: int = 20) -> list[SessaoCardio]:
    """Retorna o histórico recente de sessões de cardio ordenado por data decrescente."""
    with get_db_session() as session:
        stmt = (
            select(SessaoCardio)
            .order_by(desc(SessaoCardio.data), desc(SessaoCardio.id))
            .limit(max(1, limite))
        )
        return list(session.scalars(stmt).all())


def excluir_sessao_cardio(sessao_id: int) -> None:
    """Remove uma sessão de cardio do banco de dados."""
    with get_db_session() as session:
        sessao = session.get(SessaoCardio, sessao_id)
        if sessao is not None:
            session.delete(sessao)


def obter_resumo_cardio(dias: int = 30) -> dict[str, Any]:
    """Retorna distância total (km), tempo total formatado, pace médio geral e calorias no período."""
    data_corte = datetime.now() - timedelta(days=max(1, dias))
    with get_db_session() as session:
        stmt = select(SessaoCardio).where(SessaoCardio.data >= data_corte)
        sessoes = list(session.scalars(stmt).all())

        total_sessoes = len(sessoes)
        distancia_total_km = round(
            sum(float(s.distancia_km) for s in sessoes), 2
        )
        duracao_total_seg = sum(int(s.duracao_segundos) for s in sessoes)
        calorias_totais = sum(int(s.calorias_estimadas) for s in sessoes)

        # Pace médio ponderado das sessões que possuem distância > 0
        seg_com_dist = sum(
            int(s.duracao_segundos) for s in sessoes if float(s.distancia_km) > 0
        )
        if distancia_total_km > 0 and seg_com_dist > 0:
            seg_por_km = int(round(seg_com_dist / distancia_total_km))
            p_min, p_seg = divmod(seg_por_km, 60)
            pace_geral = f"{p_min}:{p_seg:02d} /km"
        else:
            pace_geral = "-- /km"

        return {
            "total_sessoes": total_sessoes,
            "distancia_total_km": distancia_total_km,
            "duracao_total_segundos": duracao_total_seg,
            "tempo_total_fmt": formatar_tempo_segundos(duracao_total_seg),
            "pace_medio_geral": pace_geral,
            "calorias_totais": calorias_totais,
        }
