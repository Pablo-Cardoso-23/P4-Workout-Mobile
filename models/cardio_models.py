from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class SessaoCardio(Base):
    __tablename__ = "sessoes_cardio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, index=True, nullable=False
    )
    modalidade: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Corrida Rua", index=True
    )
    duracao_segundos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    distancia_km: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pace_medio_str: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    velocidade_media_kmh: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    calorias_estimadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fc_media: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    percepcao_esforco: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    notas: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<SessaoCardio(id={self.id}, modalidade='{self.modalidade}', "
            f"duracao={self.duracao_segundos}s, dist={self.distancia_km}km)>"
        )
