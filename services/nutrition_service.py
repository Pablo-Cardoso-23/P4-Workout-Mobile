from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from core.database import get_db_session
from models.nutrition_models import (
    CheckItemDiario,
    ItemChecklistNutri,
    MetaNutricional,
    RegistroDiarioNutri,
    SuplementoEstoque,
)


def _garantir_registro_e_checks(
    session: Any, data_ref: date
) -> tuple[RegistroDiarioNutri, MetaNutricional]:
    """Garante a existência do registro diário, da meta e dos checks de itens ativos."""
    meta = session.get(MetaNutricional, 1)
    if meta is None:
        meta = MetaNutricional(
            id=1,
            meta_proteina_g=160.0,
            meta_agua_ml=3500,
            doses_creatina_alvo=4,
        )
        session.add(meta)
        session.flush()

    stmt_reg = (
        select(RegistroDiarioNutri)
        .where(RegistroDiarioNutri.data == data_ref)
        .options(
            selectinload(RegistroDiarioNutri.checks).joinedload(CheckItemDiario.item)
        )
    )
    registro = session.scalar(stmt_reg)
    if registro is None:
        registro = RegistroDiarioNutri(
            data=data_ref,
            agua_consumida_ml=0,
            creatina_doses_tomadas=0,
            proteina_extra_g=0.0,
        )
        session.add(registro)
        session.flush()

    itens_ativos = list(
        session.scalars(
            select(ItemChecklistNutri)
            .where(ItemChecklistNutri.ativo.is_(True))
            .order_by(ItemChecklistNutri.ordem, ItemChecklistNutri.id)
        ).all()
    )

    checks_existentes = list(
        session.scalars(
            select(CheckItemDiario).where(CheckItemDiario.registro_id == registro.id)
        ).all()
    )
    ids_ja_vinculados = {c.item_id for c in checks_existentes}

    novos_criados = False
    for item in itens_ativos:
        if item.id not in ids_ja_vinculados:
            session.add(
                CheckItemDiario(
                    registro_id=registro.id,
                    item_id=item.id,
                    concluido=False,
                )
            )
            novos_criados = True

    if novos_criados:
        session.flush()

    registro_atualizado = session.scalar(stmt_reg)
    return (registro_atualizado or registro), meta


def obter_ou_criar_dia(data_alvo: date | None = None) -> dict[str, Any]:
    """Busca ou inicializa o RegistroDiarioNutri da data e calcula os totais."""
    data_ref = data_alvo or date.today()
    with get_db_session() as session:
        registro, meta = _garantir_registro_e_checks(session, data_ref)

        checks_ordenados = sorted(
            [c for c in registro.checks if c.item is not None and c.item.ativo],
            key=lambda c: (c.item.ordem, c.item.id),
        )

        proteina_checks = sum(
            float(c.item.proteina_estimada_g)
            for c in checks_ordenados
            if c.concluido
        )
        proteina_total = round(
            proteina_checks + float(registro.proteina_extra_g), 1
        )

        return {
            "registro": registro,
            "checks": checks_ordenados,
            "proteina_ingerida_g": proteina_total,
            "proteina_checks_g": round(proteina_checks, 1),
            "meta": meta,
        }


def alternar_check_item(check_id: int) -> None:
    """Inverte o estado booleano concluido de um item do checklist no dia."""
    with get_db_session() as session:
        check = session.get(CheckItemDiario, check_id)
        if check is None:
            raise ValueError(f"Item de check #{check_id} não encontrado.")
        check.concluido = not check.concluido
        session.flush()


def adicionar_agua(data_alvo: date, delta_ml: int) -> int:
    """Soma ou subtrai delta_ml em agua_consumida_ml (nunca abaixo de 0)."""
    with get_db_session() as session:
        registro, _ = _garantir_registro_e_checks(session, data_alvo)
        novo_valor = max(0, int(registro.agua_consumida_ml) + int(delta_ml))
        registro.agua_consumida_ml = novo_valor
        session.flush()
        return novo_valor


def registrar_dose_creatina(data_alvo: date, delta: int = 1) -> int:
    """Incrementa ou decrementa creatina_doses_tomadas (mínimo 0)."""
    with get_db_session() as session:
        registro, _ = _garantir_registro_e_checks(session, data_alvo)
        novo_valor = max(0, int(registro.creatina_doses_tomadas) + int(delta))
        registro.creatina_doses_tomadas = novo_valor
        session.flush()
        return novo_valor


def adicionar_proteina_avulsa(data_alvo: date, gramas: float) -> float:
    """Soma gramas em proteina_extra_g (nunca abaixo de 0)."""
    with get_db_session() as session:
        registro, _ = _garantir_registro_e_checks(session, data_alvo)
        novo_valor = max(0.0, round(float(registro.proteina_extra_g) + float(gramas), 1))
        registro.proteina_extra_g = novo_valor
        session.flush()
        return novo_valor


