from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from core.database import get_db_session
from models.nutrition_models import (
    CheckItemDiario,
    ItemChecklistNutri,
    LojaSuplemento,
    MetaNutricional,
    RegistroDiarioNutri,
    SuplementoEstoque,
)

TIPOS_MACRO_VALIDOS = ["Proteína", "Carboidrato", "Gordura", "Calorias"]


def _normalizar_url(url_bruta: str) -> str:
    limpa = url_bruta.strip()
    if not limpa:
        raise ValueError("Informe o link (URL) da loja.")
    if not (limpa.startswith("http://") or limpa.startswith("https://")):
        return f"https://{limpa}"
    return limpa


def listar_lojas_suplementos() -> list[LojaSuplemento]:
    """Lista todas as lojas de suplementos ativas ordenadas por nome."""
    with get_db_session() as session:
        stmt = (
            select(LojaSuplemento)
            .where(LojaSuplemento.ativa.is_(True))
            .order_by(LojaSuplemento.nome)
        )
        return list(session.scalars(stmt).all())


def criar_loja_suplemento(nome: str, url: str) -> LojaSuplemento:
    """Cria uma nova loja favorita normalizando a URL com https://."""
    nome_limpo = nome.strip()
    if not nome_limpo:
        raise ValueError("Informe o nome da loja.")
    url_normalizada = _normalizar_url(url)

    with get_db_session() as session:
        existente = session.scalar(
            select(LojaSuplemento).where(
                func.lower(LojaSuplemento.nome) == nome_limpo.lower()
            )
        )
        if existente is not None:
            existente.url = url_normalizada
            existente.ativa = True
            session.flush()
            return existente

        nova = LojaSuplemento(
            nome=nome_limpo,
            url=url_normalizada,
            ativa=True,
        )
        session.add(nova)
        session.flush()
        return nova


def excluir_loja_suplemento(loja_id: int) -> None:
    """Remove uma loja do catálogo de lojas favoritas."""
    with get_db_session() as session:
        loja = session.get(LojaSuplemento, loja_id)
        if loja is not None:
            session.delete(loja)


def vincular_loja_suplemento(suplemento_id: int, loja_id: int | None) -> None:
    """Atualiza a loja preferencial vinculada a um suplemento do estoque."""
    with get_db_session() as session:
        sup = session.get(SuplementoEstoque, suplemento_id)
        if sup is None:
            raise ValueError(f"Suplemento #{suplemento_id} não encontrado.")
        sup.loja_id = (
            int(loja_id) if (loja_id is not None and loja_id > 0) else None
        )
        session.flush()


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
            selectinload(RegistroDiarioNutri.checks).joinedload(
                CheckItemDiario.item
            )
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
            select(CheckItemDiario).where(
                CheckItemDiario.registro_id == registro.id
            )
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


def _proteina_efetiva_item(item: ItemChecklistNutri) -> float:
    """Retorna a proteína contabilizável na meta proteica (apenas itens do tipo Proteína)."""
    if getattr(item, "tipo_macro", "Proteína") != "Proteína":
        return 0.0
    prot_g = float(getattr(item, "proteina_g", 0.0) or 0.0)
    if prot_g > 0.0:
        return prot_g
    return float(item.proteina_estimada_g or 0.0)


