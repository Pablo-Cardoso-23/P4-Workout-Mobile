from typing import Any

import flet as ft

from services.workout_service import (
    atualizar_ficha_exercicio,
    criar_exercicio,
    criar_ficha,
    excluir_ficha,
    listar_exercicios,
    listar_fichas,
    mover_exercicio_ficha,
    renomear_ficha,
)

ORCELA_BLUE = "#007BFF"
ORCELA_DARK_SURFACE = "#002B5C"
ORCELA_BORDER_GLOW = "#33007BFF"
ORCELA_BORDER_HIGHLIGHT = "#4D007BFF"
ORCELA_SHADOW_COLOR = "#1A007BFF"
PURE_WHITE = "#FFFFFF"
DARK_BG = "#0F0F0F"
CARD_BG = "#1A1A1A"
SURFACE_BORDER = "#2A2A2A"
TEXT_MUTED = "#9E9E9E"
DANGER_RED = "#FF5252"

GRUPOS_MUSCULARES = [
    "Peito",
    "Costas",
    "Pernas",
    "Ombros",
    "Bíceps",
    "Tríceps",
    "Core",
]
EQUIPAMENTOS = ["Barra", "Halter", "Máquina", "Polia", "Peso Corporal"]


def construir_sombra_orcela() -> ft.BoxShadow:
    """Retorna a sombra suave em Azul Orcela translúcido para os cards."""
    return ft.BoxShadow(
        color=ORCELA_SHADOW_COLOR,
        blur_radius=12,
        spread_radius=0,
    )


def construir_borda_input(raio: float = 8.0) -> dict[ft.ControlState, ft.InputBorder]:
    """Cria o mapeamento moderno de bordas Flet 1.x sem DeprecationWarning."""
    return {
        ft.ControlState.DEFAULT: ft.OutlineInputBorder(
            side=ft.BorderSide(width=1, color=ORCELA_BORDER_GLOW),
            border_radius=raio,
        ),
        ft.ControlState.FOCUSED: ft.OutlineInputBorder(
            side=ft.BorderSide(width=2, color=ORCELA_BLUE),
            border_radius=raio,
        ),
    }


def construir_logo_p4() -> ft.Text:
    """Retorna o componente oficial da logo P4 WORKOUT."""
    return ft.Text(
        size=26,
        weight=ft.FontWeight.W_900,
        spans=[
            ft.TextSpan("P", ft.TextStyle(color=PURE_WHITE, weight=ft.FontWeight.W_900)),
            ft.TextSpan("4", ft.TextStyle(color=ORCELA_BLUE, weight=ft.FontWeight.W_900)),
            ft.TextSpan(
                " WORKOUT", ft.TextStyle(color=PURE_WHITE, weight=ft.FontWeight.W_900)
            ),
        ],
    )


