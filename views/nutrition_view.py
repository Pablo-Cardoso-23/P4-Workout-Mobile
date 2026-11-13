from datetime import date, timedelta
from typing import Any, Callable
import webbrowser

import flet as ft

from models.nutrition_models import (
    CheckItemDiario,
    MetaNutricional,
    RegistroDiarioNutri,
    SuplementoEstoque,
)
from services.nutrition_service import (
    adicionar_agua,
    adicionar_proteina_avulsa,
    alternar_check_item,
    atualizar_metas,
    consumir_suplemento,
    criar_item_checklist,
    criar_loja_suplemento,
    criar_suplemento_estoque,
    excluir_loja_suplemento,
    listar_estoque_suplementos,
    listar_lojas_suplementos,
    obter_ou_criar_dia,
    reabastecer_suplemento,
    registrar_dose_creatina,
)
from views.routines_view import (
    CARD_BG,
    DANGER_RED,
    DARK_BG,
    ORCELA_BLUE,
    ORCELA_BORDER_GLOW,
    ORCELA_BORDER_HIGHLIGHT,
    ORCELA_DARK_SURFACE,
    PURE_WHITE,
    SURFACE_BORDER,
    TEXT_MUTED,
    construir_borda_input,
    construir_logo_p4,
    construir_sombra_orcela,
)

AMBER_WARN = "#FFA000"


def _formatar_label_data(data_ref: date) -> str:
    hoje = date.today()
    if data_ref == hoje:
        return f"Hoje • {data_ref.strftime('%d/%m')}"
    if data_ref == hoje - timedelta(days=1):
        return f"Ontem • {data_ref.strftime('%d/%m')}"
    return data_ref.strftime("%d/%m/%Y")