def criar_item_checklist(
    titulo: str, categoria: str, proteina_estimada_g: float
) -> ItemChecklistNutri:
    """Cadastra um novo item recorrente e já o vincula ao registro de hoje."""
    titulo_limpo = titulo.strip()
    if not titulo_limpo:
        raise ValueError("Informe o título do suplemento ou refeição.")

    cat_limpa = categoria.strip() if categoria else "Refeição"
    if cat_limpa not in {"Suplemento", "Refeição"}:
        cat_limpa = "Refeição"

    with get_db_session() as session:
        maior_ordem = (
            session.scalar(select(func.max(ItemChecklistNutri.ordem))) or 0
        )
        novo_item = ItemChecklistNutri(
            titulo=titulo_limpo,
            categoria=cat_limpa,
            proteina_estimada_g=max(0.0, float(proteina_estimada_g)),
            ativo=True,
            ordem=int(maior_ordem) + 1,
        )
        session.add(novo_item)
        session.flush()

        _garantir_registro_e_checks(session, date.today())
        return novo_item


def atualizar_metas(
    meta_proteina_g: float, meta_agua_ml: int, doses_creatina_alvo: int
) -> None:
    """Atualiza as metas diárias de proteína, água e creatina."""
    with get_db_session() as session:
        meta = session.get(MetaNutricional, 1)
        if meta is None:
            meta = MetaNutricional(id=1)
            session.add(meta)
        meta.meta_proteina_g = max(10.0, float(meta_proteina_g))
        meta.meta_agua_ml = max(500, int(meta_agua_ml))
        meta.doses_creatina_alvo = max(1, int(doses_creatina_alvo))
        session.flush()


def listar_estoque_suplementos() -> list[dict[str, Any]]:
    """Retorna os suplementos ativos com percentual restante, dias restantes e alerta."""
    with get_db_session() as session:
        stmt = (
            select(SuplementoEstoque)
            .where(SuplementoEstoque.ativo.is_(True))
            .order_by(SuplementoEstoque.id)
        )
        suplementos = list(session.scalars(stmt).all())

        resultado: list[dict[str, Any]] = []
        for sup in suplementos:
            total = max(1.0, float(sup.quantidade_total))
            atual = max(0.0, float(sup.quantidade_atual))
            consumo = max(0.1, float(sup.consumo_diario_padrao))

            percentual = round((atual / total) * 100.0, 1)
            dias_restantes = int(atual // consumo)

            if percentual <= 5.0 or dias_restantes <= 3:
                status_alerta = "CRITICO"
            elif percentual <= float(sup.alerta_minimo_percentual) or dias_restantes <= 7:
                status_alerta = "BAIXO"
            else:
                status_alerta = "OK"

            resultado.append(
                {
                    "suplemento": sup,
                    "percentual_restante": percentual,
                    "proporcao": min(1.0, max(0.0, atual / total)),
                    "dias_restantes": dias_restantes,
                    "status_alerta": status_alerta,
                }
            )
        return resultado


def consumir_suplemento(
    suplemento_id: int, quantidade: float | None = None
) -> None:
    """Desconta uma dose ou quantidade informada do estoque atual do suplemento."""
    with get_db_session() as session:
        sup = session.get(SuplementoEstoque, suplemento_id)
        if sup is None:
            raise ValueError(f"Suplemento #{suplemento_id} não encontrado.")
        desconto = (
            float(quantidade)
            if quantidade is not None
            else float(sup.consumo_diario_padrao)
        )
        sup.quantidade_atual = max(0.0, round(float(sup.quantidade_atual) - desconto, 1))
        session.flush()


def reabastecer_suplemento(
    suplemento_id: int, nova_quantidade: float | None = None
) -> None:
    """Restaura a quantidade atual do suplemento para a quantidade total (pote cheio)."""
    with get_db_session() as session:
        sup = session.get(SuplementoEstoque, suplemento_id)
        if sup is None:
            raise ValueError(f"Suplemento #{suplemento_id} não encontrado.")
        alvo = (
            float(nova_quantidade)
            if nova_quantidade is not None
            else float(sup.quantidade_total)
        )
        sup.quantidade_atual = max(0.0, round(alvo, 1))
        if nova_quantidade is not None and nova_quantidade > sup.quantidade_total:
            sup.quantidade_total = round(float(nova_quantidade), 1)
        session.flush()


def criar_suplemento_estoque(
    nome: str,
    unidade: str,
    quantidade_total: float,
    consumo_diario_padrao: float,
) -> SuplementoEstoque:
    """Cadastra um novo pote de suplemento no controle de estoque."""
    nome_limpo = nome.strip()
    if not nome_limpo:
        raise ValueError("Informe o nome do suplemento.")
    if quantidade_total <= 0:
        raise ValueError("A quantidade total deve ser maior que zero.")

    with get_db_session() as session:
        existente = session.scalar(
            select(SuplementoEstoque).where(
                func.lower(SuplementoEstoque.nome) == nome_limpo.lower()
            )
        )
        if existente is not None:
            raise ValueError(f"O suplemento '{nome_limpo}' já existe no estoque.")

        qtd = round(float(quantidade_total), 1)
        consumo = max(0.1, round(float(consumo_diario_padrao), 1))
        novo = SuplementoEstoque(
            nome=nome_limpo,
            unidade=unidade.strip() or "doses",
            quantidade_total=qtd,
            quantidade_atual=qtd,
            consumo_diario_padrao=consumo,
            alerta_minimo_percentual=20.0,
            ativo=True,
        )
        session.add(novo)
        session.flush()
        return novo
