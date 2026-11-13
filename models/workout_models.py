from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Exercicio(Base):
    __tablename__ = "exercicios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    grupo_muscular: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    equipamento: Mapped[str] = mapped_column(String(50), nullable=False)

    ficha_itens: Mapped[list["FichaExercicio"]] = relationship(
        "FichaExercicio",
        back_populates="exercicio",
        cascade="all, delete-orphan",
    )
    series_executadas: Mapped[list["SerieExecutada"]] = relationship(
        "SerieExecutada",
        back_populates="exercicio",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Exercicio(id={self.id}, nome='{self.nome}', grupo='{self.grupo_muscular}')>"


class Ficha(Base):
    __tablename__ = "fichas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    itens: Mapped[list["FichaExercicio"]] = relationship(
        "FichaExercicio",
        back_populates="ficha",
        cascade="all, delete-orphan",
        order_by="FichaExercicio.ordem",
        lazy="selectin",
    )
    sessoes: Mapped[list["SessaoTreino"]] = relationship(
        "SessaoTreino",
        back_populates="ficha",
    )

    def __repr__(self) -> str:
        return f"<Ficha(id={self.id}, nome='{self.nome}', ativa={self.ativa})>"


class FichaExercicio(Base):
    __tablename__ = "ficha_exercicios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ficha_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("fichas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercicio_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("exercicios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    series_alvo: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    reps_alvo: Mapped[str] = mapped_column(String(20), nullable=False, default="8-12")
    descanso_segundos: Mapped[int] = mapped_column(Integer, nullable=False, default=90)

    ficha: Mapped["Ficha"] = relationship("Ficha", back_populates="itens")
    exercicio: Mapped["Exercicio"] = relationship("Exercicio", back_populates="ficha_itens", lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<FichaExercicio(ficha_id={self.ficha_id}, exercicio_id={self.exercicio_id}, "
            f"ordem={self.ordem}, series={self.series_alvo}x{self.reps_alvo})>"
        )


class SessaoTreino(Base):
    __tablename__ = "sessoes_treino"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ficha_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("fichas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    data_inicio: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
        index=True,
    )
    data_fim: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    peso_corporal_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notas: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duracao_segundos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fc_media: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    calorias_estimadas: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    percepcao_esforco: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    ficha: Mapped[Optional["Ficha"]] = relationship("Ficha", back_populates="sessoes")
    series: Mapped[list["SerieExecutada"]] = relationship(
        "SerieExecutada",
        back_populates="sessao",
        cascade="all, delete-orphan",
        order_by="SerieExecutada.id",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<SessaoTreino(id={self.id}, ficha_id={self.ficha_id}, inicio='{self.data_inicio}')>"


class SerieExecutada(Base):
    __tablename__ = "series_executadas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sessao_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sessoes_treino.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercicio_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("exercicios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    numero_serie: Mapped[int] = mapped_column(Integer, nullable=False)
    carga_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    repeticoes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rir: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tipo_serie: Mapped[str] = mapped_column(String(5), nullable=False, default="W")

    sessao: Mapped["SessaoTreino"] = relationship("SessaoTreino", back_populates="series")
    exercicio: Mapped["Exercicio"] = relationship("Exercicio", back_populates="series_executadas", lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<SerieExecutada(sessao={self.sessao_id}, exercicio={self.exercicio_id}, "
            f"serie=#{self.numero_serie}, {self.carga_kg}kg x {self.repeticoes} [{self.tipo_serie}])>"
        )
