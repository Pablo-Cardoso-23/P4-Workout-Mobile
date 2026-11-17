import asyncio

import flet as ft

from core.seed import init_db
from views.cardio_view import build_cardio_view
from views.nutrition_view import build_nutrition_view
from views.routines_view import (
    CARD_BG,
    DARK_BG,
    ORCELA_BLUE,
    ORCELA_BORDER_HIGHLIGHT,
    ORCELA_DARK_SURFACE,
    PURE_WHITE,
    TEXT_MUTED,
    build_routines_view,
)
from views.stats_view import build_stats_view
from views.train_view import build_train_view


def main(page: ft.Page) -> None:
    init_db()

    page.title = "P4 Workout"
    page.window.width = 400
    page.window.height = 820
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = DARK_BG
    page.padding = 0

    page.theme = ft.Theme(
        color_scheme_seed=ORCELA_BLUE,
        scaffold_bgcolor=DARK_BG,
    )

    conteudo_principal = ft.Container(
        expand=True,
        padding=ft.Padding.symmetric(horizontal=16, vertical=20),
        opacity=1.0,
        animate_opacity=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
    )

    def ao_trocar_aba(evento: ft.Event[ft.NavigationBar]) -> None:
        indice = evento.control.selected_index
        if indice == 0:
            conteudo_principal.content = build_train_view(page)
        elif indice == 1:
            conteudo_principal.content = build_cardio_view(page)
        elif indice == 2:
            conteudo_principal.content = build_routines_view(page)
        elif indice == 3:
            conteudo_principal.content = build_stats_view(page)
        else:
            conteudo_principal.content = build_nutrition_view(page)
        page.update()

    barra_navegacao = ft.NavigationBar(
        selected_index=0,
        bgcolor=CARD_BG,
        indicator_color=ORCELA_DARK_SURFACE,
        on_change=ao_trocar_aba,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.FITNESS_CENTER_OUTLINED,
                selected_icon=ft.Icons.FITNESS_CENTER,
                label="Treinar",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.DIRECTIONS_RUN_OUTLINED,
                selected_icon=ft.Icons.DIRECTIONS_RUN,
                label="Cardio",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.LIST_ALT_OUTLINED,
                selected_icon=ft.Icons.LIST_ALT,
                label="Fichas",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.SHOW_CHART_OUTLINED,
                selected_icon=ft.Icons.SHOW_CHART,
                label="Evolução",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.RESTAURANT_OUTLINED,
                selected_icon=ft.Icons.RESTAURANT,
                label="Nutri",
            ),
        ],
    )

    emblema_splash = ft.Container(
        bgcolor=CARD_BG,
        border=ft.Border.all(2, ORCELA_BLUE),
        border_radius=28,
        padding=ft.Padding.symmetric(horizontal=36, vertical=32),
        shadow=ft.BoxShadow(
            color=ORCELA_BORDER_HIGHLIGHT,
            blur_radius=28,
            spread_radius=2,
        ),
        opacity=0.0,
        scale=0.82,
        animate_opacity=ft.Animation(550, ft.AnimationCurve.EASE_OUT),
        animate_scale=ft.Animation(600, ft.AnimationCurve.EASE_OUT_BACK),
        content=ft.Column(
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Icon(
                    ft.Icons.FITNESS_CENTER_ROUNDED,
                    color=ORCELA_BLUE,
                    size=44,
                ),
                ft.Text(
                    size=42,
                    weight=ft.FontWeight.W_900,
                    spans=[
                        ft.TextSpan(
                            "P",
                            ft.TextStyle(
                                color=PURE_WHITE, weight=ft.FontWeight.W_900
                            ),
                        ),
                        ft.TextSpan(
                            "4",
                            ft.TextStyle(
                                color=ORCELA_BLUE, weight=ft.FontWeight.W_900
                            ),
                        ),
                    ],
                ),
                ft.Container(
                    width=110,
                    height=3,
                    bgcolor=ORCELA_BLUE,
                    border_radius=2,
                ),
                ft.Text(
                    "WORKOUT",
                    size=16,
                    weight=ft.FontWeight.W_900,
                    color=PURE_WHITE,
                ),
                ft.Text(
                    "PERFORMANCE & ORGANIZATION",
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT_MUTED,
                ),
            ],
        ),
    )

    tela_intro = ft.Container(
        expand=True,
        bgcolor=DARK_BG,
        alignment=ft.Alignment.CENTER,
        content=emblema_splash,
    )

    raiz_safe_area = ft.SafeArea(expand=True, content=tela_intro)
    page.add(raiz_safe_area)

    async def _executar_animacao_abertura() -> None:
        await asyncio.sleep(0.05)
        emblema_splash.opacity = 1.0
        emblema_splash.scale = 1.0
        page.update()

        await asyncio.sleep(0.9)
        emblema_splash.animate_opacity = ft.Animation(
            300, ft.AnimationCurve.EASE_IN
        )
        emblema_splash.opacity = 0.0
        page.update()

        await asyncio.sleep(0.3)
        conteudo_principal.content = build_train_view(page)
        raiz_safe_area.content = conteudo_principal
        page.navigation_bar = barra_navegacao
        page.update()

    if hasattr(page, "run_task"):
        page.run_task(_executar_animacao_abertura)


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
