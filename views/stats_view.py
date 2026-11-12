from typing import Any

import flet as ft
import flet.canvas as cv

from services.analytics_service import (
    listar_exercicios_para_analise,
    obter_evolucao_exercicio,
    obter_historico_biometria,
    obter_metricas_gerais,
    obter_volume_por_grupo_muscular,
    registrar_biometria,
)
from views.routines_view import (
    CARD_BG,
    DANGER_RED,
    DARK_BG,
    GRUPOS_MUSCULARES,
    ORCELA_BLUE,
    ORCELA_DARK_SURFACE,
    PURE_WHITE,
    SURFACE_BORDER,
    TEXT_MUTED,
    construir_borda_input,
    construir_logo_p4,
)


def _construir_grafico_linha_evolucao(
    historico: list[dict[str, Any]],
) -> ft.Control:
    """Renderiza o gráfico de linha de evolução de Carga e 1RM (Epley) em alta definição."""
    if not historico:
        return ft.Container(
            bgcolor=DARK_BG,
            border=ft.Border.all(1, SURFACE_BORDER),
            border_radius=10,
            padding=20,
            alignment=ft.Alignment.CENTER,
            content=ft.Text(
                "Sem sessões finalizadas para este exercício ainda.\nRegistre séries de trabalho (W) ou falha (F) para ver a curva de evolução.",
                size=12,
                color=TEXT_MUTED,
                text_align=ft.TextAlign.CENTER,
            ),
        )

    pontos_recentes = historico[-8:]
    valores_1rm = [float(p["one_rm_estimado"]) for p in pontos_recentes]
    valores_carga = [float(p["carga_maxima_kg"]) for p in pontos_recentes]

    min_val = min(valores_carga) * 0.9 if valores_carga else 0.0
    max_val = max(valores_1rm) * 1.08 if valores_1rm else 100.0
    if max_val <= min_val:
        max_val = min_val + 10.0

    largura = 310.0
    altura = 145.0
    pad_x = 24.0
    pad_y = 20.0
    area_w = largura - (2 * pad_x)
    area_h = altura - (2 * pad_y)

    shapes: list[cv.Shape] = []
    paint_grid = ft.Paint(color=SURFACE_BORDER, stroke_width=1)

    for i in range(3):
        y_grid = pad_y + (area_h * i / 2.0)
        shapes.append(
            cv.Line(
                x1=pad_x,
                y1=y_grid,
                x2=largura - pad_x,
                y2=y_grid,
                paint=paint_grid,
            )
        )

    n = len(pontos_recentes)
    coords_1rm: list[tuple[float, float]] = []
    coords_carga: list[tuple[float, float]] = []

    for idx, ponto in enumerate(pontos_recentes):
        x = (
            pad_x + (area_w / 2.0)
            if n == 1
            else pad_x + (idx * area_w / float(n - 1))
        )
        ratio_1rm = (float(ponto["one_rm_estimado"]) - min_val) / (
            max_val - min_val
        )
        y_1rm = (pad_y + area_h) - (ratio_1rm * area_h)
        coords_1rm.append((x, y_1rm))

        ratio_carga = (float(ponto["carga_maxima_kg"]) - min_val) / (
            max_val - min_val
        )
        y_carga = (pad_y + area_h) - (ratio_carga * area_h)
        coords_carga.append((x, y_carga))

    paint_linha_1rm = ft.Paint(color=ORCELA_BLUE, stroke_width=3)
    paint_linha_carga = ft.Paint(color=PURE_WHITE, stroke_width=1.5)

    for i in range(len(coords_1rm) - 1):
        x1, y1 = coords_1rm[i]
        x2, y2 = coords_1rm[i + 1]
        shapes.append(cv.Line(x1=x1, y1=y1, x2=x2, y2=y2, paint=paint_linha_1rm))

        cx1, cy1 = coords_carga[i]
        cx2, cy2 = coords_carga[i + 1]
        shapes.append(
            cv.Line(x1=cx1, y1=cy1, x2=cx2, y2=cy2, paint=paint_linha_carga)
        )

    paint_ponto_ext = ft.Paint(color=ORCELA_BLUE)
    paint_ponto_int = ft.Paint(color=PURE_WHITE)

    for x, y in coords_1rm:
        shapes.append(cv.Circle(x=x, y=y, radius=5, paint=paint_ponto_ext))
        shapes.append(cv.Circle(x=x, y=y, radius=2.5, paint=paint_ponto_int))

    labels_datas = [
        ft.Text(str(p["data"]), size=10, color=TEXT_MUTED)
        for p in pontos_recentes
    ]

    return ft.Container(
        bgcolor=DARK_BG,
        border=ft.Border.all(1, SURFACE_BORDER),
        border_radius=10,
        padding=12,
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            f"Topo: {max(valores_1rm):.1f} kg (1RM)",
                            size=11,
                            color=ORCELA_BLUE,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            f"Base: {min(valores_carga):.1f} kg",
                            size=11,
                            color=TEXT_MUTED,
                        ),
                    ],
                ),
                cv.Canvas(width=largura, height=altura, shapes=shapes),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    if len(labels_datas) > 1
                    else ft.MainAxisAlignment.CENTER,
                    controls=labels_datas,
                ),
            ],
        ),
    )


