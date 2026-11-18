import asyncio

import flet as ft

from core.seed import init_db
from views.cardio_view import build_cardio_view
from views.nutrition_view import build_nutrition_view
from views.routines_view import (
    CARD_BG,
    DARK_BG,
    ORCELA_BLUE,
    ORCELA_DARK_SURFACE,
    PURE_WHITE,
    SURFACE_BORDER,
    TEXT_MUTED,
    build_routines_view,
)
from views.stats_view import build_stats_view
from views.train_view import build_train_view

CYAN_HUD = "#00E5FF"


def main(page: ft.Page) -> None:
    init_db()

    page.title = "P4 Workout"
    page.window.width = 400
    page.window.height = 820
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = DARK_BG
    page.padding = 0

    tema_app = ft.Theme(
        color_scheme_seed=ORCELA_BLUE,
        scaffold_bgcolor=DARK_BG,
        scrollbar_theme=ft.ScrollbarTheme(thickness=0.0, radius=0),
    )
    page.theme = tema_app
    page.dark_theme = tema_app

    switcher_abas = ft.AnimatedSwitcher(
        content=ft.Container(expand=True),
        expand=True,
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=250,
        reverse_duration=150,
        switch_in_curve=ft.AnimationCurve.EASE_OUT,
        switch_out_curve=ft.AnimationCurve.EASE_IN,
    )

    conteudo_principal = ft.Container(
        expand=True,
        padding=ft.Padding.symmetric(horizontal=16, vertical=20),
        opacity=1.0,
        animate_opacity=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
        content=switcher_abas,
    )

    def ao_trocar_aba(evento: ft.Event[ft.NavigationBar]) -> None:
        indice = evento.control.selected_index
        if indice == 0:
            nova_view = build_train_view(page)
        elif indice == 1:
            nova_view = build_cardio_view(page)
        elif indice == 2:
            nova_view = build_routines_view(page)
        elif indice == 3:
            nova_view = build_stats_view(page)
        else:
            nova_view = build_nutrition_view(page)
        switcher_abas.content = ft.Container(
            key=f"tab_{indice}",
            expand=True,
            content=nova_view,
        )
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

    # Camada 1 — Halo de Energia Radial
    halo_radial = ft.Container(
        width=180,
        height=180,
        border_radius=90,
        bgcolor="#14007BFF",
        shadow=ft.BoxShadow(
            color="#66007BFF",
            blur_radius=80,
            spread_radius=12,
        ),
        scale=0.4,
        opacity=0.0,
        animate_scale=ft.Animation(600, ft.AnimationCurve.EASE_OUT_BACK),
        animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
    )

    # Camada 2 — Cantoneiras HUD (Mira de Precisão 260x260)
    quadro_hud = ft.Container(
        width=260,
        height=260,
        scale=1.25,
        opacity=0.0,
        animate_scale=ft.Animation(520, ft.AnimationCurve.EASE_OUT_EXPO),
        animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
        content=ft.Stack(
            controls=[
                ft.Container(
                    width=24,
                    height=24,
                    top=0,
                    left=0,
                    border=ft.Border.only(
                        top=ft.BorderSide(2.5, ORCELA_BLUE),
                        left=ft.BorderSide(2.5, CYAN_HUD),
                    ),
                ),
                ft.Container(
                    width=24,
                    height=24,
                    top=0,
                    right=0,
                    border=ft.Border.only(
                        top=ft.BorderSide(2.5, ORCELA_BLUE),
                        right=ft.BorderSide(2.5, CYAN_HUD),
                    ),
                ),
                ft.Container(
                    width=24,
                    height=24,
                    bottom=0,
                    left=0,
                    border=ft.Border.only(
                        bottom=ft.BorderSide(2.5, CYAN_HUD),
                        left=ft.BorderSide(2.5, ORCELA_BLUE),
                    ),
                ),
                ft.Container(
                    width=24,
                    height=24,
                    bottom=0,
                    right=0,
                    border=ft.Border.only(
                        bottom=ft.BorderSide(2.5, CYAN_HUD),
                        right=ft.BorderSide(2.5, ORCELA_BLUE),
                    ),
                ),
            ],
        ),
    )

    # Camada 3 — Emblema Central "P4 WORKOUT" & Feixe Laser
    bloco_logo_p4 = ft.Container(
        scale=0.6,
        opacity=0.0,
        animate_scale=ft.Animation(520, ft.AnimationCurve.EASE_OUT_BACK),
        animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
        content=ft.Text(
            size=64,
            weight=ft.FontWeight.W_900,
            spans=[
                ft.TextSpan(
                    "P",
                    ft.TextStyle(
                        color=PURE_WHITE,
                        weight=ft.FontWeight.W_900,
                    ),
                ),
                ft.TextSpan(
                    "4",
                    ft.TextStyle(
                        color=ORCELA_BLUE,
                        weight=ft.FontWeight.W_900,
                        shadow=ft.BoxShadow(
                            color="#99007BFF",
                            blur_radius=24,
                            spread_radius=2,
                        ),
                    ),
                ),
            ],
        ),
    )

    feixe_laser = ft.Container(
        width=0,
        height=3,
        border_radius=2,
        gradient=ft.LinearGradient(colors=[ORCELA_BLUE, CYAN_HUD, ORCELA_BLUE]),
        shadow=ft.BoxShadow(
            color="#8000E5FF",
            blur_radius=12,
            spread_radius=1,
        ),
        animate_size=ft.Animation(450, ft.AnimationCurve.EASE_OUT_EXPO),
    )

    bloco_txt_workout = ft.Container(
        opacity=0.0,
        offset=ft.Offset(0.0, 0.4),
        animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
        animate_offset=ft.Animation(420, ft.AnimationCurve.EASE_OUT_CUBIC),
        content=ft.Text(
            "W O R K O U T",
            size=18,
            weight=ft.FontWeight.W_900,
            color=PURE_WHITE,
            style=ft.TextStyle(letter_spacing=6, color=PURE_WHITE),
        ),
    )

    # Camada 4 — Barra de Telemetria na Base
    preenchimento_telemetria = ft.Container(
        width=0,
        height=2,
        border_radius=2,
        gradient=ft.LinearGradient(colors=[ORCELA_BLUE, CYAN_HUD]),
        animate_size=ft.Animation(950, ft.AnimationCurve.EASE_OUT_EXPO),
    )

    painel_telemetria_base = ft.Container(
        bottom=36,
        left=0,
        right=0,
        opacity=0.0,
        animate_opacity=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
        content=ft.Column(
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Text(
                    "INITIALIZING PERFORMANCE ENGINE...",
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT_MUTED,
                    style=ft.TextStyle(letter_spacing=2, color=TEXT_MUTED),
                ),
                ft.Container(
                    width=160,
                    height=2,
                    bgcolor=SURFACE_BORDER,
                    border_radius=2,
                    alignment=ft.Alignment.CENTER_LEFT,
                    content=preenchimento_telemetria,
                ),
            ],
        ),
    )

    tela_intro = ft.Container(
        expand=True,
        bgcolor=DARK_BG,
        scale=1.0,
        opacity=1.0,
        animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_IN_BACK),
        animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN),
        content=ft.Stack(
            expand=True,
            controls=[
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=halo_radial,
                ),
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=quadro_hud,
                ),
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            bloco_logo_p4,
                            feixe_laser,
                            bloco_txt_workout,
                        ],
                    ),
                ),
                painel_telemetria_base,
            ],
        ),
    )

    raiz_safe_area = ft.SafeArea(expand=True, content=tela_intro)
    page.add(raiz_safe_area)

    async def _executar_animacao_abertura() -> None:
        # Etapa 1 (0.05s): Halo radial + cantoneiras HUD + impacto P4
        await asyncio.sleep(0.05)
        halo_radial.scale = 1.0
        halo_radial.opacity = 1.0
        quadro_hud.scale = 1.0
        quadro_hud.opacity = 1.0
        bloco_logo_p4.scale = 1.0
        bloco_logo_p4.opacity = 1.0
        painel_telemetria_base.opacity = 1.0
        page.update()

        # Etapa 2 (0.35s): Expansão do feixe laser + W O R K O U T + telemetria
        await asyncio.sleep(0.30)
        feixe_laser.width = 210
        bloco_txt_workout.opacity = 1.0
        bloco_txt_workout.offset = ft.Offset(0.0, 0.0)
        preenchimento_telemetria.width = 160
        page.update()

        # Etapa 3 (1.55s): Transição de saída futurista (warp zoom: scale=1.15, opacity=0.0 em 300ms)
        await asyncio.sleep(1.20)
        tela_intro.scale = 1.15
        tela_intro.opacity = 0.0
        page.update()

        await asyncio.sleep(0.30)
        switcher_abas.content = ft.Container(
            key="tab_0",
            expand=True,
            content=build_train_view(page),
        )
        raiz_safe_area.content = conteudo_principal
        page.navigation_bar = barra_navegacao
        page.update()

    if hasattr(page, "run_task"):
        page.run_task(_executar_animacao_abertura)


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
