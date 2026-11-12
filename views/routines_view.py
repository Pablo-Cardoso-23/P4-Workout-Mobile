from typing import Any

import flet as ft

from services.workout_service import (
    criar_exercicio,
    criar_ficha,
    excluir_ficha,
    listar_exercicios,
    listar_fichas,
)

ORCELA_BLUE = "#007BFF"
ORCELA_DARK_SURFACE = "#002B5C"
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


def construir_borda_input(raio: float = 8.0) -> dict[ft.ControlState, ft.InputBorder]:
    """Cria o mapeamento moderno de bordas Flet 1.x sem DeprecationWarning."""
    return {
        ft.ControlState.DEFAULT: ft.OutlineInputBorder(
            side=ft.BorderSide(width=1, color=SURFACE_BORDER),
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
    form_ficha_visivel = False
    form_exercicio_visivel = False
    form_exercicio_inline_visivel = False

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

    dd_exercicio = ft.Dropdown(
        label="Selecionar Exercício",
        border=construir_borda_input(),
        color=PURE_WHITE,
        expand=True,
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
        exercicios = listar_exercicios()
        mapa = {ex.id: f"{ex.nome} ({ex.grupo_muscular})" for ex in exercicios}
        dd_exercicio.options = [
            ft.dropdown.Option(key=str(ex.id), text=f"{ex.nome} • {ex.grupo_muscular}")
            for ex in exercicios
        ]
        if exercicios and not dd_exercicio.value:
            dd_exercicio.value = str(exercicios[0].id)
        return mapa

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
        nonlocal form_exercicio_visivel, form_exercicio_inline_visivel
        try:
            novo = criar_exercicio(
                nome=tf_novo_ex_nome.value or "",
                grupo_muscular=dd_novo_ex_grupo.value or "Peito",
                equipamento=dd_novo_ex_equip.value or "Barra",
            )
            tf_novo_ex_nome.value = ""
            form_exercicio_visivel = False
            form_exercicio_inline_visivel = False
            atualizar_opcoes_exercicios()
            dd_exercicio.value = str(novo.id)
            notificar(f"Exercício '{novo.nome}' criado e selecionado!")
            renderizar()
        except Exception as exc:
            notificar(str(exc), erro=True)

    def adicionar_item_rascunho(_: Any = None) -> None:
        if not dd_exercicio.value:
            notificar("Selecione um exercício do catálogo.", erro=True)
            return
        try:
            ex_id = int(dd_exercicio.value)
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
            border=ft.Border.all(1, ORCELA_BLUE),
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
            for idx, item in enumerate(itens_rascunho):
                linhas_rascunho.append(
                    ft.Container(
                        bgcolor=DARK_BG,
                        border=ft.Border.all(1, SURFACE_BORDER),
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(
                                    spacing=2,
                                    expand=True,
                                    controls=[
                                        ft.Text(
                                            f"{item['ordem']}. {item['nome_exibicao']}",
                                            size=13,
                                            weight=ft.FontWeight.BOLD,
                                            color=PURE_WHITE,
                                        ),
                                        ft.Text(
                                            f"{item['series_alvo']} séries x {item['reps_alvo']} reps • {item['descanso_segundos']}s descanso",
                                            size=11,
                                            color=ORCELA_BLUE,
                                        ),
                                    ],
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                    icon_color=DANGER_RED,
                                    on_click=lambda _, i=idx: remover_item_rascunho(i),
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
                            content="+ Exercício",
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
                    ft.Row(controls=[dd_exercicio]),
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
                    border=ft.Border.all(1, ORCELA_BLUE),
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
                    border=ft.Border.all(1, SURFACE_BORDER),
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
                linhas_ex = [
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                f"{item.ordem}. {item.exercicio.nome}",
                                size=13,
                                color=PURE_WHITE,
                            ),
                            ft.Container(
                                bgcolor=ORCELA_DARK_SURFACE,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                border_radius=6,
                                content=ft.Text(
                                    f"{item.series_alvo}x {item.reps_alvo} • {item.descanso_segundos}s",
                                    size=11,
                                    color=ORCELA_BLUE,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ),
                        ],
                    )
                    for item in ficha.itens
                ]

                controles.append(
                    ft.Container(
                        bgcolor=CARD_BG,
                        border=ft.Border.all(1, SURFACE_BORDER),
                        border_radius=14,
                        padding=16,
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