def _construir_grafico_linha_peso(
    historico_peso: list[dict[str, Any]],
) -> ft.Control:
    """Renderiza a curva de evolução do peso corporal em Azul Orcela e Branco."""
    if not historico_peso:
        return ft.Container(
            bgcolor=DARK_BG,
            border=ft.Border.all(1, SURFACE_BORDER),
            border_radius=10,
            padding=14,
            content=ft.Text(
                "Sem registros de pesagem.",
                size=12,
                color=TEXT_MUTED,
            ),
        )

    pontos = historico_peso[-8:]
    pesos = [float(p["peso_kg"]) for p in pontos]
    min_p = min(pesos) - 1.5
    max_p = max(pesos) + 1.5
    if max_p <= min_p:
        max_p = min_p + 2.0

    largura = 310.0
    altura = 115.0
    pad_x = 24.0
    pad_y = 16.0
    area_w = largura - (2 * pad_x)
    area_h = altura - (2 * pad_y)

    shapes: list[cv.Shape] = []
    paint_grid = ft.Paint(color=SURFACE_BORDER, stroke_width=1)
    for i in range(3):
        yg = pad_y + (area_h * i / 2.0)
        shapes.append(
            cv.Line(x1=pad_x, y1=yg, x2=largura - pad_x, y2=yg, paint=paint_grid)
        )

    n = len(pontos)
    coords: list[tuple[float, float]] = []
    for idx, p in enumerate(pontos):
        x = (
            pad_x + (area_w / 2.0)
            if n == 1
            else pad_x + (idx * area_w / float(n - 1))
        )
        ratio = (float(p["peso_kg"]) - min_p) / (max_p - min_p)
        y = (pad_y + area_h) - (ratio * area_h)
        coords.append((x, y))

    paint_linha = ft.Paint(color=ORCELA_BLUE, stroke_width=3)
    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        shapes.append(cv.Line(x1=x1, y1=y1, x2=x2, y2=y2, paint=paint_linha))

    paint_ext = ft.Paint(color=ORCELA_BLUE)
    paint_int = ft.Paint(color=PURE_WHITE)
    for x, y in coords:
        shapes.append(cv.Circle(x=x, y=y, radius=5, paint=paint_ext))
        shapes.append(cv.Circle(x=x, y=y, radius=2.5, paint=paint_int))

    labels = [
        ft.Text(f"{p['data']} ({p['peso_kg']:g}kg)", size=10, color=TEXT_MUTED)
        for p in pontos
    ]

    return ft.Container(
        bgcolor=DARK_BG,
        border=ft.Border.all(1, SURFACE_BORDER),
        border_radius=10,
        padding=12,
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            "Curva de Peso Corporal",
                            size=11,
                            color=ORCELA_BLUE,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            f"Faixa: {min(pesos):.1f} - {max(pesos):.1f} kg",
                            size=11,
                            color=TEXT_MUTED,
                        ),
                    ],
                ),
                cv.Canvas(width=largura, height=altura, shapes=shapes),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    if len(labels) > 1
                    else ft.MainAxisAlignment.CENTER,
                    controls=labels,
                ),
            ],
        ),
    )


