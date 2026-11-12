import threading
import time
from typing import Any

import flet as ft

from models.workout_models import Ficha
from services.workout_service import (
    finalizar_sessao,
    iniciar_sessao,
    listar_fichas,
    obter_ficha_por_id,
    obter_metricas_resumo,
    obter_ultima_execucao_exercicio,
    registrar_serie,
)
from views.routines_view import (
    CARD_BG,
    DANGER_RED,
    DARK_BG,
    ORCELA_BLUE,
    ORCELA_DARK_SURFACE,
    PURE_WHITE,
    SURFACE_BORDER,
    TEXT_MUTED,
    construir_borda_input,
    construir_logo_p4,
)

TIPOS_SERIE = [
    ("W", "W • Trabalho"),
    ("A", "A • Aquec."),
    ("D", "D • Dropset"),
    ("F", "F • Falha"),
]


def _extrair_reps_padrao(reps_alvo: str) -> int:
    """Extrai o primeiro número inteiro da faixa de repetições alvo (ex: '8-12' -> 8)."""
    partes = reps_alvo.replace(" ", "").split("-")
    for parte in partes:
        if parte.isdigit():
            return int(parte)
    return 10


def build_train_view(page: ft.Page) -> ft.Control:
    """Constrói a view modular de Execução de Treino e Resumo Principal."""
    sessao_ativa_id: int | None = None
    ficha_ativa: Ficha | None = None
    series_concluidas: set[tuple[int, int]] = set()
    timer_segundos_restantes: int = 0
    timer_rodando: bool = False
    timer_token: int = 0

    container_raiz = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=16,
    )

    txt_cronometro = ft.Text(
        "Descanso: Pronto",
        size=14,
        weight=ft.FontWeight.BOLD,
        color=PURE_WHITE,
    )
    barra_progresso_timer = ft.ProgressBar(
        value=0.0,
        color=ORCELA_BLUE,
        bgcolor=SURFACE_BORDER,
        height=6,
    )

    tf_notas_sessao = ft.TextField(
        label="Notas do treino (opcional)",
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
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

    def disparar_cronometro(segundos_totais: int) -> None:
        nonlocal timer_segundos_restantes, timer_rodando, timer_token
        timer_token += 1
        meu_token = timer_token
        timer_segundos_restantes = max(1, segundos_totais)
        timer_rodando = True

        def _loop_regressivo() -> None:
            nonlocal timer_segundos_restantes, timer_rodando
            total = float(max(1, segundos_totais))
            while timer_segundos_restantes > 0 and timer_token == meu_token:
                mins, segs = divmod(timer_segundos_restantes, 60)
                txt_cronometro.value = f"Descanso Ativo: {mins:02d}:{segs:02d}"
                txt_cronometro.color = ORCELA_BLUE
                barra_progresso_timer.value = timer_segundos_restantes / total
                try:
                    page.update()
                except Exception:
                    break
                time.sleep(1)
                timer_segundos_restantes -= 1

            if timer_token == meu_token:
                timer_rodando = False
                txt_cronometro.value = "Descanso finalizado! Próxima série!"
                txt_cronometro.color = PURE_WHITE
                barra_progresso_timer.value = 0.0
                try:
                    page.update()
                except Exception:
                    pass

        threading.Thread(target=_loop_regressivo, daemon=True).start()

    def parar_cronometro(atualizar_pagina: bool = True) -> None:
        nonlocal timer_token, timer_rodando, timer_segundos_restantes
        timer_token += 1
        timer_rodando = False
        timer_segundos_restantes = 0
        txt_cronometro.value = "Descanso: Pronto"
        txt_cronometro.color = PURE_WHITE
        barra_progresso_timer.value = 0.0
        if atualizar_pagina:
            page.update()

    def construir_card_metrica(
        titulo: str, valor: str, icone: ft.IconData
    ) -> ft.Container:
        return ft.Container(
            expand=True,
            bgcolor=CARD_BG,
            border=ft.Border.all(1, SURFACE_BORDER),
            border_radius=12,
            padding=14,
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Icon(icone, color=ORCELA_BLUE, size=22),
                    ft.Text(
                        valor,
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=PURE_WHITE,
                    ),
                    ft.Text(titulo, size=12, color=TEXT_MUTED),
                ],
            ),
        )

    def comecar_treino(ficha_id: int) -> None:
        nonlocal sessao_ativa_id, ficha_ativa
        ficha_carregada = obter_ficha_por_id(ficha_id)
        if ficha_carregada is None:
            notificar("Ficha não encontrada.", erro=True)
            return

        sessao = iniciar_sessao(ficha_id=ficha_id)
        sessao_ativa_id = sessao.id
        ficha_ativa = ficha_carregada
        series_concluidas.clear()
        tf_notas_sessao.value = ""
        parar_cronometro()
        renderizar()

    def concluir_treino_ativo(_: Any = None) -> None:
        nonlocal sessao_ativa_id, ficha_ativa
        if sessao_ativa_id is None:
            return
        parar_cronometro()
        finalizar_sessao(sessao_id=sessao_ativa_id, notas=tf_notas_sessao.value)
        total_series = len(series_concluidas)
        sessao_ativa_id = None
        ficha_ativa = None
        series_concluidas.clear()
        notificar(f"Treino finalizado! {total_series} série(s) registrada(s).")
        renderizar()

    def construir_linha_serie(
        exercicio_id: int,
        numero_serie: int,
        carga_sugerida: float,
        reps_sugeridas: int,
        rir_sugerido: int | None,
        tipo_sugerido: str,
        descanso_segundos: int,
    ) -> ft.Container:
        tf_carga = ft.TextField(
            value=f"{carga_sugerida:g}",
            width=68,
            height=40,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=6),
            keyboard_type=ft.KeyboardType.NUMBER,
            border=construir_borda_input(6.0),
            color=PURE_WHITE,
            text_size=13,
        )
        tf_reps = ft.TextField(
            value=str(reps_sugeridas),
            width=56,
            height=40,
            content_padding=ft.Padding.symmetric(horizontal=8, vertical=6),
            keyboard_type=ft.KeyboardType.NUMBER,
            border=construir_borda_input(6.0),
            color=PURE_WHITE,
            text_size=13,
        )
        tf_rir = ft.TextField(
            value=str(rir_sugerido) if rir_sugerido is not None else "2",
            width=48,
            height=40,
            content_padding=ft.Padding.symmetric(horizontal=6, vertical=6),
            keyboard_type=ft.KeyboardType.NUMBER,
            border=construir_borda_input(6.0),
            color=PURE_WHITE,
            text_size=13,
        )
        dd_tipo = ft.Dropdown(
            value=tipo_sugerido if tipo_sugerido in {"W", "A", "D", "F"} else "W",
            width=74,
            border=construir_borda_input(6.0),
            color=PURE_WHITE,
            text_size=12,
            options=[
                ft.dropdown.Option(key=cod, text=cod) for cod, _ in TIPOS_SERIE
            ],
        )

        chave_serie = (exercicio_id, numero_serie)
        ja_concluida = chave_serie in series_concluidas

        btn_check = ft.IconButton(
            icon=ft.Icons.CHECK_CIRCLE_ROUNDED
            if ja_concluida
            else ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
            icon_color=ORCELA_BLUE if ja_concluida else TEXT_MUTED,
            tooltip="Registrar Série",
        )

        linha_container = ft.Container(
            bgcolor=ORCELA_DARK_SURFACE if ja_concluida else DARK_BG,
            border=ft.Border.all(
                1, ORCELA_BLUE if ja_concluida else SURFACE_BORDER
            ),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=8, vertical=6),
        )

        def ao_confirmar_serie(_: Any) -> None:
            if sessao_ativa_id is None:
                return
            try:
                carga_val = float((tf_carga.value or "0").replace(",", "."))
                reps_val = int(tf_reps.value or "0")
                rir_val = (
                    int(tf_rir.value)
                    if (tf_rir.value and tf_rir.value.strip().isdigit())
                    else None
                )
            except ValueError:
                notificar("Verifique os valores numéricos de carga e reps.", erro=True)
                return

            registrar_serie(
                sessao_id=sessao_ativa_id,
                exercicio_id=exercicio_id,
                numero_serie=numero_serie,
                carga_kg=carga_val,
                repeticoes=reps_val,
                rir=rir_val,
                tipo_serie=dd_tipo.value or "W",
            )
            series_concluidas.add(chave_serie)
            btn_check.icon = ft.Icons.CHECK_CIRCLE_ROUNDED
            btn_check.icon_color = ORCELA_BLUE
            linha_container.bgcolor = ORCELA_DARK_SURFACE
            linha_container.border = ft.Border.all(1, ORCELA_BLUE)
            disparar_cronometro(descanso_segundos)
            page.update()

        btn_check.on_click = ao_confirmar_serie

        linha_container.content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
            controls=[
                ft.Text(
                    f"#{numero_serie}",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=ORCELA_BLUE,
                    width=24,
                ),
                dd_tipo,
                tf_carga,
                tf_reps,
                tf_rir,
                btn_check,
            ],
        )
        return linha_container

    def renderizar_modo_treino_ativo() -> list[ft.Control]:
        assert ficha_ativa is not None
        blocos_exercicios: list[ft.Control] = []

        for item in ficha_ativa.itens:
            historico = obter_ultima_execucao_exercicio(item.exercicio_id)
            reps_padrao = _extrair_reps_padrao(item.reps_alvo)

            txt_historico = (
                f"Auto-fill: última sessão ({len(historico)} séries)"
                if historico
                else "Auto-fill: 1ª vez neste exercício"
            )

            linhas_series: list[ft.Control] = [
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Série", size=11, color=TEXT_MUTED, width=28),
                        ft.Text("Tipo", size=11, color=TEXT_MUTED, width=68),
                        ft.Text("Carga (kg)", size=11, color=TEXT_MUTED, width=68),
                        ft.Text("Reps", size=11, color=TEXT_MUTED, width=52),
                        ft.Text("RIR", size=11, color=TEXT_MUTED, width=44),
                        ft.Text("OK", size=11, color=TEXT_MUTED, width=32),
                    ],
                )
            ]

            for num_s in range(1, item.series_alvo + 1):
                serie_ant = (
                    historico[num_s - 1]
                    if num_s - 1 < len(historico)
                    else (historico[-1] if historico else None)
                )
                carga_sug = serie_ant.carga_kg if serie_ant else 20.0
                reps_sug = serie_ant.repeticoes if serie_ant else reps_padrao
                rir_sug = serie_ant.rir if (serie_ant and serie_ant.rir is not None) else 2
                tipo_sug = serie_ant.tipo_serie if serie_ant else "W"

                linhas_series.append(
                    construir_linha_serie(
                        exercicio_id=item.exercicio_id,
                        numero_serie=num_s,
                        carga_sugerida=carga_sug,
                        reps_sugeridas=reps_sug,
                        rir_sugerido=rir_sug,
                        tipo_sugerido=tipo_sug,
                        descanso_segundos=item.descanso_segundos,
                    )
                )

            blocos_exercicios.append(
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, SURFACE_BORDER),
                    border_radius=14,
                    padding=14,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Column(
                                        spacing=2,
                                        expand=True,
                                        controls=[
                                            ft.Text(
                                                f"{item.ordem}. {item.exercicio.nome}",
                                                size=15,
                                                weight=ft.FontWeight.BOLD,
                                                color=PURE_WHITE,
                                            ),
                                            ft.Text(
                                                txt_historico,
                                                size=11,
                                                color=ORCELA_BLUE,
                                            ),
                                        ],
                                    ),
                                    ft.Container(
                                        bgcolor=ORCELA_DARK_SURFACE,
                                        padding=ft.Padding.symmetric(
                                            horizontal=8, vertical=4
                                        ),
                                        border_radius=6,
                                        content=ft.Text(
                                            f"{item.series_alvo}x {item.reps_alvo}",
                                            size=11,
                                            color=PURE_WHITE,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ),
                                ],
                            ),
                            ft.Divider(height=1, color=SURFACE_BORDER),
                            ft.Column(spacing=6, controls=linhas_series),
                        ],
                    ),
                )
            )

        return [
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
                                f"Sessão Ativa • {ficha_ativa.nome}",
                                size=12,
                                color=ORCELA_BLUE,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                    ),
                    ft.Container(
                        bgcolor=ORCELA_DARK_SURFACE,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                        border_radius=8,
                        content=ft.Text(
                            "EM TREINO",
                            size=11,
                            color=PURE_WHITE,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ),
                ],
            ),
            ft.Container(
                bgcolor=CARD_BG,
                border=ft.Border.all(1, ORCELA_BLUE),
                border_radius=12,
                padding=12,
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.TIMER_ROUNDED,
                                            color=ORCELA_BLUE,
                                            size=20,
                                        ),
                                        txt_cronometro,
                                    ],
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.STOP_CIRCLE_OUTLINED,
                                    icon_color=TEXT_MUTED,
                                    tooltip="Zerar descanso",
                                    on_click=parar_cronometro,
                                ),
                            ],
                        ),
                        barra_progresso_timer,
                    ],
                ),
            ),
            *blocos_exercicios,
            tf_notas_sessao,
            ft.Button(
                content="FINALIZAR TREINO",
                icon=ft.Icons.CHECK_CIRCLE_ROUNDED,
                bgcolor=ORCELA_BLUE,
                color=PURE_WHITE,
                width=float("inf"),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
                on_click=concluir_treino_ativo,
            ),
        ]

    def renderizar_modo_resumo() -> list[ft.Control]:
        metricas = obter_metricas_resumo()
        fichas_ativas = listar_fichas(apenas_ativas=True)

        cards_fichas: list[ft.Control] = []
        for ficha in fichas_ativas:
            itens_preview = [
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            f"{item.ordem}. {item.exercicio.nome}",
                            size=13,
                            color=PURE_WHITE,
                            weight=ft.FontWeight.W_500,
                            expand=True,
                        ),
                        ft.Text(
                            f"{item.series_alvo}x {item.reps_alvo} ({item.descanso_segundos}s)",
                            size=12,
                            color=ORCELA_BLUE,
                        ),
                    ],
                )
                for item in ficha.itens
            ]

            cards_fichas.append(
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
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=8,
                                controls=[
                                    ft.Text(
                                        ficha.nome,
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=PURE_WHITE,
                                        expand=True,
                                    ),
                                    ft.Container(
                                        bgcolor=ORCELA_DARK_SURFACE,
                                        padding=ft.Padding.symmetric(
                                            horizontal=8, vertical=4
                                        ),
                                        border_radius=6,
                                        content=ft.Text(
                                            f"{len(ficha.itens)} exercícios",
                                            size=11,
                                            color=ORCELA_BLUE,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ),
                                ],
                            ),
                            ft.Text(
                                ficha.descricao or "Sem descrição",
                                size=12,
                                color=TEXT_MUTED,
                            ),
                            ft.Divider(height=1, color=SURFACE_BORDER),
                            ft.Column(spacing=6, controls=itens_preview),
                            ft.Container(height=4),
                            ft.Button(
                                content="INICIAR SESSÃO",
                                icon=ft.Icons.PLAY_ARROW_ROUNDED,
                                bgcolor=ORCELA_BLUE,
                                color=PURE_WHITE,
                                width=float("inf"),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                                on_click=lambda _, fid=ficha.id: comecar_treino(fid),
                            ),
                        ],
                    ),
                )
            )

        return [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        spacing=2,
                        controls=[
                            construir_logo_p4(),
                            ft.Text(
                                "SQLite Offline-First Ativo",
                                size=12,
                                color=TEXT_MUTED,
                            ),
                        ],
                    ),
                    ft.Icon(ft.Icons.BOLT_ROUNDED, color=ORCELA_BLUE, size=28),
                ],
            ),
            ft.Row(
                spacing=10,
                controls=[
                    construir_card_metrica(
                        "Fichas Ativas",
                        str(metricas["total_fichas"]),
                        ft.Icons.LIST_ALT_ROUNDED,
                    ),
                    construir_card_metrica(
                        "Exercícios",
                        str(metricas["total_exercicios"]),
                        ft.Icons.FITNESS_CENTER_ROUNDED,
                    ),
                    construir_card_metrica(
                        "Sessões",
                        str(metricas["total_sessoes"]),
                        ft.Icons.HISTORY_ROUNDED,
                    ),
                ],
            ),
            ft.Text(
                "PRONTO PARA TREINAR",
                size=13,
                weight=ft.FontWeight.BOLD,
                color=TEXT_MUTED,
            ),
            *cards_fichas,
        ]

    def renderizar(atualizar_pagina: bool = True) -> None:
        if sessao_ativa_id is not None and ficha_ativa is not None:
            container_raiz.controls = renderizar_modo_treino_ativo()
        else:
            container_raiz.controls = renderizar_modo_resumo()
        if atualizar_pagina:
            page.update()

    renderizar(atualizar_pagina=False)
    return container_raiz