def build_routines_view(page: ft.Page) -> ft.Control:
    """Constrói a view modular de Gestão de Fichas e Catálogo de Exercícios."""
    itens_rascunho: list[dict[str, Any]] = []
    exercicio_selecionado_id: int | None = None
    form_ficha_visivel = False
    form_exercicio_visivel = False
    form_exercicio_inline_visivel = False

    container_raiz = ft.Column(
        scroll=ft.ScrollMode.HIDDEN,
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

    tf_nome_ficha = ft.TextField(
        label="Nome da Ficha (ex: Treino A - Push)",
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=14,
    )
    tf_desc_ficha = ft.TextField(
        label="Descrição / Foco (opcional)",
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
    )

    txt_exercicio_selecionado = ft.Text(
        "Selecionar Exercício...",
        size=13,
        weight=ft.FontWeight.BOLD,
        color=PURE_WHITE,
        expand=True,
        max_lines=1,
        overflow=ft.TextOverflow.ELLIPSIS,
    )
    txt_grupo_selecionado = ft.Text(
        "Toque para buscar",
        size=11,
        color=ORCELA_BLUE,
    )
    tf_series_alvo = ft.TextField(
        label="Séries",
        value="4",
        width=75,
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
    )
    tf_reps_alvo = ft.TextField(
        label="Reps",
        value="8-12",
        width=90,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
    )
    tf_descanso = ft.TextField(
        label="Desc (s)",
        value="90",
        width=90,
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
    )

    tf_novo_ex_nome = ft.TextField(
        label="Nome do Novo Exercício",
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
    )
    dd_novo_ex_grupo = ft.Dropdown(
        label="Grupo Muscular",
        value="Peito",
        border=construir_borda_input(),
        color=PURE_WHITE,
        expand=True,
        options=[ft.dropdown.Option(key=g, text=g) for g in GRUPOS_MUSCULARES],
    )
    dd_novo_ex_equip = ft.Dropdown(
        label="Equipamento",
        value="Barra",
        border=construir_borda_input(),
        color=PURE_WHITE,
        expand=True,
        options=[ft.dropdown.Option(key=e, text=e) for e in EQUIPAMENTOS],
    )

    def atualizar_opcoes_exercicios() -> dict[int, str]:
        nonlocal exercicio_selecionado_id
        exercicios = listar_exercicios()
        mapa = {ex.id: f"{ex.nome} ({ex.grupo_muscular})" for ex in exercicios}
        if exercicios:
            if exercicio_selecionado_id is None or exercicio_selecionado_id not in mapa:
                exercicio_selecionado_id = exercicios[0].id
            ex_sel = next(
                (e for e in exercicios if e.id == exercicio_selecionado_id),
                exercicios[0],
            )
            txt_exercicio_selecionado.value = ex_sel.nome
            txt_grupo_selecionado.value = (
                f"{ex_sel.grupo_muscular} • {ex_sel.equipamento}"
            )
        else:
            txt_exercicio_selecionado.value = "Nenhum exercício cadastrado"
            txt_grupo_selecionado.value = ""
        return mapa

    def abrir_modal_busca_exercicio(_: Any = None) -> None:
        nonlocal exercicio_selecionado_id
        todos_exercicios = listar_exercicios()

        lista_filtrada = ft.ListView(
            height=280,
            spacing=4,
        )

        def _selecionar_exercicio(ex_obj: Any) -> None:
            nonlocal exercicio_selecionado_id
            exercicio_selecionado_id = ex_obj.id
            txt_exercicio_selecionado.value = ex_obj.nome
            txt_grupo_selecionado.value = (
                f"{ex_obj.grupo_muscular} • {ex_obj.equipamento}"
            )
            page.pop_dialog()
            page.update()

        def _popular_lista(termo_busca: str = "") -> None:
            termo = termo_busca.strip().lower()
            itens_lv: list[ft.Control] = []
            for ex in todos_exercicios:
                if (
                    not termo
                    or termo in ex.nome.lower()
                    or termo in ex.grupo_muscular.lower()
                    or termo in ex.equipamento.lower()
                ):
                    selecionado = ex.id == exercicio_selecionado_id
                    itens_lv.append(
                        ft.Container(
                            bgcolor=ORCELA_DARK_SURFACE
                            if selecionado
                            else DARK_BG,
                            border=ft.Border.all(
                                1,
                                ORCELA_BLUE
                                if selecionado
                                else ORCELA_BORDER_GLOW,
                            ),
                            border_radius=8,
                            padding=ft.Padding.symmetric(
                                horizontal=12, vertical=8
                            ),
                            on_click=lambda _, e_item=ex: _selecionar_exercicio(
                                e_item
                            ),
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=8,
                                controls=[
                                    ft.Column(
                                        spacing=2,
                                        expand=True,
                                        controls=[
                                            ft.Text(
                                                ex.nome,
                                                size=13,
                                                weight=ft.FontWeight.BOLD,
                                                color=PURE_WHITE,
                                            ),
                                            ft.Text(
                                                f"{ex.grupo_muscular} • {ex.equipamento}",
                                                size=11,
                                                color=ORCELA_BLUE,
                                                weight=ft.FontWeight.W_500,
                                            ),
                                        ],
                                    ),
                                    ft.Icon(
                                        ft.Icons.CHECK_CIRCLE_ROUNDED
                                        if selecionado
                                        else ft.Icons.CHEVRON_RIGHT_ROUNDED,
                                        color=ORCELA_BLUE
                                        if selecionado
                                        else TEXT_MUTED,
                                        size=18,
                                    ),
                                ],
                            ),
                        )
                    )
            if not itens_lv:
                itens_lv.append(
                    ft.Container(
                        padding=16,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Text(
                            "Nenhum exercício encontrado para esta busca.",
                            size=12,
                            color=TEXT_MUTED,
                        ),
                    )
                )
            lista_filtrada.controls = itens_lv

        tf_busca_ex = ft.TextField(
            hint_text="Buscar exercício ou músculo...",
            autofocus=True,
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            border=construir_borda_input(),
            color=PURE_WHITE,
            text_size=13,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            on_change=lambda e: (_popular_lista(e.control.value or ""), page.update()),
        )

        _popular_lista("")

        dlg_busca = ft.AlertDialog(
            bgcolor=CARD_BG,
            shape=ft.RoundedRectangleBorder(
                radius=14, side=ft.BorderSide(width=1, color=ORCELA_BORDER_HIGHLIGHT)
            ),
            title=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(
                        "Selecionar Exercício",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=PURE_WHITE,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE_ROUNDED,
                        icon_color=TEXT_MUTED,
                        width=32,
                        height=32,
                        icon_size=18,
                        on_click=lambda _: page.pop_dialog(),
                    ),
                ],
            ),
            content=ft.Container(
                width=320,
                content=ft.Column(
                    tight=True,
                    spacing=10,
                    controls=[
                        tf_busca_ex,
                        lista_filtrada,
                    ],
                ),
            ),
        )
        page.show_dialog(dlg_busca)

    btn_seletor_exercicio = ft.Container(
        expand=True,
        bgcolor=DARK_BG,
        border=ft.Border.all(1, ORCELA_BORDER_GLOW),
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=12, vertical=10),
        on_click=abrir_modal_busca_exercicio,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Icon(
                    ft.Icons.SEARCH_ROUNDED,
                    color=ORCELA_BLUE,
                    size=20,
                ),
                ft.Column(
                    spacing=1,
                    expand=True,
                    controls=[
                        txt_exercicio_selecionado,
                        txt_grupo_selecionado,
                    ],
                ),
                ft.Icon(
                    ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED,
                    color=ORCELA_BLUE,
                    size=22,
                ),
            ],
        ),
    )

    def alternar_form_ficha(_: Any = None) -> None:
        nonlocal form_ficha_visivel, form_exercicio_inline_visivel
        form_ficha_visivel = not form_ficha_visivel
        if not form_ficha_visivel:
            form_exercicio_inline_visivel = False
        renderizar()

    def alternar_form_exercicio(_: Any = None) -> None:
        nonlocal form_exercicio_visivel
        form_exercicio_visivel = not form_exercicio_visivel
        renderizar()

    def alternar_form_exercicio_inline(_: Any = None) -> None:
        nonlocal form_exercicio_inline_visivel
        form_exercicio_inline_visivel = not form_exercicio_inline_visivel
        renderizar()

    def salvar_novo_exercicio(_: Any = None) -> None:
        nonlocal form_exercicio_visivel, form_exercicio_inline_visivel, exercicio_selecionado_id
        try:
            novo = criar_exercicio(
                nome=tf_novo_ex_nome.value or "",
                grupo_muscular=dd_novo_ex_grupo.value or "Peito",
                equipamento=dd_novo_ex_equip.value or "Barra",
            )
            tf_novo_ex_nome.value = ""
            form_exercicio_visivel = False
            form_exercicio_inline_visivel = False
            exercicio_selecionado_id = novo.id
            atualizar_opcoes_exercicios()
            notificar(f"Exercício '{novo.nome}' criado e selecionado!")
            renderizar()
        except Exception as exc:
            notificar(str(exc), erro=True)

    def adicionar_item_rascunho(_: Any = None) -> None:
        if exercicio_selecionado_id is None:
            notificar("Selecione um exercício do catálogo.", erro=True)
            return
        try:
            ex_id = int(exercicio_selecionado_id)
            series = max(1, int(tf_series_alvo.value or "4"))
            descanso = max(15, int(tf_descanso.value or "90"))
            reps = (tf_reps_alvo.value or "8-12").strip()
        except ValueError:
            notificar("Séries e descanso devem ser números inteiros.", erro=True)
            return

        mapa_nomes = atualizar_opcoes_exercicios()
        itens_rascunho.append(
            {
                "exercicio_id": ex_id,
                "nome_exibicao": mapa_nomes.get(ex_id, f"Exercício #{ex_id}"),
                "ordem": len(itens_rascunho) + 1,
                "series_alvo": series,
                "reps_alvo": reps,
                "descanso_segundos": descanso,
            }
        )
        renderizar()

    def remover_item_rascunho(indice: int) -> None:
        if 0 <= indice < len(itens_rascunho):
            itens_rascunho.pop(indice)
            for idx, item in enumerate(itens_rascunho, start=1):
                item["ordem"] = idx
            renderizar()

    def mover_item_rascunho(indice: int, direcao: str) -> None:
        if direcao == "subir" and indice > 0:
            itens_rascunho[indice - 1], itens_rascunho[indice] = (
                itens_rascunho[indice],
                itens_rascunho[indice - 1],
            )
        elif direcao == "descer" and indice < len(itens_rascunho) - 1:
            itens_rascunho[indice + 1], itens_rascunho[indice] = (
                itens_rascunho[indice],
                itens_rascunho[indice + 1],
            )
        for idx, item in enumerate(itens_rascunho, start=1):
            item["ordem"] = idx
        renderizar()

    def reordenar_exercicio_salvo(ficha_ex_id: int, direcao: str) -> None:
        mover_exercicio_ficha(ficha_ex_id, direcao)
        renderizar()

    def abrir_dialogo_editar_ficha(
        ficha_id: int, nome_atual: str, desc_atual: str | None
    ) -> None:
        tf_edit_nome = ft.TextField(
            label="Nome da Ficha",
            value=nome_atual,
            border=construir_borda_input(),
            color=PURE_WHITE,
            text_size=14,
        )
        tf_edit_desc = ft.TextField(
            label="Descrição / Foco (opcional)",
            value=desc_atual or "",
            border=construir_borda_input(),
            color=PURE_WHITE,
            text_size=13,
        )

        def _salvar_edicao_ficha(_: Any) -> None:
            try:
                renomear_ficha(
                    ficha_id=ficha_id,
                    novo_nome=tf_edit_nome.value or "",
                    descricao=tf_edit_desc.value,
                )
                page.pop_dialog()
                notificar("Ficha atualizada com sucesso!")
                renderizar()
            except Exception as exc:
                notificar(str(exc), erro=True)

        dlg_ficha = ft.AlertDialog(
            bgcolor=CARD_BG,
            shape=ft.RoundedRectangleBorder(
                radius=14, side=ft.BorderSide(width=1, color=ORCELA_BORDER_HIGHLIGHT)
            ),
            title=ft.Text(
                "Editar Ficha de Treino",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=PURE_WHITE,
            ),
            content=ft.Column(
                tight=True,
                spacing=10,
                controls=[tf_edit_nome, tf_edit_desc],
            ),
            actions=[
                ft.TextButton(
                    content="Cancelar",
                    on_click=lambda _: page.pop_dialog(),
                ),
                ft.Button(
                    content="Salvar",
                    bgcolor=ORCELA_BLUE,
                    color=PURE_WHITE,
                    on_click=_salvar_edicao_ficha,
                ),
            ],
        )
        page.show_dialog(dlg_ficha)

    def abrir_dialogo_editar_exercicio_ficha(item_ficha: Any) -> None:
        tf_ed_series = ft.TextField(
            label="Séries Alvo",
            value=str(item_ficha.series_alvo),
            keyboard_type=ft.KeyboardType.NUMBER,
            border=construir_borda_input(),
            color=PURE_WHITE,
            text_size=13,
            expand=True,
        )
        tf_ed_reps = ft.TextField(
            label="Repetições Alvo",
            value=str(item_ficha.reps_alvo),
            border=construir_borda_input(),
            color=PURE_WHITE,
            text_size=13,
            expand=True,
        )
        tf_ed_descanso = ft.TextField(
            label="Descanso (segundos)",
            value=str(item_ficha.descanso_segundos),
            keyboard_type=ft.KeyboardType.NUMBER,
            border=construir_borda_input(),
            color=PURE_WHITE,
            text_size=13,
        )
        tf_ed_obs = ft.TextField(
            label="Observações (ex: Cadência 3010, Pausa 2s)",
            value=getattr(item_ficha, "observacoes", None) or "",
            border=construir_borda_input(),
            color=PURE_WHITE,
            text_size=13,
        )

        def _salvar_edicao_item(_: Any) -> None:
            try:
                s_val = int(tf_ed_series.value or "4")
                d_val = int(tf_ed_descanso.value or "90")
                atualizar_ficha_exercicio(
                    ficha_exercicio_id=item_ficha.id,
                    series_alvo=s_val,
                    reps_alvo=tf_ed_reps.value or "8-12",
                    descanso_segundos=d_val,
                    observacoes=tf_ed_obs.value,
                )
                page.pop_dialog()
                notificar(f"'{item_ficha.exercicio.nome}' atualizado!")
                renderizar()
            except ValueError as exc:
                notificar(str(exc), erro=True)

        dlg_item = ft.AlertDialog(
            bgcolor=CARD_BG,
            shape=ft.RoundedRectangleBorder(
                radius=14, side=ft.BorderSide(width=1, color=ORCELA_BORDER_HIGHLIGHT)
            ),
            title=ft.Text(
                f"Editar • {item_ficha.exercicio.nome}",
                size=15,
                weight=ft.FontWeight.BOLD,
                color=PURE_WHITE,
            ),
            content=ft.Column(
                tight=True,
                spacing=10,
                controls=[
                    ft.Row(spacing=8, controls=[tf_ed_series, tf_ed_reps]),
                    tf_ed_descanso,
                    tf_ed_obs,
                ],
            ),
            actions=[
                ft.TextButton(
                    content="Cancelar",
                    on_click=lambda _: page.pop_dialog(),
                ),
                ft.Button(
                    content="Salvar",
                    bgcolor=ORCELA_BLUE,
                    color=PURE_WHITE,
                    on_click=_salvar_edicao_item,
                ),
            ],
        )
        page.show_dialog(dlg_item)

    def salvar_ficha_completa(_: Any = None) -> None:
        nonlocal form_ficha_visivel, form_exercicio_inline_visivel
        try:
            ficha = criar_ficha(
                nome=tf_nome_ficha.value or "",
                descricao=tf_desc_ficha.value or "",
                itens=itens_rascunho,
            )
            tf_nome_ficha.value = ""
            tf_desc_ficha.value = ""
            itens_rascunho.clear()
            form_ficha_visivel = False
            form_exercicio_inline_visivel = False
            notificar(f"Ficha '{ficha.nome}' criada com sucesso!")
            renderizar()
        except Exception as exc:
            notificar(str(exc), erro=True)

    def deletar_ficha_existente(ficha_id: int, nome_ficha: str) -> None:
        excluir_ficha(ficha_id)
        notificar(f"Ficha '{nome_ficha}' removida.")
        renderizar()

    def construir_painel_novo_exercicio(fechar_callback: Any) -> ft.Container:
        return ft.Container(
            bgcolor=DARK_BG,
            border=ft.Border.all(1, ORCELA_BORDER_HIGHLIGHT),
            shadow=construir_sombra_orcela(),
            border_radius=10,
            padding=12,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                "Novo Exercício no Catálogo",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=PURE_WHITE,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE_ROUNDED,
                                icon_color=TEXT_MUTED,
                                on_click=fechar_callback,
                            ),
                        ],
                    ),
                    tf_novo_ex_nome,
                    ft.Row(spacing=8, controls=[dd_novo_ex_grupo, dd_novo_ex_equip]),
                    ft.Button(
                        content="SALVAR E SELECIONAR",
                        icon=ft.Icons.CHECK_ROUNDED,
                        bgcolor=ORCELA_BLUE,
                        color=PURE_WHITE,
                        width=float("inf"),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                        on_click=salvar_novo_exercicio,
                    ),
                ],
            ),
        )

    def renderizar(atualizar_pagina: bool = True) -> None:
        atualizar_opcoes_exercicios()
        fichas = listar_fichas(apenas_ativas=True)
        exercicios_catalogo = listar_exercicios()

        controles: list[ft.Control] = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            construir_logo_p4(),
                            ft.Text(
                                f"Fichas & Catálogo ({len(exercicios_catalogo)} exercícios)",
                                size=12,
                                color=TEXT_MUTED,
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.FITNESS_CENTER_ROUNDED,
                                icon_color=ORCELA_BLUE,
                                bgcolor=ORCELA_DARK_SURFACE,
                                tooltip="Novo Exercício no Catálogo",
                                on_click=alternar_form_exercicio,
                            ),
                            ft.Button(
                                content="NOVA FICHA",
                                icon=ft.Icons.ADD_ROUNDED,
                                bgcolor=ORCELA_BLUE,
                                color=PURE_WHITE,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                                on_click=alternar_form_ficha,
                            ),
                        ],
                    ),
                ],
            )
        ]

        if form_exercicio_visivel and not form_ficha_visivel:
            controles.append(construir_painel_novo_exercicio(alternar_form_exercicio))

        if form_ficha_visivel:
            linhas_rascunho: list[ft.Control] = []
            total_rascunho = len(itens_rascunho)
            for idx, item in enumerate(itens_rascunho):
                eh_primeiro_r = idx == 0
                eh_ultimo_r = idx == total_rascunho - 1
                linhas_rascunho.append(
                    ft.Container(
                        bgcolor=DARK_BG,
                        border=ft.Border.all(1, ORCELA_BORDER_GLOW),
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=6),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                            controls=[
                                ft.Column(
                                    spacing=2,
                                    expand=True,
                                    controls=[
                                        ft.Text(
                                            size=13,
                                            spans=[
                                                ft.TextSpan(
                                                    f"{item['ordem']}. ",
                                                    ft.TextStyle(
                                                        color=ORCELA_BLUE,
                                                        weight=ft.FontWeight.BOLD,
                                                    ),
                                                ),
                                                ft.TextSpan(
                                                    str(item["nome_exibicao"]),
                                                    ft.TextStyle(
                                                        color=PURE_WHITE,
                                                        weight=ft.FontWeight.BOLD,
                                                    ),
                                                ),
                                            ],
                                        ),
                                        ft.Text(
                                            f"{item['series_alvo']} séries x {item['reps_alvo']} reps • {item['descanso_segundos']}s descanso",
                                            size=11,
                                            color=ORCELA_BLUE,
                                        ),
                                    ],
                                ),
                                ft.Row(
                                    spacing=2,
                                    controls=[
                                        ft.IconButton(
                                            icon=ft.Icons.KEYBOARD_ARROW_UP_ROUNDED,
                                            icon_size=18,
                                            width=30,
                                            height=30,
                                            disabled=eh_primeiro_r,
                                            icon_color=SURFACE_BORDER
                                            if eh_primeiro_r
                                            else ORCELA_BLUE,
                                            tooltip="Subir exercício",
                                            on_click=lambda _, i=idx: mover_item_rascunho(
                                                i, "subir"
                                            ),
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED,
                                            icon_size=18,
                                            width=30,
                                            height=30,
                                            disabled=eh_ultimo_r,
                                            icon_color=SURFACE_BORDER
                                            if eh_ultimo_r
                                            else ORCELA_BLUE,
                                            tooltip="Descer exercício",
                                            on_click=lambda _, i=idx: mover_item_rascunho(
                                                i, "descer"
                                            ),
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                            icon_size=18,
                                            width=30,
                                            height=30,
                                            icon_color=DANGER_RED,
                                            on_click=lambda _, i=idx: remover_item_rascunho(
                                                i
                                            ),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    )
                )

            controles_form_ficha: list[ft.Control] = [
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            "Nova Ficha de Treino",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=PURE_WHITE,
                            expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE_ROUNDED,
                            icon_color=TEXT_MUTED,
                            on_click=alternar_form_ficha,
                        ),
                    ],
                ),
                tf_nome_ficha,
                tf_desc_ficha,
                ft.Divider(height=1, color=SURFACE_BORDER),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        ft.Text(
                            "Adicionar Exercícios à Ficha",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=ORCELA_BLUE,
                            expand=True,
                        ),
                        ft.OutlinedButton(
                            content="Novo Exercício",
                            icon=ft.Icons.ADD_ROUNDED,
                            style=ft.ButtonStyle(
                                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                            ),
                            on_click=alternar_form_exercicio_inline,
                        ),
                    ],
                ),
            ]

            if form_exercicio_inline_visivel:
                controles_form_ficha.append(
                    construir_painel_novo_exercicio(alternar_form_exercicio_inline)
                )

            controles_form_ficha.extend(
                [
                    ft.Row(controls=[btn_seletor_exercicio]),
                    ft.Row(
                        spacing=8,
                        controls=[
                            tf_series_alvo,
                            tf_reps_alvo,
                            tf_descanso,
                            ft.IconButton(
                                icon=ft.Icons.ADD_CIRCLE_ROUNDED,
                                icon_color=ORCELA_BLUE,
                                icon_size=30,
                                tooltip="Incluir na ficha",
                                on_click=adicionar_item_rascunho,
                            ),
                        ],
                    ),
                    ft.Column(spacing=6, controls=linhas_rascunho),
                    ft.Button(
                        content="SALVAR FICHA",
                        icon=ft.Icons.SAVE_ROUNDED,
                        bgcolor=ORCELA_BLUE,
                        color=PURE_WHITE,
                        width=float("inf"),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                        on_click=salvar_ficha_completa,
                    ),
                ]
            )

            controles.append(
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, ORCELA_BORDER_HIGHLIGHT),
                    shadow=construir_sombra_orcela(),
                    border_radius=14,
                    padding=16,
                    content=ft.Column(spacing=12, controls=controles_form_ficha),
                )
            )

        controles.append(
            ft.Text(
                "MINHAS FICHAS CADASTRADAS",
                size=12,
                weight=ft.FontWeight.BOLD,
                color=TEXT_MUTED,
            )
        )

        if not fichas:
            controles.append(
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, ORCELA_BORDER_GLOW),
                    shadow=construir_sombra_orcela(),
                    border_radius=12,
                    padding=20,
                    content=ft.Text(
                        "Nenhuma ficha ativa. Toque em 'NOVA FICHA' acima para criar.",
                        size=13,
                        color=TEXT_MUTED,
                    ),
                )
            )
        else:
            for ficha in fichas:
                total_itens_ficha = len(ficha.itens)
                linhas_ex: list[ft.Control] = []
                for idx_it, item in enumerate(ficha.itens):
                    eh_primeiro = idx_it == 0
                    eh_ultimo = idx_it == total_itens_ficha - 1
                    obs_txt = getattr(item, "observacoes", None)
                    bloco_texto_ex: list[ft.Control] = [
                        ft.Text(
                            size=13,
                            spans=[
                                ft.TextSpan(
                                    f"{idx_it + 1}. ",
                                    ft.TextStyle(
                                        color=ORCELA_BLUE,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ),
                                ft.TextSpan(
                                    item.exercicio.nome,
                                    ft.TextStyle(
                                        color=PURE_WHITE,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                ),
                            ],
                        )
                    ]
                    if obs_txt:
                        bloco_texto_ex.append(
                            ft.Text(
                                obs_txt,
                                size=11,
                                color=TEXT_MUTED,
                            )
                        )

                    linhas_ex.append(
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                            controls=[
                                ft.Column(
                                    spacing=1,
                                    expand=True,
                                    controls=bloco_texto_ex,
                                ),
                                ft.Container(
                                    bgcolor=ORCELA_DARK_SURFACE,
                                    padding=ft.Padding.symmetric(
                                        horizontal=7, vertical=3
                                    ),
                                    border_radius=6,
                                    content=ft.Text(
                                        f"{item.series_alvo}x {item.reps_alvo} • {item.descanso_segundos}s",
                                        size=11,
                                        color=ORCELA_BLUE,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ),
                                ft.Row(
                                    spacing=0,
                                    controls=[
                                        ft.IconButton(
                                            icon=ft.Icons.EDIT_ROUNDED,
                                            icon_size=16,
                                            width=28,
                                            height=28,
                                            icon_color=ORCELA_BLUE,
                                            tooltip="Editar séries, reps e descanso",
                                            on_click=lambda _, it=item: abrir_dialogo_editar_exercicio_ficha(
                                                it
                                            ),
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.KEYBOARD_ARROW_UP_ROUNDED,
                                            icon_size=18,
                                            width=28,
                                            height=28,
                                            disabled=eh_primeiro,
                                            icon_color=SURFACE_BORDER
                                            if eh_primeiro
                                            else ORCELA_BLUE,
                                            tooltip="Subir exercício",
                                            on_click=lambda _, feid=item.id: reordenar_exercicio_salvo(
                                                feid, "subir"
                                            ),
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED,
                                            icon_size=18,
                                            width=28,
                                            height=28,
                                            disabled=eh_ultimo,
                                            icon_color=SURFACE_BORDER
                                            if eh_ultimo
                                            else ORCELA_BLUE,
                                            tooltip="Descer exercício",
                                            on_click=lambda _, feid=item.id: reordenar_exercicio_salvo(
                                                feid, "descer"
                                            ),
                                        ),
                                    ],
                                ),
                            ],
                        )
                    )

                controles.append(
                    ft.Container(
                        bgcolor=CARD_BG,
                        border=ft.Border.all(1, ORCELA_BORDER_GLOW),
                        shadow=construir_sombra_orcela(),
                        border_radius=14,
                        padding=16,
                        animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                        animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK),
                        content=ft.Column(
                            spacing=10,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Column(
                                            spacing=2,
                                            expand=True,
                                            controls=[
                                                ft.Text(
                                                    ficha.nome,
                                                    size=16,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=PURE_WHITE,
                                                ),
                                                ft.Text(
                                                    ficha.descricao or "Sem descrição",
                                                    size=12,
                                                    color=TEXT_MUTED,
                                                ),
                                            ],
                                        ),
                                        ft.Row(
                                            spacing=2,
                                            controls=[
                                                ft.IconButton(
                                                    icon=ft.Icons.EDIT_ROUNDED,
                                                    icon_color=ORCELA_BLUE,
                                                    tooltip="Editar nome e descrição da ficha",
                                                    on_click=lambda _, fid=ficha.id, fn=ficha.nome, fd=ficha.descricao: abrir_dialogo_editar_ficha(
                                                        fid, fn, fd
                                                    ),
                                                ),
                                                ft.IconButton(
                                                    icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                                    icon_color=DANGER_RED,
                                                    tooltip="Excluir Ficha",
                                                    on_click=lambda _, fid=ficha.id, fnome=ficha.nome: deletar_ficha_existente(
                                                        fid, fnome
                                                    ),
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                ft.Divider(height=1, color=SURFACE_BORDER),
                                ft.Column(spacing=6, controls=linhas_ex),
                            ],
                        ),
                    )
                )

        container_raiz.controls = controles
        if atualizar_pagina:
            page.update()

    renderizar(atualizar_pagina=False)
    return container_raiz