def build_stats_view(page: ft.Page) -> ft.Control:
    """Constrói a view modular da aba Evolução com KPIs, Biometria, Curva 1RM e Volume."""
    exercicio_selecionado_id: int | None = None
    form_biometria_visivel: bool = False

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

    dd_seletor_exercicio = ft.Dropdown(
        label="Analisar Exercício",
        border=construir_borda_input(),
        color=PURE_WHITE,
        expand=True,
    )

    tf_bio_peso = ft.TextField(
        label="Peso (kg)",
        value="77.6",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_bio_altura = ft.TextField(
        label="Altura (cm)",
        value="190",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_bio_bf = ft.TextField(
        label="% Gordura (opc)",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_bio_cintura = ft.TextField(
        label="Cintura cm",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_bio_braco = ft.TextField(
        label="Braço cm",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )

    def alternar_form_biometria(bio_atual: dict[str, Any]) -> None:
        nonlocal form_biometria_visivel
        form_biometria_visivel = not form_biometria_visivel
        if form_biometria_visivel:
            tf_bio_peso.value = f"{bio_atual['peso_atual_kg']:g}"
            tf_bio_altura.value = f"{bio_atual['altura_cm']:g}"
            tf_bio_bf.value = (
                f"{bio_atual['percentual_gordura']:g}"
                if bio_atual["percentual_gordura"] is not None
                else ""
            )
            tf_bio_cintura.value = (
                f"{bio_atual['cintura_cm']:g}"
                if bio_atual["cintura_cm"] is not None
                else ""
            )
            tf_bio_braco.value = (
                f"{bio_atual['braco_cm']:g}"
                if bio_atual["braco_cm"] is not None
                else ""
            )
        renderizar(atualizar_pagina=True)

    def salvar_nova_biometria(_: Any = None) -> None:
        nonlocal form_biometria_visivel
        try:
            peso_v = float((tf_bio_peso.value or "77.6").replace(",", "."))
            alt_v = float((tf_bio_altura.value or "190").replace(",", "."))
            bf_v = (
                float(tf_bio_bf.value.replace(",", "."))
                if (tf_bio_bf.value and tf_bio_bf.value.strip())
                else None
            )
            cint_v = (
                float(tf_bio_cintura.value.replace(",", "."))
                if (tf_bio_cintura.value and tf_bio_cintura.value.strip())
                else None
            )
            braco_v = (
                float(tf_bio_braco.value.replace(",", "."))
                if (tf_bio_braco.value and tf_bio_braco.value.strip())
                else None
            )
            registrar_biometria(
                peso_kg=peso_v,
                altura_cm=alt_v,
                percentual_gordura=bf_v,
                cintura_cm=cint_v,
                braco_cm=braco_v,
            )
            form_biometria_visivel = False
            notificar("Biometria e medidas registradas com sucesso!")
            renderizar(atualizar_pagina=True)
        except Exception as exc:
            notificar(str(exc), erro=True)

    def construir_card_kpi(
        titulo: str, valor: str, subtitulo: str, icone: ft.IconData
    ) -> ft.Container:
        return ft.Container(
            expand=True,
            bgcolor=CARD_BG,
            border=ft.Border.all(1, SURFACE_BORDER),
            border_radius=12,
            padding=12,
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Icon(icone, color=ORCELA_BLUE, size=20),
                    ft.Text(
                        valor,
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=PURE_WHITE,
                    ),
                    ft.Text(titulo, size=11, color=TEXT_MUTED),
                    ft.Text(subtitulo, size=10, color=ORCELA_BLUE),
                ],
            ),
        )

    def ao_mudar_exercicio(_: Any = None) -> None:
        nonlocal exercicio_selecionado_id
        if dd_seletor_exercicio.value:
            exercicio_selecionado_id = int(dd_seletor_exercicio.value)
        renderizar(atualizar_pagina=True)

    dd_seletor_exercicio.on_select = ao_mudar_exercicio

    def renderizar(atualizar_pagina: bool = True) -> None:
        nonlocal exercicio_selecionado_id
        metricas = obter_metricas_gerais()
        biometria = obter_historico_biometria()
        exercicios = listar_exercicios_para_analise()

        dd_seletor_exercicio.options = [
            ft.dropdown.Option(
                key=str(ex.id), text=f"{ex.nome} • {ex.grupo_muscular}"
            )
            for ex in exercicios
        ]

        if exercicios and exercicio_selecionado_id is None:
            exercicio_selecionado_id = exercicios[0].id
            dd_seletor_exercicio.value = str(exercicio_selecionado_id)
        elif exercicio_selecionado_id is not None:
            dd_seletor_exercicio.value = str(exercicio_selecionado_id)

        historico_ex = (
            obter_evolucao_exercicio(exercicio_selecionado_id)
            if exercicio_selecionado_id is not None
            else []
        )

        pr_carga = max(
            (float(h["carga_maxima_kg"]) for h in historico_ex), default=0.0
        )
        melhor_1rm = max(
            (float(h["one_rm_estimado"]) for h in historico_ex), default=0.0
        )

        tonelagem_fmt = (
            f"{metricas['tonelagem_total_kg'] / 1000.0:.1f} t"
            if metricas["tonelagem_total_kg"] >= 1000.0
            else f"{metricas['tonelagem_total_kg']:.0f} kg"
        )
        peso_fmt = f"{biometria['peso_atual_kg']:.1f} kg"
        var_peso = float(biometria["variacao_peso_kg"])
        sinal_var = "+" if var_peso > 0 else ""

        partes_medidas: list[str] = []
        if biometria["percentual_gordura"] is not None:
            partes_medidas.append(f"BF {biometria['percentual_gordura']:g}%")
        if biometria["braco_cm"] is not None:
            partes_medidas.append(f"Braço {biometria['braco_cm']:g}cm")
        if biometria["cintura_cm"] is not None:
            partes_medidas.append(f"Cint. {biometria['cintura_cm']:g}cm")
        resumo_medidas = (
            " • ".join(partes_medidas)
            if partes_medidas
            else f"{biometria['altura_cm']:.0f} cm altura"
        )

        volumes_grupo = obter_volume_por_grupo_muscular(dias=30)
        maior_volume_grupo = max(volumes_grupo.values(), default=0.0)

        barras_grupos: list[ft.Control] = []
        for grupo in GRUPOS_MUSCULARES:
            vol_grupo = volumes_grupo.get(grupo, 0.0)
            proporcao = (
                (vol_grupo / maior_volume_grupo)
                if maior_volume_grupo > 0
                else 0.0
            )
            barras_grupos.append(
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    grupo,
                                    size=12,
                                    color=PURE_WHITE,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Text(
                                    f"{vol_grupo:.0f} kg",
                                    size=12,
                                    color=ORCELA_BLUE,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                        ),
                        ft.ProgressBar(
                            value=proporcao,
                            color=ORCELA_BLUE,
                            bgcolor=SURFACE_BORDER,
                            height=7,
                        ),
                    ],
                )
            )

        controles_biometria: list[ft.Control] = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Text(
                        "BIOMETRIA & COMPOSIÇÃO CORPORAL",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_MUTED,
                        expand=True,
                    ),
                    ft.OutlinedButton(
                        content="Pesagem",
                        icon=ft.Icons.ADD_ROUNDED,
                        style=ft.ButtonStyle(
                            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                        ),
                        on_click=lambda _: alternar_form_biometria(biometria),
                    ),
                ],
            )
        ]

        if form_biometria_visivel:
            controles_biometria.append(
                ft.Container(
                    bgcolor=DARK_BG,
                    border=ft.Border.all(1, ORCELA_BLUE),
                    border_radius=12,
                    padding=12,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        "Nova Pesagem & Medidas",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=PURE_WHITE,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.CLOSE_ROUNDED,
                                        icon_color=TEXT_MUTED,
                                        on_click=lambda _: alternar_form_biometria(
                                            biometria
                                        ),
                                    ),
                                ],
                            ),
                            ft.Row(spacing=8, controls=[tf_bio_peso, tf_bio_altura]),
                            ft.Row(
                                spacing=8,
                                controls=[tf_bio_bf, tf_bio_cintura, tf_bio_braco],
                            ),
                            ft.Button(
                                content="SALVAR BIOMETRIA",
                                icon=ft.Icons.CHECK_ROUNDED,
                                bgcolor=ORCELA_BLUE,
                                color=PURE_WHITE,
                                width=float("inf"),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                                on_click=salvar_nova_biometria,
                            ),
                        ],
                    ),
                )
            )

        controles_biometria.extend(
            [
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Container(
                            expand=True,
                            bgcolor=ORCELA_DARK_SURFACE,
                            border_radius=10,
                            padding=10,
                            content=ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        "IMC Atual",
                                        size=11,
                                        color=TEXT_MUTED,
                                    ),
                                    ft.Text(
                                        f"{biometria['imc']:.1f}",
                                        size=17,
                                        weight=ft.FontWeight.BOLD,
                                        color=PURE_WHITE,
                                    ),
                                    ft.Text(
                                        str(biometria["classificacao_imc"]),
                                        size=10,
                                        color=ORCELA_BLUE,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            bgcolor=ORCELA_DARK_SURFACE,
                            border_radius=10,
                            padding=10,
                            content=ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        "TMB Estimada",
                                        size=11,
                                        color=TEXT_MUTED,
                                    ),
                                    ft.Text(
                                        f"{biometria['tmb_kcal']} kcal",
                                        size=17,
                                        weight=ft.FontWeight.BOLD,
                                        color=PURE_WHITE,
                                    ),
                                    ft.Text(
                                        "Mifflin-St Jeor",
                                        size=10,
                                        color=ORCELA_BLUE,
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Container(
                            expand=True,
                            bgcolor=DARK_BG,
                            border=ft.Border.all(1, SURFACE_BORDER),
                            border_radius=10,
                            padding=10,
                            content=ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        "Força Relativa",
                                        size=11,
                                        color=TEXT_MUTED,
                                    ),
                                    ft.Text(
                                        f"{biometria['forca_relativa']:.2f}x BW",
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color=ORCELA_BLUE,
                                    ),
                                    ft.Text(
                                        "Supino/Agach. ÷ Peso",
                                        size=10,
                                        color=TEXT_MUTED,
                                    ),
                                ],
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            bgcolor=DARK_BG,
                            border=ft.Border.all(1, SURFACE_BORDER),
                            border_radius=10,
                            padding=10,
                            content=ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        "Composição / Medidas",
                                        size=11,
                                        color=TEXT_MUTED,
                                    ),
                                    ft.Text(
                                        resumo_medidas,
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color=PURE_WHITE,
                                    ),
                                    ft.Text(
                                        f"Variação: {sinal_var}{var_peso:.1f} kg",
                                        size=10,
                                        color=ORCELA_BLUE,
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
                _construir_grafico_linha_peso(biometria["historico"]),
            ]
        )

        container_raiz.controls = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            construir_logo_p4(),
                            ft.Text(
                                "Analytics, Biometria & Progressão",
                                size=12,
                                color=TEXT_MUTED,
                            ),
                        ],
                    ),
                    ft.Icon(
                        ft.Icons.SHOW_CHART_ROUNDED,
                        color=ORCELA_BLUE,
                        size=28,
                    ),
                ],
            ),
            ft.Row(
                spacing=8,
                controls=[
                    construir_card_kpi(
                        "Tonelagem",
                        tonelagem_fmt,
                        f"{metricas['total_series_validas']} séries W/F",
                        ft.Icons.FITNESS_CENTER_ROUNDED,
                    ),
                    construir_card_kpi(
                        "Treinos",
                        str(metricas["total_sessoes"]),
                        "Finalizados",
                        ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                    ),
                    construir_card_kpi(
                        "Peso Atual",
                        peso_fmt,
                        f"IMC {biometria['imc']:.1f}",
                        ft.Icons.MONITOR_WEIGHT_OUTLINED,
                    ),
                ],
            ),
            ft.Container(
                bgcolor=CARD_BG,
                border=ft.Border.all(1, SURFACE_BORDER),
                border_radius=14,
                padding=16,
                content=ft.Column(spacing=12, controls=controles_biometria),
            ),
            ft.Container(
                bgcolor=CARD_BG,
                border=ft.Border.all(1, SURFACE_BORDER),
                border_radius=14,
                padding=16,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Text(
                            "PROGRESSÃO POR EXERCÍCIO",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=TEXT_MUTED,
                        ),
                        ft.Row(controls=[dd_seletor_exercicio]),
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Container(
                                    expand=True,
                                    bgcolor=ORCELA_DARK_SURFACE,
                                    border_radius=10,
                                    padding=12,
                                    content=ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text(
                                                "PR de Carga",
                                                size=11,
                                                color=TEXT_MUTED,
                                            ),
                                            ft.Text(
                                                f"{pr_carga:.1f} kg",
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                                color=PURE_WHITE,
                                            ),
                                        ],
                                    ),
                                ),
                                ft.Container(
                                    expand=True,
                                    bgcolor=ORCELA_DARK_SURFACE,
                                    border_radius=10,
                                    padding=12,
                                    content=ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text(
                                                "Melhor 1RM (Epley)",
                                                size=11,
                                                color=TEXT_MUTED,
                                            ),
                                            ft.Text(
                                                f"{melhor_1rm:.1f} kg",
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                                color=ORCELA_BLUE,
                                            ),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                        _construir_grafico_linha_evolucao(historico_ex),
                    ],
                ),
            ),
            ft.Container(
                bgcolor=CARD_BG,
                border=ft.Border.all(1, SURFACE_BORDER),
                border_radius=14,
                padding=16,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    "VOLUME POR GRUPO MUSCULAR",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=TEXT_MUTED,
                                ),
                                ft.Text(
                                    "Últimos 30 dias",
                                    size=11,
                                    color=ORCELA_BLUE,
                                ),
                            ],
                        ),
                        *barras_grupos,
                    ],
                ),
            ),
        ]

        if atualizar_pagina:
            page.update()

    renderizar(atualizar_pagina=False)
    return container_raiz
