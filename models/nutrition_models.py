from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class MetaNutricional(Base):
    __tablename__ = "metas_nutricionais"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    meta_proteina_g: Mapped[float] = mapped_column(Float, nullable=False, default=160.0)
    meta_agua_ml: Mapped[int] = mapped_column(Integer, nullable=False, default=3500)
    doses_creatina_alvo: Mapped[int] = mapped_column(Integer, nullable=False, default=4)

    def __repr__(self) -> str:
        return (
            f"<MetaNutricional(proteina={self.meta_proteina_g}g, "
            f"agua={self.meta_agua_ml}ml, creatina={self.doses_creatina_alvo} doses)>"
        )


class ItemChecklistNutri(Base):
    __tablename__ = "itens_checklist_nutri"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(160), nullable=False)
    categoria: Mapped[str] = mapped_column(String(40), nullable=False, default="Refeição")
    proteina_estimada_g: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    checks_diarios: Mapped[list["CheckItemDiario"]] = relationship(
        "CheckItemDiario",
        back_populates="item",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<ItemChecklistNutri(id={self.id}, titulo='{self.titulo}', "
            f"categoria='{self.categoria}', proteina={self.proteina_estimada_g}g)>"
        )


class RegistroDiarioNutri(Base):
    __tablename__ = "registros_diarios_nutri"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data: Mapped[date] = mapped_column(
        Date, unique=True, index=True, nullable=False, default=date.today
    )
    agua_consumida_ml: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    creatina_doses_tomadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    proteina_extra_g: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    notas: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    checks: Mapped[list["CheckItemDiario"]] = relationship(
        "CheckItemDiario",
        back_populates="registro",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<RegistroDiarioNutri(id={self.id}, data='{self.data}', "
            f"agua={self.agua_consumida_ml}ml, creatina={self.creatina_doses_tomadas})>"
        )


class CheckItemDiario(Base):
    __tablename__ = "checks_itens_diarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    registro_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("registros_diarios_nutri.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("itens_checklist_nutri.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    concluido: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    registro: Mapped["RegistroDiarioNutri"] = relationship(
        "RegistroDiarioNutri", back_populates="checks"
    )
    item: Mapped["ItemChecklistNutri"] = relationship(
        "ItemChecklistNutri", back_populates="checks_diarios", lazy="joined"
    )

    def __repr__(self) -> str:
        return (
            f"<CheckItemDiario(id={self.id}, registro_id={self.registro_id}, "
            f"item_id={self.item_id}, concluido={self.concluido})>"
        )


class RegistroBiometria(Base):
    __tablename__ = "registros_biometria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    data: Mapped[date] = mapped_column(
        Date, index=True, nullable=False, default=date.today
    )
    peso_kg: Mapped[float] = mapped_column(Float, nullable=False)
    altura_cm: Mapped[float] = mapped_column(Float, nullable=False, default=190.0)
    percentual_gordura: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cintura_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    braco_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notas: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<RegistroBiometria(id={self.id}, data='{self.data}', "
            f"peso={self.peso_kg}kg, altura={self.altura_cm}cm)>"
        )


class LojaSuplemento(Base):
    __tablename__ = "lojas_suplementos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    ativa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<LojaSuplemento(id={self.id}, nome='{self.nome}', url='{self.url}')>"


class SuplementoEstoque(Base):
    __tablename__ = "suplementos_estoque"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    unidade: Mapped[str] = mapped_column(String(20), nullable=False, default="doses")
    quantidade_total: Mapped[float] = mapped_column(Float, nullable=False, default=80.0)
    quantidade_atual: Mapped[float] = mapped_column(Float, nullable=False, default=80.0)
    consumo_diario_padrao: Mapped[float] = mapped_column(
        Float, nullable=False, default=1.0
    )
    alerta_minimo_percentual: Mapped[float] = mapped_column(
        Float, nullable=False, default=20.0
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    loja_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("lojas_suplementos.id", ondelete="SET NULL"),
        nullable=True,
    )

    loja: Mapped[Optional["LojaSuplemento"]] = relationship(
        "LojaSuplemento", lazy="joined"
    )

    def __repr__(self) -> str:
        return (
            f"<SuplementoEstoque(id={self.id}, nome='{self.nome}', "
            f"atual={self.quantidade_atual}/{self.quantidade_total} {self.unidade})>"
        )