def formatar_rotulo_macro_item(item: ItemChecklistNutri) -> str:
    """Formata o rótulo de porção e macro (ex: '200g • 50g Carboidrato' ou '30g • 24g Proteína')."""
    porcao = float(getattr(item, "quantidade_gramas", 100.0) or 100.0)
    tipo = str(getattr(item, "tipo_macro", "Proteína") or "Proteína")

    if tipo == "Proteína":
        val = float(getattr(item, "proteina_g", 0.0) or item.proteina_estimada_g or 0.0)
        if val > 0:
            return f"{porcao:g}g • {val:g}g Proteína"
        return f"{porcao:g}g • {item.categoria}"
    if tipo == "Carboidrato":
        val = float(getattr(item, "carboidrato_g", 0.0) or item.proteina_estimada_g or 0.0)
        if val > 0:
            return f"{porcao:g}g • {val:g}g Carboidrato"
        return f"{porcao:g}g • Carboidrato"
    if tipo == "Gordura":
        val = float(getattr(item, "carboidrato_g", 0.0) or item.proteina_estimada_g or 0.0)
        if val > 0:
            return f"{porcao:g}g • {val:g}g Gordura"
        return f"{porcao:g}g • Gordura"
    # Calorias / Bebida
    val = float(getattr(item, "carboidrato_g", 0.0) or item.proteina_estimada_g or 0.0)
    if val > 0:
        return f"{porcao:g}g • {val:g} kcal"
    return f"{porcao:g}g • {item.categoria}"


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
            _proteina_efetiva_item(c.item)
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
        novo_valor = max(
            0.0, round(float(registro.proteina_extra_g) + float(gramas), 1)
        )
        registro.proteina_extra_g = novo_valor
        session.flush()
        return novo_valor


def criar_item_checklist(
    titulo: str,
    categoria: str,
    proteina_estimada_g: float = 0.0,
    quantidade_gramas: float = 100.0,
    tipo_macro: str = "Proteína",
    valor_macro_g: float | None = None,
) -> ItemChecklistNutri:
    """Cadastra um novo item recorrente com porção em gramas e macronutriente principal."""
    titulo_limpo = titulo.strip()
    if not titulo_limpo:
        raise ValueError("Informe o título do suplemento ou refeição.")

    cat_limpa = categoria.strip() if categoria else "Refeição"
    if cat_limpa not in {"Suplemento", "Refeição"}:
        cat_limpa = "Refeição"

    macro_limpo = (
        tipo_macro.strip()
        if (tipo_macro and tipo_macro.strip() in TIPOS_MACRO_VALIDOS)
        else "Proteína"
    )
    valor_macro = (
        max(0.0, float(valor_macro_g))
        if valor_macro_g is not None
        else max(0.0, float(proteina_estimada_g))
    )
    porcao_g = max(1.0, float(quantidade_gramas))

    prot_g = valor_macro if macro_limpo == "Proteína" else 0.0
    carb_g = valor_macro if macro_limpo != "Proteína" else 0.0

    with get_db_session() as session:
        maior_ordem = (
            session.scalar(select(func.max(ItemChecklistNutri.ordem))) or 0
        )
        novo_item = ItemChecklistNutri(
            titulo=titulo_limpo,
            categoria=cat_limpa,
            quantidade_gramas=porcao_g,
            tipo_macro=macro_limpo,
            proteina_estimada_g=prot_g,
            proteina_g=prot_g,
            carboidrato_g=carb_g,
            ativo=True,
            ordem=int(maior_ordem) + 1,
        )
        session.add(novo_item)
        session.flush()

        _garantir_registro_e_checks(session, date.today())
        return novo_item