def build_nutrition_view(page: ft.Page) -> ft.Control:
    """Constrói a view modular de Nutrição, Hidratação, Estoque e Lojas Favoritas."""
    data_selecionada: date = date.today()
    form_metas_visivel: bool = False
    form_lojas_visivel: bool = False
    form_novo_item_visivel: bool = False
    form_novo_suplemento_visivel: bool = False

    container_raiz = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=16,
    )

    def notificar(mensagem: str, erro: bool = False) -> None:
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(
                    mensagem,
                    color=PURE_WHITE,
                    weight=ft.FontWeight.BOLD,
                ),
                bgcolor=DANGER_RED if erro else ORCELA_BLUE,
            )
        )

    url_launcher = ft.UrlLauncher()

    def abrir_url_loja(url: str) -> None:
        """Garante prefixo https:// e abre a URL via UrlLauncher assíncrono do Flet 1.1.2 com fallback webbrowser."""
        url_limpa = (url or "").strip()
        if not url_limpa:
            notificar("URL da loja inválida.", erro=True)
            return
        if not (
            url_limpa.startswith("http://") or url_limpa.startswith("https://")
        ):
            url_limpa = f"https://{url_limpa}"

        async def _disparar_url() -> None:
            try:
                await url_launcher.launch_url(url_limpa)
            except Exception:
                try:
                    webbrowser.open(url_limpa)
                except Exception as exc:
                    notificar(f"Erro ao abrir link: {exc}", erro=True)

        try:
            if hasattr(page, "run_task"):
                page.run_task(_disparar_url)
            else:
                webbrowser.open(url_limpa)
        except Exception:
            try:
                webbrowser.open(url_limpa)
            except Exception as exc:
                notificar(f"Não foi possível abrir o site: {exc}", erro=True)

    def criar_handler_abrir_url(url_destino: str) -> Callable[[Any], None]:
        """Evita closures em loops for capturando url_destino no escopo dedicado."""
        def _handler(_: Any = None) -> None:
            abrir_url_loja(url_destino)

        return _handler

    tf_meta_prot = ft.TextField(
        label="Meta Proteína (g)",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_meta_agua = ft.TextField(
        label="Meta Água (ml)",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_meta_creatina = ft.TextField(
        label="Doses Creatina",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        width=110,
    )

    # Controles do modal de Lojas Favoritas
    tf_loja_nome = ft.TextField(
        label="Nome da Loja (ex: Oficial Farma)",
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_loja_url = ft.TextField(
        label="Link / Domínio (ex: gsuplementos.com.br)",
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )

    tf_item_titulo = ft.TextField(
        label="Nome do Suplemento ou Refeição",
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
    )
    dd_item_categoria = ft.Dropdown(
        label="Categoria",
        value="Refeição",
        border=construir_borda_input(),
        color=PURE_WHITE,
        expand=True,
        options=[
            ft.dropdown.Option(key="Refeição", text="Refeição"),
            ft.dropdown.Option(key="Suplemento", text="Suplemento"),
        ],
    )
    tf_item_proteina = ft.TextField(
        label="Proteína (g)",
        value="20",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        width=120,
    )

    tf_sup_nome = ft.TextField(
        label="Nome do Suplemento (ex: Pré-Treino Growth)",
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
    )
    dd_sup_unidade = ft.Dropdown(
        label="Unidade",
        value="doses",
        border=construir_borda_input(),
        color=PURE_WHITE,
        width=110,
        options=[
            ft.dropdown.Option(key="doses", text="doses"),
            ft.dropdown.Option(key="g", text="g"),
            ft.dropdown.Option(key="caps", text="caps"),
        ],
    )
    tf_sup_total = ft.TextField(
        label="Qtd Total Pote",
        value="60",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_sup_consumo = ft.TextField(
        label="Uso/Dia",
        value="1",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        width=90,
    )
    dd_sup_loja = ft.Dropdown(
        label="Loja Preferencial de Reposição",
        border=construir_borda_input(),
        color=PURE_WHITE,
        expand=True,
    )

    def mudar_dia(delta_dias: int) -> None:
        nonlocal data_selecionada
        nova_data = data_selecionada + timedelta(days=delta_dias)
        if nova_data <= date.today():
            data_selecionada = nova_data
            renderizar(atualizar_pagina=True)

    def alternar_form_metas(meta_atual: MetaNutricional) -> None:
        nonlocal form_metas_visivel
        form_metas_visivel = not form_metas_visivel
        if form_metas_visivel:
            tf_meta_prot.value = f"{meta_atual.meta_proteina_g:g}"
            tf_meta_agua.value = str(meta_atual.meta_agua_ml)
            tf_meta_creatina.value = str(meta_atual.doses_creatina_alvo)
        renderizar(atualizar_pagina=True)

    def alternar_form_lojas(_: Any = None) -> None:
        nonlocal form_lojas_visivel
        form_lojas_visivel = not form_lojas_visivel
        renderizar(atualizar_pagina=True)

    def salvar_nova_loja(_: Any = None) -> None:
        try:
            nova = criar_loja_suplemento(
                nome=tf_loja_nome.value or "",
                url=tf_loja_url.value or "",
            )
            tf_loja_nome.value = ""
            tf_loja_url.value = ""
            notificar(f"Loja '{nova.nome}' salva com sucesso!")
            renderizar(atualizar_pagina=True)
        except Exception as exc:
            notificar(str(exc), erro=True)

    def remover_loja(loja_id: int, nome_loja: str) -> None:
        excluir_loja_suplemento(loja_id)
        notificar(f"Loja '{nome_loja}' removida.")
        renderizar(atualizar_pagina=True)

    def salvar_metas(_: Any = None) -> None:
        nonlocal form_metas_visivel
        try:
            prot = float((tf_meta_prot.value or "160").replace(",", "."))
            agua = int(tf_meta_agua.value or "3500")
            creatina = int(tf_meta_creatina.value or "4")
            atualizar_metas(prot, agua, creatina)
            form_metas_visivel = False
            notificar("Metas nutricionais atualizadas!")
            renderizar(atualizar_pagina=True)
        except ValueError:
            notificar("Informe valores numéricos válidos para as metas.", erro=True)

    def alternar_form_novo_item(_: Any = None) -> None:
        nonlocal form_novo_item_visivel
        form_novo_item_visivel = not form_novo_item_visivel
        renderizar(atualizar_pagina=True)

    def alternar_form_novo_suplemento(_: Any = None) -> None:
        nonlocal form_novo_suplemento_visivel
        form_novo_suplemento_visivel = not form_novo_suplemento_visivel
        renderizar(atualizar_pagina=True)

    def salvar_novo_item(_: Any = None) -> None:
        nonlocal form_novo_item_visivel
        try:
            prot_val = float((tf_item_proteina.value or "0").replace(",", "."))
            novo = criar_item_checklist(
                titulo=tf_item_titulo.value or "",
                categoria=dd_item_categoria.value or "Refeição",
                proteina_estimada_g=prot_val,
            )
            tf_item_titulo.value = ""
            tf_item_proteina.value = "20"
            form_novo_item_visivel = False
            notificar(f"Item '{novo.titulo}' adicionado ao checklist!")
            renderizar(atualizar_pagina=True)
        except Exception as exc:
            notificar(str(exc), erro=True)

    def salvar_novo_suplemento(_: Any = None) -> None:
        nonlocal form_novo_suplemento_visivel
        try:
            qtd_tot = float((tf_sup_total.value or "60").replace(",", "."))
            uso_dia = float((tf_sup_consumo.value or "1").replace(",", "."))
            lid = int(dd_sup_loja.value) if dd_sup_loja.value else None
            novo = criar_suplemento_estoque(
                nome=tf_sup_nome.value or "",
                unidade=dd_sup_unidade.value or "doses",
                quantidade_total=qtd_tot,
                consumo_diario_padrao=uso_dia,
                loja_id=lid,
            )
            tf_sup_nome.value = ""
            form_novo_suplemento_visivel = False
            notificar(f"Suplemento '{novo.nome}' adicionado ao estoque!")
            renderizar(atualizar_pagina=True)
        except Exception as exc:
            notificar(str(exc), erro=True)

    def acao_check_item(check_id: int) -> None:
        alternar_check_item(check_id)
        renderizar(atualizar_pagina=True)

    def acao_agua(delta_ml: int) -> None:
        adicionar_agua(data_selecionada, delta_ml)
        renderizar(atualizar_pagina=True)

    def acao_creatina(delta: int) -> None:
        registrar_dose_creatina(data_selecionada, delta)
        renderizar(atualizar_pagina=True)

    def acao_proteina_extra(gramas: float) -> None:
        adicionar_proteina_avulsa(data_selecionada, gramas)
        renderizar(atualizar_pagina=True)

    def acao_consumir_estoque(sup_id: int) -> None:
        consumir_suplemento(sup_id, 1.0)
        renderizar(atualizar_pagina=True)

    def acao_reabastecer_estoque(sup_id: int, nome_sup: str) -> None:
        reabastecer_suplemento(sup_id)
        notificar(f"Estoque de '{nome_sup}' restaurado para 100%!")
        renderizar(atualizar_pagina=True)

    def renderizar(atualizar_pagina: bool = True) -> None:
        dados_dia = obter_ou_criar_dia(data_selecionada)
        registro: RegistroDiarioNutri = dados_dia["registro"]
        checks: list[CheckItemDiario] = dados_dia["checks"]
        proteina_ingerida: float = dados_dia["proteina_ingerida_g"]
        meta: MetaNutricional = dados_dia["meta"]
        estoque_lista = listar_estoque_suplementos()
        lojas_cadastradas = listar_lojas_suplementos()

        dd_sup_loja.options = [
            ft.dropdown.Option(key="0", text="Sem loja vinculada"),
            *[
                ft.dropdown.Option(key=str(lj.id), text=lj.nome)
                for lj in lojas_cadastradas
            ],
        ]
        if not dd_sup_loja.value:
            loja_growth = next(
                (lj for lj in lojas_cadastradas if "growth" in lj.nome.lower()),
                lojas_cadastradas[0] if lojas_cadastradas else None,
            )
            dd_sup_loja.value = str(loja_growth.id) if loja_growth else "0"

        prop_proteina = min(
            1.0,
            proteina_ingerida / max(1.0, float(meta.meta_proteina_g)),
        )
        prop_agua = min(
            1.0,
            float(registro.agua_consumida_ml) / max(1.0, float(meta.meta_agua_ml)),
        )
        prop_creatina = min(
            1.0,
            float(registro.creatina_doses_tomadas)
            / max(1.0, float(meta.doses_creatina_alvo)),
        )

        controles: list[ft.Control] = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            construir_logo_p4(),
                            ft.Text(
                                "Nutrição, Hidratação & Suplementos",
                                size=12,
                                color=TEXT_MUTED,
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=2,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.CHEVRON_LEFT_ROUNDED,
                                icon_color=PURE_WHITE,
                                tooltip="Dia anterior",
                                on_click=lambda _: mudar_dia(-1),
                            ),
                            ft.Container(
                                bgcolor=ORCELA_DARK_SURFACE,
                                padding=ft.Padding.symmetric(
                                    horizontal=10, vertical=6
                                ),
                                border_radius=8,
                                content=ft.Text(
                                    _formatar_label_data(data_selecionada),
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                    color=PURE_WHITE,
                                ),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CHEVRON_RIGHT_ROUNDED,
                                icon_color=(
                                    PURE_WHITE
                                    if data_selecionada < date.today()
                                    else TEXT_MUTED
                                ),
                                disabled=data_selecionada >= date.today(),
                                tooltip="Próximo dia",
                                on_click=lambda _: mudar_dia(1),
                            ),
                        ],
                    ),
                ],
            )
        ]

        # Modal / Painel de Lojas Favoritas
        if form_lojas_visivel:
            linhas_lojas: list[ft.Control] = []
            for lj in lojas_cadastradas:
                linhas_lojas.append(
                    ft.Container(
                        bgcolor=DARK_BG,
                        border=ft.Border.all(1, ORCELA_BORDER_GLOW),
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Column(
                                    spacing=2,
                                    expand=True,
                                    controls=[
                                        ft.Text(
                                            lj.nome,
                                            size=13,
                                            weight=ft.FontWeight.BOLD,
                                            color=PURE_WHITE,
                                        ),
                                        ft.Text(
                                            lj.url,
                                            size=11,
                                            color=ORCELA_BLUE,
                                        ),
                                    ],
                                ),
                                ft.Row(
                                    spacing=4,
                                    controls=[
                                        ft.IconButton(
                                            icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                                            icon_color=ORCELA_BLUE,
                                            tooltip=f"Abrir {lj.nome}",
                                            on_click=criar_handler_abrir_url(lj.url),
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                            icon_color=DANGER_RED,
                                            tooltip="Remover loja",
                                            on_click=lambda _, lid=lj.id, lnome=lj.nome: remover_loja(
                                                lid, lnome
                                            ),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    )
                )

            controles.append(
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, ORCELA_BORDER_HIGHLIGHT),
                    shadow=construir_sombra_orcela(),
                    border_radius=12,
                    padding=14,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Row(
                                        spacing=6,
                                        expand=True,
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.STOREFRONT_ROUNDED,
                                                color=ORCELA_BLUE,
                                                size=20,
                                            ),
                                            ft.Text(
                                                "Lojas Favoritas de Suplementos",
                                                size=15,
                                                weight=ft.FontWeight.BOLD,
                                                color=PURE_WHITE,
                                                expand=True,
                                            ),
                                        ],
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.CLOSE_ROUNDED,
                                        icon_color=TEXT_MUTED,
                                        on_click=alternar_form_lojas,
                                    ),
                                ],
                            ),
                            ft.Column(spacing=6, controls=linhas_lojas),
                            ft.Divider(height=1, color=SURFACE_BORDER),
                            ft.Text(
                                "Adicionar Nova Loja",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=ORCELA_BLUE,
                            ),
                            ft.Row(
                                spacing=8,
                                controls=[tf_loja_nome, tf_loja_url],
                            ),
                            ft.Button(
                                content="SALVAR LOJA",
                                icon=ft.Icons.ADD_LINK_ROUNDED,
                                bgcolor=ORCELA_BLUE,
                                color=PURE_WHITE,
                                width=float("inf"),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                                on_click=salvar_nova_loja,
                            ),
                        ],
                    ),
                )
            )

        if form_metas_visivel:
            controles.append(
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, ORCELA_BORDER_HIGHLIGHT),
                    shadow=construir_sombra_orcela(),
                    border_radius=12,
                    padding=14,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        "Configurar Metas Diárias",
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color=PURE_WHITE,
                                        expand=True,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.CLOSE_ROUNDED,
                                        icon_color=TEXT_MUTED,
                                        on_click=lambda _: alternar_form_metas(meta),
                                    ),
                                ],
                            ),
                            ft.Row(
                                spacing=8,
                                controls=[tf_meta_prot, tf_meta_agua, tf_meta_creatina],
                            ),
                            ft.Button(
                                content="SALVAR METAS",
                                icon=ft.Icons.CHECK_ROUNDED,
                                bgcolor=ORCELA_BLUE,
                                color=PURE_WHITE,
                                width=float("inf"),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                                on_click=salvar_metas,
                            ),
                        ],
                    ),
                )
            )

        controles.append(
            ft.Container(
                bgcolor=CARD_BG,
                border=ft.Border.all(1, ORCELA_BORDER_HIGHLIGHT),
                shadow=construir_sombra_orcela(),
                border_radius=14,
                padding=16,
                content=ft.Column(
                    spacing=14,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(
                                    "METAS & PROGRESSO DIÁRIO",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=TEXT_MUTED,
                                    expand=True,
                                ),
                                ft.Row(
                                    spacing=4,
                                    controls=[
                                        ft.IconButton(
                                            icon=ft.Icons.STOREFRONT_ROUNDED,
                                            icon_color=ORCELA_BLUE,
                                            bgcolor=ORCELA_DARK_SURFACE,
                                            icon_size=20,
                                            tooltip="Lojas Favoritas",
                                            on_click=alternar_form_lojas,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.SETTINGS_OUTLINED,
                                            icon_color=ORCELA_BLUE,
                                            icon_size=20,
                                            tooltip="Editar metas",
                                            on_click=lambda _: alternar_form_metas(
                                                meta
                                            ),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        ft.Column(
                            spacing=6,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Row(
                                            spacing=6,
                                            controls=[
                                                ft.Icon(
                                                    ft.Icons.BOLT_ROUNDED,
                                                    color=ORCELA_BLUE,
                                                    size=18,
                                                ),
                                                ft.Text(
                                                    "Proteína",
                                                    size=14,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=PURE_WHITE,
                                                ),
                                            ],
                                        ),
                                        ft.Row(
                                            spacing=8,
                                            controls=[
                                                ft.Text(
                                                    f"{proteina_ingerida:.0f} / {meta.meta_proteina_g:.0f} g",
                                                    size=13,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=ORCELA_BLUE,
                                                ),
                                                ft.OutlinedButton(
                                                    content="+25g",
                                                    on_click=lambda _: acao_proteina_extra(
                                                        25.0
                                                    ),
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                ft.ProgressBar(
                                    value=prop_proteina,
                                    color=ORCELA_BLUE,
                                    bgcolor=SURFACE_BORDER,
                                    bar_height=10,
                                    border_radius=ft.BorderRadius.all(10),
                                ),
                            ],
                        ),
                        ft.Divider(height=1, color=SURFACE_BORDER),
                        ft.Column(
                            spacing=6,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Row(
                                            spacing=6,
                                            controls=[
                                                ft.Icon(
                                                    ft.Icons.WATER_DROP_ROUNDED,
                                                    color=ORCELA_BLUE,
                                                    size=18,
                                                ),
                                                ft.Text(
                                                    "Hidratação",
                                                    size=14,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=PURE_WHITE,
                                                ),
                                            ],
                                        ),
                                        ft.Text(
                                            f"{registro.agua_consumida_ml} / {meta.meta_agua_ml} ml",
                                            size=13,
                                            weight=ft.FontWeight.BOLD,
                                            color=ORCELA_BLUE,
                                        ),
                                    ],
                                ),
                                ft.ProgressBar(
                                    value=prop_agua,
                                    color=ORCELA_BLUE,
                                    bgcolor=SURFACE_BORDER,
                                    bar_height=10,
                                    border_radius=ft.BorderRadius.all(10),
                                ),
                                ft.Row(
                                    spacing=8,
                                    alignment=ft.MainAxisAlignment.END,
                                    controls=[
                                        ft.OutlinedButton(
                                            content="+250ml",
                                            on_click=lambda _: acao_agua(250),
                                        ),
                                        ft.Button(
                                            content="+500ml",
                                            bgcolor=ORCELA_BLUE,
                                            color=PURE_WHITE,
                                            style=ft.ButtonStyle(
                                                shape=ft.RoundedRectangleBorder(
                                                    radius=8
                                                ),
                                            ),
                                            on_click=lambda _: acao_agua(500),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        ft.Divider(height=1, color=SURFACE_BORDER),
                        ft.Column(
                            spacing=6,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Row(
                                            spacing=6,
                                            controls=[
                                                ft.Icon(
                                                    ft.Icons.SCIENCE_ROUNDED,
                                                    color=ORCELA_BLUE,
                                                    size=18,
                                                ),
                                                ft.Text(
                                                    "Creatina",
                                                    size=14,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=PURE_WHITE,
                                                ),
                                            ],
                                        ),
                                        ft.Row(
                                            spacing=8,
                                            controls=[
                                                ft.Text(
                                                    f"{registro.creatina_doses_tomadas}/{meta.doses_creatina_alvo} doses",
                                                    size=13,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=ORCELA_BLUE,
                                                ),
                                                ft.Button(
                                                    content="+1 Dose",
                                                    bgcolor=ORCELA_BLUE,
                                                    color=PURE_WHITE,
                                                    style=ft.ButtonStyle(
                                                        shape=ft.RoundedRectangleBorder(
                                                            radius=8
                                                        ),
                                                    ),
                                                    on_click=lambda _: acao_creatina(1),
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                ft.ProgressBar(
                                    value=prop_creatina,
                                    color=ORCELA_BLUE,
                                    bgcolor=SURFACE_BORDER,
                                    bar_height=10,
                                    border_radius=ft.BorderRadius.all(10),
                                ),
                            ],
                        ),
                    ],
                ),
            )
        )

        # Seção Estoque Inteligente de Suplementos
        controles.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Text(
                        "ESTOQUE DE SUPLEMENTOS",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_MUTED,
                        expand=True,
                    ),
                    ft.OutlinedButton(
                        content="Novo Suplemento",
                        icon=ft.Icons.ADD_ROUNDED,
                        style=ft.ButtonStyle(
                            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                        ),
                        on_click=alternar_form_novo_suplemento,
                    ),
                ],
            )
        )

        if form_novo_suplemento_visivel:
            controles.append(
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, ORCELA_BORDER_HIGHLIGHT),
                    shadow=construir_sombra_orcela(),
                    border_radius=12,
                    padding=14,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        "Cadastrar Pote no Estoque",
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color=PURE_WHITE,
                                        expand=True,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.CLOSE_ROUNDED,
                                        icon_color=TEXT_MUTED,
                                        on_click=alternar_form_novo_suplemento,
                                    ),
                                ],
                            ),
                            tf_sup_nome,
                            ft.Row(
                                spacing=8,
                                controls=[
                                    tf_sup_total,
                                    dd_sup_unidade,
                                    tf_sup_consumo,
                                ],
                            ),
                            ft.Row(controls=[dd_sup_loja]),
                            ft.Button(
                                content="SALVAR NO ESTOQUE",
                                icon=ft.Icons.CHECK_ROUNDED,
                                bgcolor=ORCELA_BLUE,
                                color=PURE_WHITE,
                                width=float("inf"),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                                on_click=salvar_novo_suplemento,
                            ),
                        ],
                    ),
                )
            )

        for info_sup in estoque_lista:
            sup: SuplementoEstoque = info_sup["suplemento"]
            perc: float = info_sup["percentual_restante"]
            prop_sup: float = info_sup["proporcao"]
            dias_rest: int = info_sup["dias_restantes"]
            status: str = info_sup["status_alerta"]
            loja_nome: str | None = info_sup["loja_nome"]
            loja_url: str | None = info_sup["loja_url"]

            if status == "CRITICO":
                cor_barra = DANGER_RED
                texto_badge = "REPOR URGENTE"
                bg_badge = "#3D0A0A"
            elif status == "BAIXO":
                cor_barra = AMBER_WARN
                texto_badge = "ACABANDO"
                bg_badge = "#3D2600"
            else:
                cor_barra = ORCELA_BLUE
                texto_badge = f"~{dias_rest} dias"
                bg_badge = ORCELA_DARK_SURFACE

            subtitulo_loja = f" • Loja: {loja_nome}" if loja_nome else ""

            controles_card_sup: list[ft.Control] = [
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            expand=True,
                            controls=[
                                ft.Text(
                                    sup.nome,
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=PURE_WHITE,
                                ),
                                ft.Text(
                                    f"Restam {sup.quantidade_atual:g} / {sup.quantidade_total:g} {sup.unidade} ({perc:.0f}%) • ~{dias_rest} dias{subtitulo_loja}",
                                    size=11,
                                    color=TEXT_MUTED,
                                ),
                            ],
                        ),
                        ft.Container(
                            bgcolor=bg_badge,
                            padding=ft.Padding.symmetric(
                                horizontal=8, vertical=4
                            ),
                            border_radius=6,
                            content=ft.Text(
                                texto_badge,
                                size=10,
                                weight=ft.FontWeight.BOLD,
                                color=cor_barra
                                if status != "OK"
                                else PURE_WHITE,
                            ),
                        ),
                    ],
                ),
                ft.ProgressBar(
                    value=prop_sup,
                    color=cor_barra,
                    bgcolor=SURFACE_BORDER,
                    bar_height=10,
                    border_radius=ft.BorderRadius.all(10),
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            f"Uso diário: {sup.consumo_diario_padrao:g} {sup.unidade}/dia",
                            size=11,
                            color=TEXT_MUTED,
                        ),
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.OutlinedButton(
                                    content="-1 Dose",
                                    on_click=lambda _, sid=sup.id: acao_consumir_estoque(
                                        sid
                                    ),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.REFRESH_ROUNDED,
                                    icon_color=ORCELA_BLUE,
                                    bgcolor=ORCELA_DARK_SURFACE,
                                    tooltip="Reabastecer pote (100%)",
                                    on_click=lambda _, sid=sup.id, snome=sup.nome: acao_reabastecer_estoque(
                                        sid, snome
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            ]

            if status in {"BAIXO", "CRITICO"} and loja_nome and loja_url:
                controles_card_sup.append(
                    ft.Button(
                        content=f"Comprar na {loja_nome}",
                        icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                        bgcolor=ORCELA_BLUE,
                        color=PURE_WHITE,
                        width=float("inf"),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        on_click=criar_handler_abrir_url(loja_url),
                    )
                )

            controles.append(
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(
                        1, cor_barra if status != "OK" else ORCELA_BORDER_GLOW
                    ),
                    shadow=construir_sombra_orcela(),
                    border_radius=12,
                    padding=14,
                    content=ft.Column(spacing=8, controls=controles_card_sup),
                )
            )

        # Cabeçalho Checklist Diário
        controles.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Text(
                        "CHECKLIST DIÁRIO",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_MUTED,
                        expand=True,
                    ),
                    ft.OutlinedButton(
                        content="Novo Item",
                        icon=ft.Icons.ADD_ROUNDED,
                        style=ft.ButtonStyle(
                            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                        ),
                        on_click=alternar_form_novo_item,
                    ),
                ],
            )
        )

        if form_novo_item_visivel:
            controles.append(
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, ORCELA_BORDER_HIGHLIGHT),
                    shadow=construir_sombra_orcela(),
                    border_radius=12,
                    padding=14,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        "Novo Item Recorrente",
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color=PURE_WHITE,
                                        expand=True,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.CLOSE_ROUNDED,
                                        icon_color=TEXT_MUTED,
                                        on_click=alternar_form_novo_item,
                                    ),
                                ],
                            ),
                            tf_item_titulo,
                            ft.Row(
                                spacing=8,
                                controls=[dd_item_categoria, tf_item_proteina],
                            ),
                            ft.Button(
                                content="ADICIONAR AO CHECKLIST",
                                icon=ft.Icons.CHECK_ROUNDED,
                                bgcolor=ORCELA_BLUE,
                                color=PURE_WHITE,
                                width=float("inf"),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                                on_click=salvar_novo_item,
                            ),
                        ],
                    ),
                )
            )

        for chk in checks:
            item = chk.item
            marcado = bool(chk.concluido)
            badge_prot = (
                f"+{item.proteina_estimada_g:.0f}g prot"
                if item.proteina_estimada_g > 0
                else item.categoria
            )

            controles.append(
                ft.Container(
                    bgcolor=ORCELA_DARK_SURFACE if marcado else CARD_BG,
                    border=ft.Border.all(
                        1, ORCELA_BLUE if marcado else ORCELA_BORDER_GLOW
                    ),
                    shadow=construir_sombra_orcela(),
                    border_radius=12,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=8,
                                expand=True,
                                controls=[
                                    ft.Checkbox(
                                        value=marcado,
                                        active_color=ORCELA_BLUE,
                                        check_color=PURE_WHITE,
                                        on_change=lambda _, cid=chk.id: acao_check_item(
                                            cid
                                        ),
                                    ),
                                    ft.Column(
                                        spacing=2,
                                        expand=True,
                                        controls=[
                                            ft.Text(
                                                item.titulo,
                                                size=14,
                                                weight=ft.FontWeight.BOLD,
                                                color=PURE_WHITE,
                                            ),
                                            ft.Text(
                                                item.categoria,
                                                size=11,
                                                color=TEXT_MUTED,
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            ft.Container(
                                bgcolor=DARK_BG,
                                padding=ft.Padding.symmetric(
                                    horizontal=8, vertical=4
                                ),
                                border_radius=6,
                                content=ft.Text(
                                    badge_prot,
                                    size=11,
                                    weight=ft.FontWeight.BOLD,
                                    color=ORCELA_BLUE,
                                ),
                            ),
                        ],
                    ),
                )
            )

        container_raiz.controls = controles
        if atualizar_pagina:
            page.update()

    renderizar(atualizar_pagina=False)
    return container_raiz
