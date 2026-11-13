import flet as ft

from core.seed import init_db
from views.cardio_view import build_cardio_view
from views.nutrition_view import build_nutrition_view
from views.routines_view import (
    CARD_BG,
    DARK_BG,
    ORCELA_BLUE,
    ORCELA_DARK_SURFACE,
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

    page.navigation_bar = ft.NavigationBar(
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

    conteudo_principal.content = build_train_view(page)
    page.add(ft.SafeArea(expand=True, content=conteudo_principal))


if __name__ == "__main__":
    ft.run(main)