def atualizar_item_checklist(
    item_id: int,
    titulo: str,
    categoria: str,
    quantidade_gramas: float,
    tipo_macro: str,
    valor_macro_g: float,
) -> None:
    """Edita porção, categoria e macronutriente principal de um item do checklist."""
    titulo_limpo = titulo.strip()
    if not titulo_limpo:
        raise ValueError("O título do item não pode ficar vazio.")
    macro_limpo = (
        tipo_macro.strip()
        if (tipo_macro and tipo_macro.strip() in TIPOS_MACRO_VALIDOS)
        else "Proteína"
    )
    val = max(0.0, float(valor_macro_g))
    porcao = max(1.0, float(quantidade_gramas))

    with get_db_session() as session:
        item = session.get(ItemChecklistNutri, item_id)
        if item is None:
            raise ValueError(f"Item #{item_id} não encontrado.")
        item.titulo = titulo_limpo
        item.categoria = (
            categoria.strip()
            if categoria in {"Refeição", "Suplemento"}
            else "Refeição"
        )
        item.quantidade_gramas = porcao
        item.tipo_macro = macro_limpo
        if macro_limpo == "Proteína":
            item.proteina_g = val
            item.proteina_estimada_g = val
            item.carboidrato_g = 0.0
        else:
            item.proteina_g = 0.0
            item.proteina_estimada_g = 0.0
            item.carboidrato_g = val
        session.flush()


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
    """Retorna os suplementos ativos com gramatura, doses, percentual, dias restantes e loja."""
    with get_db_session() as session:
        stmt = (
            select(SuplementoEstoque)
            .where(SuplementoEstoque.ativo.is_(True))
            .order_by(SuplementoEstoque.id)
        )
        suplementos = list(session.scalars(stmt).all())

        resultado: list[dict[str, Any]] = []
        for sup in suplementos:
            dose_g = max(0.5, float(getattr(sup, "dose_padrao_g", 5.0) or 5.0))
            peso_tot = max(
                dose_g,
                float(getattr(sup, "peso_total_g", 300.0) or 300.0),
            )
            peso_rest = max(
                0.0,
                float(getattr(sup, "peso_restante_g", peso_tot) or 0.0),
            )

            doses_totais = int(round(peso_tot / dose_g))
            doses_restantes = int(round(peso_rest / dose_g))
            consumo_doses_dia = max(0.1, float(sup.consumo_diario_padrao))

            percentual = round((peso_rest / peso_tot) * 100.0, 1)
            dias_restantes = int(doses_restantes // consumo_doses_dia)

            if percentual <= 5.0 or dias_restantes <= 3:
                status_alerta = "CRITICO"
            elif (
                percentual <= float(sup.alerta_minimo_percentual)
                or dias_restantes <= 7
            ):
                status_alerta = "BAIXO"
            else:
                status_alerta = "OK"

            loja_obj = sup.loja
            resultado.append(
                {
                    "suplemento": sup,
                    "peso_total_g": round(peso_tot, 1),
                    "peso_restante_g": round(peso_rest, 1),
                    "dose_padrao_g": round(dose_g, 1),
                    "doses_totais": doses_totais,
                    "doses_restantes": doses_restantes,
                    "percentual_restante": percentual,
                    "proporcao": min(1.0, max(0.0, peso_rest / peso_tot)),
                    "dias_restantes": dias_restantes,
                    "status_alerta": status_alerta,
                    "loja_id": sup.loja_id,
                    "loja_nome": loja_obj.nome if loja_obj is not None else None,
                    "loja_url": loja_obj.url if loja_obj is not None else None,
                }
            )
        return resultado


def consumir_suplemento(
    suplemento_id: int, quantidade: float | None = None
) -> None:
    """Desconta 1 dose (dose_padrao_g) de peso_restante_g e recalcula quantidade_atual."""
    with get_db_session() as session:
        sup = session.get(SuplementoEstoque, suplemento_id)
        if sup is None:
            raise ValueError(f"Suplemento #{suplemento_id} não encontrado.")

        dose_g = max(0.5, float(getattr(sup, "dose_padrao_g", 5.0) or 5.0))
        doses_a_descontar = (
            float(quantidade)
            if quantidade is not None
            else float(sup.consumo_diario_padrao)
        )
        gramas_desconto = doses_a_descontar * dose_g

        novo_peso_rest = max(
            0.0, round(float(sup.peso_restante_g) - gramas_desconto, 1)
        )
        sup.peso_restante_g = novo_peso_rest
        sup.quantidade_atual = max(0.0, round(novo_peso_rest / dose_g, 1))
        session.flush()


def reabastecer_suplemento(
    suplemento_id: int, nova_quantidade: float | None = None
) -> None:
    """Restaura peso_restante_g para peso_total_g (pote cheio) e recalcula doses."""
    with get_db_session() as session:
        sup = session.get(SuplementoEstoque, suplemento_id)
        if sup is None:
            raise ValueError(f"Suplemento #{suplemento_id} não encontrado.")
        dose_g = max(0.5, float(getattr(sup, "dose_padrao_g", 5.0) or 5.0))
        if nova_quantidade is not None and nova_quantidade > 0:
            sup.peso_total_g = round(float(nova_quantidade), 1)
        sup.peso_restante_g = float(sup.peso_total_g)
        sup.quantidade_total = round(float(sup.peso_total_g) / dose_g, 1)
        sup.quantidade_atual = sup.quantidade_total
        session.flush()


def criar_suplemento_estoque(
    nome: str,
    unidade: str = "doses",
    quantidade_total: float | None = None,
    consumo_diario_padrao: float = 1.0,
    loja_id: int | None = None,
    peso_total_g: float | None = None,
    dose_padrao_g: float = 5.0,
) -> SuplementoEstoque:
    """Cadastra um novo pote de suplemento baseado em Peso Total (g) e Dose Padrão (g)."""
    nome_limpo = nome.strip()
    if not nome_limpo:
        raise ValueError("Informe o nome do suplemento.")

    dose_g = max(0.5, round(float(dose_padrao_g), 1))
    if peso_total_g is not None and peso_total_g > 0:
        peso_tot = round(float(peso_total_g), 1)
    elif quantidade_total is not None and quantidade_total > 0:
        peso_tot = round(float(quantidade_total) * dose_g, 1)
    else:
        raise ValueError("O peso total do pote (g) deve ser maior que zero.")

    doses_calculadas = max(1.0, round(peso_tot / dose_g, 1))

    with get_db_session() as session:
        existente = session.scalar(
            select(SuplementoEstoque).where(
                func.lower(SuplementoEstoque.nome) == nome_limpo.lower()
            )
        )
        if existente is not None:
            raise ValueError(f"O suplemento '{nome_limpo}' já existe no estoque.")

        consumo = max(0.1, round(float(consumo_diario_padrao), 1))
        novo = SuplementoEstoque(
            nome=nome_limpo,
            unidade=unidade.strip() or "doses",
            peso_total_g=peso_tot,
            peso_restante_g=peso_tot,
            dose_padrao_g=dose_g,
            quantidade_total=doses_calculadas,
            quantidade_atual=doses_calculadas,
            consumo_diario_padrao=consumo,
            alerta_minimo_percentual=20.0,
            ativo=True,
            loja_id=(
                int(loja_id) if (loja_id is not None and loja_id > 0) else None
            ),
        )
        session.add(novo)
        session.flush()
        return novo


def atualizar_suplemento_estoque(
    suplemento_id: int,
    nome: str,
    peso_total_g: float,
    peso_restante_g: float,
    dose_padrao_g: float,
    consumo_diario_padrao: float,
    loja_id: int | None = None,
) -> None:
    """Atualiza gramatura total/restante, dose em gramas e loja de um suplemento."""
    nome_limpo = nome.strip()
    if not nome_limpo:
        raise ValueError("O nome do suplemento é obrigatório.")
    if peso_total_g <= 0 or dose_padrao_g <= 0:
        raise ValueError("Peso total e dose (g) devem ser maiores que zero.")

    with get_db_session() as session:
        sup = session.get(SuplementoEstoque, suplemento_id)
        if sup is None:
            raise ValueError(f"Suplemento #{suplemento_id} não encontrado.")

        dose_g = round(float(dose_padrao_g), 1)
        p_tot = round(float(peso_total_g), 1)
        p_rest = min(p_tot, max(0.0, round(float(peso_restante_g), 1)))

        sup.nome = nome_limpo
        sup.peso_total_g = p_tot
        sup.peso_restante_g = p_rest
        sup.dose_padrao_g = dose_g
        sup.quantidade_total = max(1.0, round(p_tot / dose_g, 1))
        sup.quantidade_atual = max(0.0, round(p_rest / dose_g, 1))
        sup.consumo_diario_padrao = max(0.1, round(float(consumo_diario_padrao), 1))
        sup.loja_id = (
            int(loja_id) if (loja_id is not None and loja_id > 0) else None
        )
        session.flush()
