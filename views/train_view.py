from datetime import datetime
import threading
import time
from typing import Any

import flet as ft

from models.workout_models import Ficha
from services.workout_service import (
    excluir_sessao,
    finalizar_sessao,
    iniciar_sessao,
    listar_fichas,
    listar_historico_sessoes,
    obter_ficha_por_id,
    obter_metricas_resumo,
    obter_ultima_execucao_exercicio,
    registrar_serie,
    registrar_treino_muscular_manual,
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

TIPOS_SERIE = [
    ("W", "W — Trabalho"),
    ("A", "A — Aquecimento"),
    ("D", "D — Dropset"),
    ("F", "F — Falha"),
]


def _extrair_reps_padrao(reps_alvo: str) -> int:
    """Extrai o primeiro número inteiro da faixa de repetições alvo (ex: '8-12' -> 8)."""
    partes = reps_alvo.replace(" ", "").split("-")
    for parte in partes:
        if parte.isdigit():
            return int(parte)
    return 10


def build_train_view(page: ft.Page) -> ft.Control:
    """Constrói a view modular de Execução de Treino, Registro Manual e Histórico."""
    sessao_ativa_id: int | None = None
    ficha_ativa: Ficha | None = None
    series_concluidas: set[tuple[int, int]] = set()
    timer_segundos_restantes: int = 0
    timer_rodando: bool = False
    timer_token: int = 0
    form_manual_visivel: bool = False
    confirmando_fim_ativo: bool = False

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
        bar_height=8,
        border_radius=ft.BorderRadius.all(10),
    )

    tf_notas_sessao = ft.TextField(
        label="Notas do treino (opcional)",
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
    )
    tf_fc_ativo = ft.TextField(
        label="FC Média (bpm)",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_calorias_ativo = ft.TextField(
        label="Calorias (kcal)",
        hint_text="Ex: 420 (opcional)",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_rpe_ativo = ft.TextField(
        label="RPE (1-10)",
        value="8",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        width=95,
    )

    # Controles do Registro Manual de Treino Muscular
    dd_ficha_manual = ft.Dropdown(
        label="Ficha Realizada (ou Treino Livre)",
        value="0",
        border=construir_borda_input(),
        color=PURE_WHITE,
        expand=True,
    )
    tf_duracao_manual = ft.TextField(
        label="Duração (min)",
        value="55",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_calorias_manual = ft.TextField(
        label="Calorias (kcal)",
        hint_text="Ex: 420 (opcional)",
        keyboard_type=ft.KeyboardType.NUMBER,
        border=construir_borda_input(),
        color=PURE_WHITE,
        text_size=13,
        expand=True,
    )
    tf_fc_manual = ft.TextField(
        label="FC Média (bpm)",
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
        expand=True,
    )
    tf_notas_manual = ft.TextField(
        label="Notas / Observações (opcional)",
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
            border=ft.Border.all(1, ORCELA_BORDER_GLOW),
            shadow=construir_sombra_orcela(),
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

    def alternar_form_manual(_: Any = None) -> None:
        nonlocal form_manual_visivel
        form_manual_visivel = not form_manual_visivel
        renderizar()

    def salvar_treino_manual(_: Any = None) -> None:
        nonlocal form_manual_visivel
        try:
            fid_val = int(dd_ficha_manual.value or "0")
            ficha_id_sel = fid_val if fid_val > 0 else None
            dur_min = int(float((tf_duracao_manual.value or "50").replace(",", ".")))
            cal_val = (
                int(float(tf_calorias_manual.value.replace(",", ".")))
                if (tf_calorias_manual.value and tf_calorias_manual.value.strip())
                else None
            )
            fc_val = (
                int(tf_fc_manual.value)
                if (tf_fc_manual.value and tf_fc_manual.value.strip())
                else None
            )
            rpe_val = int(tf_rpe_manual.value or "8")
            sessao = registrar_treino_muscular_manual(
                ficha_id=ficha_id_sel,
                data_treino=datetime.now(),
                duracao_minutos=dur_min,
                fc_media=fc_val,
                percepcao_esforco=rpe_val,
                notas=tf_notas_manual.value,
                calorias_manuais=cal_val,
            )
            tf_notas_manual.value = ""
            tf_fc_manual.value = ""
            tf_calorias_manual.value = ""
            form_manual_visivel = False
            notificar(
                f"Treino manual salvo! {dur_min} min • {sessao.calorias_estimadas} kcal"
            )
            renderizar()
        except Exception as exc:
            notificar(str(exc), erro=True)

    def remover_sessao_historico(sessao_id: int) -> None:
        excluir_sessao(sessao_id)
        notificar("Sessão removida do histórico.")
        renderizar()

    def abrir_legenda_tipos_serie(_: Any = None) -> None:
        itens_legenda = [
            (
                "W — Trabalho (Work Set)",
                "Séries válidas principais da ficha; entram no cálculo de 1RM e recordes pessoais.",
            ),
            (
                "A — Aquecimento",
                "Séries preparatórias com carga leve antes das séries principais.",
            ),
            (
                "D — Dropset",
                "Redução imediata de carga sem intervalo de descanso.",
            ),
            (
                "F — Falha",
                "Série executada até a falha concêntrica total (também contabilizada no 1RM).",
            ),
        ]
        controles_legenda: list[ft.Control] = []
        for sigla_titulo, desc_txt in itens_legenda:
            controles_legenda.append(
                ft.Container(
                    bgcolor=DARK_BG,
                    border=ft.Border.all(1, ORCELA_BORDER_GLOW),
                    border_radius=8,
                    padding=10,
                    content=ft.Column(
                        spacing=3,
                        controls=[
                            ft.Text(
                                sigla_titulo,
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color=ORCELA_BLUE,
                            ),
                            ft.Text(
                                desc_txt,
                                size=12,
                                color=PURE_WHITE,
                            ),
                        ],
                    ),
                )
            )

        dlg_info = ft.AlertDialog(
            bgcolor=CARD_BG,
            shape=ft.RoundedRectangleBorder(
                radius=14, side=ft.BorderSide(width=1, color=ORCELA_BORDER_GLOW)
            ),
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(
                        ft.Icons.INFO_OUTLINE_ROUNDED,
                        color=ORCELA_BLUE,
                        size=22,
                    ),
                    ft.Text(
                        "Tipos de Série",
                        size=17,
                        weight=ft.FontWeight.BOLD,
                        color=PURE_WHITE,
                    ),
                ],
            ),
            content=ft.Column(
                tight=True,
                spacing=8,
                controls=controles_legenda,
            ),
            actions=[
                ft.TextButton(
                    content="Entendi",
                    on_click=lambda _: page.pop_dialog(),
                )
            ],
        )
        page.show_dialog(dlg_info)

    def descartar_sessao_ativa(_: Any = None) -> None:
        nonlocal sessao_ativa_id, ficha_ativa, confirmando_fim_ativo
        parar_cronometro(atualizar_pagina=False)
        if sessao_ativa_id is not None:
            excluir_sessao(sessao_ativa_id)
        sessao_ativa_id = None
        ficha_ativa = None
        confirmando_fim_ativo = False
        series_concluidas.clear()
        notificar("Sessão descartada.")
        renderizar()

    def solicitar_cancelamento_sessao(_: Any = None) -> None:
        if sessao_ativa_id is None:
            return
        if not series_concluidas:
            descartar_sessao_ativa()
            return

        def _confirmar_descarte(_: Any) -> None:
            page.pop_dialog()
            descartar_sessao_ativa()

        dlg_cancelar = ft.AlertDialog(
            bgcolor=CARD_BG,
            shape=ft.RoundedRectangleBorder(
                radius=14, side=ft.BorderSide(width=1, color=ORCELA_BORDER_GLOW)
            ),
            title=ft.Text(
                "Cancelar Sessão Ativa?",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=PURE_WHITE,
            ),
            content=ft.Text(
                f"Você já registrou {len(series_concluidas)} série(s) neste treino. Deseja descartar o progresso e sair?",
                size=13,
                color=TEXT_MUTED,
            ),
            actions=[
                ft.TextButton(
                    content="Continuar Treinando",
                    on_click=lambda _: page.pop_dialog(),
                ),
                ft.Button(
                    content="Descartar Treino",
                    bgcolor=DANGER_RED,
                    color=PURE_WHITE,
                    on_click=_confirmar_descarte,
                ),
            ],
        )
        page.show_dialog(dlg_cancelar)

    def comecar_treino(ficha_id: int) -> None:
        nonlocal sessao_ativa_id, ficha_ativa, confirmando_fim_ativo
        ficha_carregada = obter_ficha_por_id(ficha_id)
        if ficha_carregada is None:
            notificar("Ficha não encontrada.", erro=True)
            return

        sessao = iniciar_sessao(ficha_id=ficha_id)
        sessao_ativa_id = sessao.id
        ficha_ativa = ficha_carregada
        confirmando_fim_ativo = False
        series_concluidas.clear()
        tf_notas_sessao.value = ""
        tf_fc_ativo.value = ""
        tf_calorias_ativo.value = ""
        tf_rpe_ativo.value = "8"
        parar_cronometro(atualizar_pagina=False)
        renderizar()

    def abrir_confirmacao_fim_treino(_: Any = None) -> None:
        nonlocal confirmando_fim_ativo
        confirmando_fim_ativo = True
        renderizar()

    def concluir_treino_ativo(_: Any = None) -> None:
        nonlocal sessao_ativa_id, ficha_ativa, confirmando_fim_ativo
        if sessao_ativa_id is None:
            return
        parar_cronometro(atualizar_pagina=False)
        try:
            fc_val = (
                int(tf_fc_ativo.value)
                if (tf_fc_ativo.value and tf_fc_ativo.value.strip())
                else None
            )
            cal_val = (
                int(float(tf_calorias_ativo.value.replace(",", ".")))
                if (tf_calorias_ativo.value and tf_calorias_ativo.value.strip())
                else None
            )
            rpe_val = (
                int(tf_rpe_ativo.value)
                if (tf_rpe_ativo.value and tf_rpe_ativo.value.strip())
                else 8
            )
        except ValueError:
            fc_val = None
            cal_val = None
            rpe_val = 8

        sessao_fin = finalizar_sessao(
            sessao_id=sessao_ativa_id,
            notas=tf_notas_sessao.value,
            fc_media=fc_val,
            percepcao_esforco=rpe_val,
            calorias_manuais=cal_val,
        )
        total_series = len(series_concluidas)
        sessao_ativa_id = None
        ficha_ativa = None
        confirmando_fim_ativo = False
        series_concluidas.clear()
        notificar(
            f"Treino finalizado! {total_series} série(s) • ~{sessao_fin.calorias_estimadas or 0} kcal"
        )
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
            expand=True,
            height=38,
            text_align=ft.TextAlign.CENTER,
            content_padding=ft.Padding.symmetric(horizontal=4, vertical=8),
            keyboard_type=ft.KeyboardType.NUMBER,
            border=construir_borda_input(6.0),
            color=PURE_WHITE,
            text_size=13,
        )
        tf_reps = ft.TextField(
            value=str(reps_sugeridas),
            expand=True,
            height=38,
            text_align=ft.TextAlign.CENTER,
            content_padding=ft.Padding.symmetric(horizontal=4, vertical=8),
            keyboard_type=ft.KeyboardType.NUMBER,
            border=construir_borda_input(6.0),
            color=PURE_WHITE,
            text_size=13,
        )
        tf_rir = ft.TextField(
            value=str(rir_sugerido) if rir_sugerido is not None else "2",
            expand=True,
            height=38,
            text_align=ft.TextAlign.CENTER,
            content_padding=ft.Padding.symmetric(horizontal=4, vertical=8),
            keyboard_type=ft.KeyboardType.NUMBER,
            border=construir_borda_input(6.0),
            color=PURE_WHITE,
            text_size=13,
        )
        tipo_atual = (
            tipo_sugerido if tipo_sugerido in {"W", "A", "D", "F"} else "W"
        )
        txt_tipo_selecionado = ft.Text(
            tipo_atual,
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ORCELA_BLUE,
        )

        def selecionar_tipo_serie(novo_cod: str) -> None:
            nonlocal tipo_atual
            tipo_atual = novo_cod
            txt_tipo_selecionado.value = novo_cod
            page.update()

        seletor_tipo = ft.PopupMenuButton(
            width=46,
            height=40,
            tooltip="Selecionar tipo de série",
            content=ft.Container(
                width=46,
                height=38,
                bgcolor="#141414",
                border=ft.Border.all(1, ORCELA_BORDER_GLOW),
                border_radius=8,
                alignment=ft.Alignment.CENTER,
                content=txt_tipo_selecionado,
            ),
            items=[
                ft.PopupMenuItem(
                    content=ft.Text(
                        desc_item,
                        size=13,
                        weight=ft.FontWeight.W_500,
                        color=PURE_WHITE,
                    ),
                    on_click=lambda _, c=cod_item: selecionar_tipo_serie(c),
                )
                for cod_item, desc_item in TIPOS_SERIE
            ],
        )

        chave_serie = (exercicio_id, numero_serie)
        ja_concluida = chave_serie in series_concluidas

        btn_check = ft.IconButton(
            icon=ft.Icons.CHECK_CIRCLE_ROUNDED
            if ja_concluida
            else ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
            icon_color=ORCELA_BLUE if ja_concluida else TEXT_MUTED,
            icon_size=20,
            width=36,
            height=36,
            tooltip="Registrar Série",
        )

        linha_container = ft.Container(
            bgcolor=ORCELA_DARK_SURFACE if ja_concluida else DARK_BG,
            border=ft.Border.all(
                1, ORCELA_BLUE if ja_concluida else ORCELA_BORDER_GLOW
            ),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=6, vertical=6),
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
                tipo_serie=tipo_atual,
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
            spacing=4,
            controls=[
                ft.Text(
                    f"#{numero_serie}",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=ORCELA_BLUE,
                    width=22,
                ),
                seletor_tipo,
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
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    controls=[
                        ft.Text("Série", size=11, color=TEXT_MUTED, width=28),
                        ft.GestureDetector(
                            on_tap=abrir_legenda_tipos_serie,
                            content=ft.Container(
                                width=46,
                                tooltip="Ver significado dos tipos de série",
                                content=ft.Row(
                                    spacing=3,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Text(
                                            "Tipo",
                                            size=11,
                                            weight=ft.FontWeight.BOLD,
                                            color=ORCELA_BLUE,
                                        ),
                                        ft.Icon(
                                            ft.Icons.INFO_OUTLINE_ROUNDED,
                                            size=14,
                                            color=ORCELA_BLUE,
                                        ),
                                    ],
                                ),
                            ),
                        ),
                        ft.Text(
                            "Carga (kg)",
                            size=11,
                            color=TEXT_MUTED,
                            expand=True,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Reps",
                            size=11,
                            color=TEXT_MUTED,
                            expand=True,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "RIR",
                            size=11,
                            color=TEXT_MUTED,
                            expand=True,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "OK",
                            size=11,
                            color=TEXT_MUTED,
                            width=36,
                            text_align=ft.TextAlign.CENTER,
                        ),
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
                rir_sug = (
                    serie_ant.rir
                    if (serie_ant and serie_ant.rir is not None)
                    else 2
                )
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
                    border=ft.Border.all(1, ORCELA_BORDER_GLOW),
                    shadow=construir_sombra_orcela(),
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

        bloco_finalizacao: list[ft.Control] = []
        if confirmando_fim_ativo:
            bloco_finalizacao.append(
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, ORCELA_BORDER_HIGHLIGHT),
                    shadow=construir_sombra_orcela(),
                    border_radius=12,
                    padding=14,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text(
                                "Resumo de Intensidade da Sessão",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=PURE_WHITE,
                            ),
                            ft.Row(
                                spacing=8,
                                controls=[tf_calorias_ativo, tf_fc_ativo, tf_rpe_ativo],
                            ),
                            tf_notas_sessao,
                            ft.Button(
                                content="CONFIRMAR E SALVAR TREINO",
                                icon=ft.Icons.CHECK_CIRCLE_ROUNDED,
                                bgcolor=ORCELA_BLUE,
                                color=PURE_WHITE,
                                width=float("inf"),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                                on_click=concluir_treino_ativo,
                            ),
                        ],
                    ),
                )
            )
        else:
            bloco_finalizacao.extend(
                [
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
                        on_click=abrir_confirmacao_fim_treino,
                    ),
                ]
            )

        return [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_ROUNDED,
                        icon_color=PURE_WHITE,
                        bgcolor=ORCELA_DARK_SURFACE,
                        tooltip="Voltar / Cancelar Sessão",
                        on_click=solicitar_cancelamento_sessao,
                    ),
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
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
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
                border=ft.Border.all(1, ORCELA_BORDER_HIGHLIGHT),
                shadow=construir_sombra_orcela(),
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
                                    on_click=lambda _: parar_cronometro(True),
                                ),
                            ],
                        ),
                        barra_progresso_timer,
                    ],
                ),
            ),
            *blocos_exercicios,
            *bloco_finalizacao,
        ]

    def renderizar_modo_resumo() -> list[ft.Control]:
        metricas = obter_metricas_resumo()
        fichas_ativas = listar_fichas(apenas_ativas=True)
        historico_sessoes = listar_historico_sessoes(limite=20)

        dd_ficha_manual.options = [
            ft.dropdown.Option(key="0", text="Treino Livre / Avulso"),
            *[
                ft.dropdown.Option(key=str(f.id), text=f.nome)
                for f in fichas_ativas
            ],
        ]
        if not dd_ficha_manual.value:
            dd_ficha_manual.value = "0"

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
                    border=ft.Border.all(1, ORCELA_BORDER_HIGHLIGHT),
                    shadow=construir_sombra_orcela(),
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

        cards_historico: list[ft.Control] = []
        if not historico_sessoes:
            cards_historico.append(
                ft.Container(
                    bgcolor=CARD_BG,
                    border=ft.Border.all(1, ORCELA_BORDER_GLOW),
                    shadow=construir_sombra_orcela(),
                    border_radius=12,
                    padding=16,
                    content=ft.Text(
                        "Nenhum treino muscular concluído ainda. Inicie uma sessão acima ou use 'Registrar Treino Manual'.",
                        size=12,
                        color=TEXT_MUTED,
                    ),
                )
            )
        else:
            def _construir_pilula_badge(texto: str) -> ft.Container:
                return ft.Container(
                    bgcolor=ORCELA_DARK_SURFACE,
                    border=ft.Border.all(1, ORCELA_BORDER_HIGHLIGHT),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    border_radius=6,
                    content=ft.Text(
                        texto,
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=ORCELA_BLUE,
                    ),
                )

            for hs in historico_sessoes:
                intensidade_lbl = str(hs.get("intensidade_sessao", "Moderada"))
                kcal_min = float(hs.get("kcal_por_min", 0.0))
                pilulas_badges: list[ft.Control] = [
                    _construir_pilula_badge(f"Intensidade {intensidade_lbl}")
                ]
                if hs["percepcao_esforco"] is not None:
                    pilulas_badges.append(
                        _construir_pilula_badge(f"RPE {hs['percepcao_esforco']}/10")
                    )
                if hs["fc_media"] is not None:
                    pilulas_badges.append(
                        _construir_pilula_badge(f"{hs['fc_media']} bpm")
                    )

                metricas_rodape: list[ft.Control] = []
                if hs["tonelagem_kg"] > 0:
                    metricas_rodape.append(
                        ft.Text(
                            f"Volume: {hs['tonelagem_kg']:.0f} kg",
                            size=12,
                            color=ORCELA_BLUE,
                            weight=ft.FontWeight.BOLD,
                        )
                    )
                metricas_rodape.append(
                    ft.Text(
                        f"{hs['total_series']} séries • {hs['calorias_estimadas']} kcal ({kcal_min:.1f} kcal/min)",
                        size=12,
                        color=PURE_WHITE,
                    )
                )

                controles_card_hist: list[ft.Control] = [
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        spacing=8,
                        controls=[
                            ft.Column(
                                spacing=2,
                                expand=True,
                                controls=[
                                    ft.Text(
                                        str(hs["nome_ficha"]),
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=PURE_WHITE,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        f"{hs['data_fmt']} • {hs['duracao_fmt']}",
                                        size=12,
                                        color=TEXT_MUTED,
                                    ),
                                ],
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                icon_color=DANGER_RED,
                                icon_size=20,
                                tooltip="Excluir treino",
                                on_click=lambda _, sid=hs["id"]: remover_sessao_historico(
                                    sid
                                ),
                            ),
                        ],
                    ),
                    ft.Row(
                        wrap=True,
                        spacing=6,
                        run_spacing=6,
                        controls=pilulas_badges,
                    ),
                    ft.Row(
                        wrap=True,
                        spacing=8,
                        run_spacing=4,
                        controls=metricas_rodape,
                    ),
                ]

                if hs["resumo_exercicios"]:
                    controles_card_hist.append(
                        ft.Text(
                            " | ".join(hs["resumo_exercicios"]),
                            size=11,
                            color=TEXT_MUTED,
                        )
                    )
                if hs["notas"]:
                    controles_card_hist.append(
                        ft.Text(
                            f"Nota: {hs['notas']}",
                            size=11,
                            color=TEXT_MUTED,
                        )
                    )

                cards_historico.append(
                    ft.Container(
                        bgcolor=CARD_BG,
                        border=ft.Border.all(1, ORCELA_BORDER_GLOW),
                        shadow=construir_sombra_orcela(),
                        border_radius=12,
                        padding=14,
                        content=ft.Column(spacing=6, controls=controles_card_hist),
                    )
                )

        controles_topo: list[ft.Control] = [
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
                                "Treino & Histórico",
                                size=12,
                                color=TEXT_MUTED,
                            ),
                        ],
                    ),
                    ft.OutlinedButton(
                        content="Registrar Treino Manual",
                        icon=ft.Icons.ADD_ROUNDED,
                        style=ft.ButtonStyle(
                            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                        ),
                        on_click=alternar_form_manual,
                    ),
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
        ]

        if form_manual_visivel:
            controles_topo.append(
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
                                        "Registrar Treino Muscular Manual",
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
                            ft.Row(controls=[dd_ficha_manual]),
                            ft.Row(
                                spacing=8,
                                controls=[
                                    tf_duracao_manual,
                                    tf_calorias_manual,
                                ],
                            ),
                            ft.Row(
                                spacing=8,
                                controls=[
                                    tf_fc_manual,
                                    tf_rpe_manual,
                                ],
                            ),
                            tf_notas_manual,
                            ft.Button(
                                content="SALVAR TREINO MANUAL",
                                icon=ft.Icons.CHECK_ROUNDED,
                                bgcolor=ORCELA_BLUE,
                                color=PURE_WHITE,
                                width=float("inf"),
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                                on_click=salvar_treino_manual,
                            ),
                        ],
                    ),
                )
            )

        return [
            *controles_topo,
            ft.Text(
                "PRONTO PARA TREINAR",
                size=13,
                weight=ft.FontWeight.BOLD,
                color=TEXT_MUTED,
            ),
            *cards_fichas,
            ft.Text(
                "HISTÓRICO DE TREINOS MUSCULARES",
                size=13,
                weight=ft.FontWeight.BOLD,
                color=TEXT_MUTED,
            ),
            *cards_historico,
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
