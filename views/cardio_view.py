import asyncio
from typing import Any

import flet as ft

from services.cardio_service import (
    MODALIDADES_CARDIO,
    calcular_metricas_cardio,
    excluir_sessao_cardio,
    formatar_tempo_segundos,
    listar_sessoes_cardio,
    obter_resumo_cardio,
    registrar_sessao_cardio,
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

ICONES_MODALIDADE: dict[str, ft.IconData] = {
    "Corrida Rua": ft.Icons.DIRECTIONS_RUN_ROUNDED,
    "Esteira": ft.Icons.DIRECTIONS_RUN_ROUNDED,
    "Ciclismo": ft.Icons.DIRECTIONS_BIKE_ROUNDED,
    "Escada": ft.Icons.STAIRS_ROUNDED,
    "Elíptico": ft.Icons.FITNESS_CENTER_ROUNDED,
    "Caminhada": ft.Icons.DIRECTIONS_WALK_ROUNDED,
    "HIIT": ft.Icons.BOLT_ROUNDED,
}


def build_cardio_view(page: ft.Page) -> ft.Control:
    """Constrói a view modular dedicada de Cardio & Corrida."""
    cronometro_segundos: int = 0
    cronometro_rodando: bool = False
    cronometro_token: int = 0
    aguardando_finalizacao_ao_vivo: bool = False
    form_manual_visivel: bool = False

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

    txt_display_cronometro = ft.Text(
        "00:00",
        size=34,
        weight=ft.FontWeight.W_900,
        color=PURE_WHITE,
    )
    txt_preview_vivo = ft.Text(
        "Pronto para iniciar",
        size=12,
        color=TEXT_MUTED,
    )

    dd_modalidade_vivo = ft.Dropdown(
        label="Modalidade ao Vivo",
        value="Corrida Rua",
        border=construir_borda_input(),
        color=PURE_WHITE,
        expand=True,
        options=[
            ft.dropdown.Option(key=m, text=m) for m in MODALIDADES_CARDIO
        ],
    )
    tf_dist_vivo = ft.TextField(
        label="Distância Percorrida (km)",
        value="5.0",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_fc_vivo = ft.TextField(
        label="FC Média (bpm)",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        width=125,
    )
    tf_rpe_vivo = ft.TextField(
        label="RPE (1-10)",
        value="7",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        width=95,
    )

    dd_modalidade_manual = ft.Dropdown(
        label="Modalidade",
        value="Corrida Rua",
        border=construir_borda_input(),
        color=PURE_WHITE,
        expand=True,
        options=[
            ft.dropdown.Option(key=m, text=m) for m in MODALIDADES_CARDIO
        ],
    )
    tf_tempo_min_manual = ft.TextField(
        label="Tempo (min)",
        value="30",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_dist_manual = ft.TextField(
        label="Distância (km)",
        value="5.0",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_fc_manual = ft.TextField(
        label="FC Média (opc)",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_rpe_manual = ft.TextField(
        label="RPE (1-10)",
        value="8",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        width=100,
    )

    async def _loop_cronometro_async(meu_token: int) -> None:
        nonlocal cronometro_segundos
        while cronometro_rodando and cronometro_token == meu_token:
            await asyncio.sleep(1)
            if not cronometro_rodando or cronometro_token != meu_token:
                break
            cronometro_segundos += 1
            txt_display_cronometro.value = formatar_tempo_segundos(
                cronometro_segundos
            )
            txt_display_cronometro.color = ORCELA_BLUE
            try:
                page.update()
            except Exception:
                break

    def alternar_iniciar_pausar(_: Any = None) -> None:
        nonlocal cronometro_rodando, cronometro_token
        cronometro_rodando = not cronometro_rodando
        cronometro_token += 1
        if cronometro_rodando:
            txt_preview_vivo.value = (
                f"Em andamento • {dd_modalidade_vivo.value or 'Corrida Rua'}"
            )
            txt_preview_vivo.color = ORCELA_BLUE
            if hasattr(page, "run_task"):
                page.run_task(_loop_cronometro_async, cronometro_token)
        else:
            txt_preview_vivo.value = "Cronômetro pausado"
            txt_preview_vivo.color = TEXT_MUTED
        renderizar(atualizar_pagina=True)

    def zerar_cronometro(_: Any = None) -> None:
        nonlocal cronometro_rodando, cronometro_segundos, cronometro_token, aguardando_finalizacao_ao_vivo
        cronometro_token += 1
        cronometro_rodando = False
        cronometro_segundos = 0
        aguardando_finalizacao_ao_vivo = False
        txt_display_cronometro.value = "00:00"
        txt_display_cronometro.color = PURE_WHITE
        txt_preview_vivo.value = "Pronto para iniciar"
        txt_preview_vivo.color = TEXT_MUTED
        renderizar(atualizar_pagina=True)

    def abrir_finalizacao_vivo(_: Any = None) -> None:
        nonlocal cronometro_rodando, cronometro_token, aguardando_finalizacao_ao_vivo
        cronometro_token += 1
        cronometro_rodando = False
        if cronometro_segundos <= 0:
            cronometro_segundos_estimado = 60
        else:
            cronometro_segundos_estimado = cronometro_segundos
        aguardando_finalizacao_ao_vivo = True
        try:
            dist_v = float((tf_dist_vivo.value or "0").replace(",", "."))
        except ValueError:
            dist_v = 0.0
        prev = calcular_metricas_cardio(
            dd_modalidade_vivo.value or "Corrida Rua",
            cronometro_segundos_estimado,
            dist_v,
        )
        pace_txt = prev["pace_medio_str"] or "-- /km"
        txt_preview_vivo.value = (
            f"Prévia: Pace {pace_txt} • ~{prev['calorias_estimadas']} kcal"
        )
        txt_preview_vivo.color = ORCELA_BLUE
        renderizar(atualizar_pagina=True)

    def salvar_cardio_ao_vivo(_: Any = None) -> None:
        nonlocal cronometro_segundos, aguardando_finalizacao_ao_vivo
        duracao_final = max(1, cronometro_segundos)
        try:
            dist_val = float((tf_dist_vivo.value or "0").replace(",", "."))
            fc_val = (
                int(tf_fc_vivo.value)
                if (tf_fc_vivo.value and tf_fc_vivo.value.strip())
                else None
            )
            rpe_val = int(tf_rpe_vivo.value or "7")
            sessao = registrar_sessao_cardio(
                modalidade=dd_modalidade_vivo.value or "Corrida Rua",
                duracao_segundos=duracao_final,
                distancia_km=dist_val,
                fc_media=fc_val,
                percepcao_esforco=rpe_val,
            )
            zerar_cronometro()
            notificar(
                f"{sessao.modalidade} salva! Pace: {sessao.pace_medio_str or 'N/A'} ({sessao.calorias_estimadas} kcal)"
            )
        except Exception as exc:
            notificar(str(exc), erro=True)

    def alternar_form_manual(_: Any = None) -> None:
        nonlocal form_manual_visivel
        form_manual_visivel = not form_manual_visivel
        renderizar(atualizar_pagina=True)

    def salvar_cardio_manual(_: Any = None) -> None:
        nonlocal form_manual_visivel
        try:
            minutos = float((tf_tempo_min_manual.value or "0").replace(",", "."))
            duracao_seg = int(round(minutos * 60))
            dist_val = float((tf_dist_manual.value or "0").replace(",", "."))
            fc_val = (
                int(tf_fc_manual.value)
                if (tf_fc_manual.value and tf_fc_manual.value.strip())
                else None
            )
            rpe_val = int(tf_rpe_manual.value or "7")
            sessao = registrar_sessao_cardio(
                modalidade=dd_modalidade_manual.value or "Corrida Rua",
                duracao_segundos=duracao_seg,
                distancia_km=dist_val,
                fc_media=fc_val,
                percepcao_esforco=rpe_val,
            )
            form_manual_visivel = False
            notificar(
                f"Cardio registrado! {sessao.distancia_km:g} km • Pace {sessao.pace_medio_str or 'N/A'}"
            )
            renderizar(atualizar_pagina=True)
        except Exception as exc:
            notificar(str(exc), erro=True)

    def remover_sessao(sessao_id: int) -> None:
        excluir_sessao_cardio(sessao_id)
        notificar("Sessão de cardio removida.")
        renderizar(atualizar_pagina=True)

    def construir_card_kpi(
        titulo: str, valor: str, subtitulo: str, icone: ft.IconData
    ) -> ft.Container:
        return ft.Container(
            expand=True,
            bgcolor=CARD_BG,
            border=ft.Border.all(1, ORCELA_BORDER_GLOW),
            shadow=construir_sombra_orcela(),
            border_radius=12,
            padding=12,
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Icon(icone, color=ORCELA_BLUE, size=20),
                    ft.Text(
                        valor,
                        size=17,
                        weight=ft.FontWeight.BOLD,
                        color=PURE_WHITE,
                    ),
                    ft.Text(titulo, size=11, color=TEXT_MUTED),
                    ft.Text(subtitulo, size=10, color=ORCELA_BLUE),
                ],
            ),
        )

    def renderizar(atualizar_pagina: bool = True) -> None:
        resumo = obter_resumo_cardio(dias=30)
        historico = listar_sessoes_cardio(limite=20)

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
                                "Cardio, Corrida & Condicionamento",
                                size=12,
                                color=TEXT_MUTED,
                            ),
                        ],
                    ),
                    ft.OutlinedButton(
                        content="Registrar Cardio",
                        icon=ft.Icons.ADD_ROUNDED,
                        style=ft.ButtonStyle(
                            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                        ),
                        on_click=alternar_form_manual,
                    ),
                ],
            ),
            ft.Row(
                spacing=8,
                controls=[
                    construir_card_kpi(
                        "Distância (30d)",
                        f"{resumo['distancia_total_km']:.1f} km",
                        f"{resumo['total_sessoes']} sessões",
                        ft.Icons.DIRECTIONS_RUN_ROUNDED,
                    ),
                    construir_card_kpi(
                        "Tempo Total",
                        str(resumo["tempo_total_fmt"]),
                        f"{resumo['calorias_totais']} kcal",
                        ft.Icons.TIMER_OUTLINED,
                    ),
                    construir_card_kpi(
                        "Pace Médio",
                        str(resumo["pace_medio_geral"]),
                        "Ritmo 30d",
                        ft.Icons.SPEED_ROUNDED,
                    ),
                ],
            ),
        ]

        # Formulário Manual Rápido
        if form_manual_visivel:
            controles.append(
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, ORCELA_BORDER_HIGHLIGHT),
                    shadow=construir_sombra_orcela(),
                    border_radius=14,
                    padding=16,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        "Registro Manual de Cardio",
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color=PURE_WHITE,
                                        expand=True,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.CLOSE_ROUNDED,
                                        icon_color=TEXT_MUTED,
                                        on_click=alternar_form_manual,
                                    ),
                                ],
                            ),
                            ft.Row(controls=[dd_modalidade_manual]),
                            ft.Row(
                                spacing=8,
                                controls=[tf_tempo_min_manual, tf_dist_manual],
                            ),
                            ft.Row(
                                spacing=8,
                                controls=[tf_fc_manual, tf_rpe_manual],
                            ),
                            ft.Button(
                                content="SALVAR SESSÃO CARDIO",
                                icon=ft.Icons.CHECK_ROUNDED,
                                bgcolor=ORCELA_BLUE,
                                color=PURE_WHITE,
                                width=float("inf"),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                                on_click=salvar_cardio_manual,
                            ),
                        ],
                    ),
                )
            )

        # Card Cronômetro ao Vivo
        controles_vivo: list[ft.Control] = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        "CRONÔMETRO AO VIVO",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_MUTED,
                        expand=True,
                    ),
                    ft.Icon(
                        ft.Icons.TIMER_ROUNDED,
                        color=ORCELA_BLUE,
                        size=20,
                    ),
                ],
            ),
            ft.Row(controls=[dd_modalidade_vivo]),
            ft.Container(
                bgcolor=DARK_BG,
                border=ft.Border.all(
                    1, ORCELA_BLUE if cronometro_rodando else ORCELA_BORDER_GLOW
                ),
                border_radius=12,
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                txt_display_cronometro,
                                txt_preview_vivo,
                            ],
                        ),
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.IconButton(
                                    icon=(
                                        ft.Icons.PAUSE_CIRCLE_FILLED_ROUNDED
                                        if cronometro_rodando
                                        else ft.Icons.PLAY_CIRCLE_FILL_ROUNDED
                                    ),
                                    icon_color=ORCELA_BLUE,
                                    icon_size=36,
                                    tooltip="Iniciar / Pausar",
                                    on_click=alternar_iniciar_pausar,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.RESTART_ALT_ROUNDED,
                                    icon_color=TEXT_MUTED,
                                    tooltip="Zerar",
                                    on_click=zerar_cronometro,
                                ),
                            ],
                        ),
                    ],
                ),
            ),
        ]

        if aguardando_finalizacao_ao_vivo:
            controles_vivo.extend(
                [
                    ft.Row(
                        spacing=8,
                        controls=[tf_dist_vivo, tf_fc_vivo, tf_rpe_vivo],
                    ),
                    ft.Button(
                        content="CONFIRMAR & SALVAR",
                        icon=ft.Icons.SAVE_ROUNDED,
                        bgcolor=ORCELA_BLUE,
                        color=PURE_WHITE,
                        width=float("inf"),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                        on_click=salvar_cardio_ao_vivo,
                    ),
                ]
            )
        else:
            controles_vivo.append(
                ft.OutlinedButton(
                    content="Finalizar & Salvar",
                    icon=ft.Icons.FLAG_ROUNDED,
                    width=float("inf"),
                    on_click=abrir_finalizacao_vivo,
                )
            )

        controles.append(
            ft.Container(
                bgcolor=CARD_BG,
                border=ft.Border.all(1, ORCELA_BORDER_HIGHLIGHT),
                shadow=construir_sombra_orcela(),
                border_radius=14,
                padding=16,
                content=ft.Column(spacing=12, controls=controles_vivo),
            )
        )

        # Histórico de Sessões
        controles.append(
            ft.Text(
                "HISTÓRICO DE SESSÕES AERÓBICAS",
                size=12,
                weight=ft.FontWeight.BOLD,
                color=TEXT_MUTED,
            )
        )

        if not historico:
            controles.append(
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, ORCELA_BORDER_GLOW),
                    shadow=construir_sombra_orcela(),
                    border_radius=12,
                    padding=18,
                    content=ft.Text(
                        "Nenhuma sessão de cardio registrada ainda. Use o Cronômetro ao Vivo ou 'Registrar Cardio'.",
                        size=12,
                        color=TEXT_MUTED,
                    ),
                )
            )
        else:
            for sessao in historico:
                icone_mod = ICONES_MODALIDADE.get(
                    sessao.modalidade, ft.Icons.DIRECTIONS_RUN_ROUNDED
                )
                tempo_str = formatar_tempo_segundos(sessao.duracao_segundos)
                pace_badge = sessao.pace_medio_str or f"{sessao.velocidade_media_kmh:.1f} km/h"
                detalhes_fc = (
                    f" • {sessao.fc_media} bpm" if sessao.fc_media else ""
                )

                controles.append(
                    ft.Container(
                        bgcolor=CARD_BG,
                        border=ft.Border.all(1, ORCELA_BORDER_GLOW),
                        shadow=construir_sombra_orcela(),
                        border_radius=12,
                        padding=14,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                            controls=[
                                ft.Container(
                                    bgcolor=ORCELA_DARK_SURFACE,
                                    padding=10,
                                    border_radius=10,
                                    content=ft.Icon(
                                        icone_mod,
                                        color=ORCELA_BLUE,
                                        size=22,
                                    ),
                                ),
                                ft.Column(
                                    spacing=3,
                                    expand=True,
                                    controls=[
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                            controls=[
                                                ft.Text(
                                                    sessao.modalidade,
                                                    size=14,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=PURE_WHITE,
                                                    expand=True,
                                                ),
                                                ft.Text(
                                                    sessao.data.strftime("%d/%m %H:%M"),
                                                    size=11,
                                                    color=TEXT_MUTED,
                                                ),
                                            ],
                                        ),
                                        ft.Row(
                                            spacing=8,
                                            controls=[
                                                ft.Text(
                                                    f"{sessao.distancia_km:g} km • {tempo_str}",
                                                    size=12,
                                                    color=PURE_WHITE,
                                                ),
                                                ft.Text(
                                                    pace_badge,
                                                    size=12,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=ORCELA_BLUE,
                                                ),
                                            ],
                                        ),
                                        ft.Text(
                                            f"{sessao.calorias_estimadas} kcal • RPE {sessao.percepcao_esforco}/10{detalhes_fc}",
                                            size=11,
                                            color=TEXT_MUTED,
                                        ),
                                    ],
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                    icon_color=DANGER_RED,
                                    tooltip="Excluir sessão",
                                    on_click=lambda _, sid=sessao.id: remover_sessao(
                                        sid
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
