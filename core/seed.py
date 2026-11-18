from typing import Any

from sqlalchemy import func, select, text

from core.database import Base, engine, get_db_session
from models.cardio_models import SessaoCardio
from models.nutrition_models import (
    CheckItemDiario,
    ItemChecklistNutri,
    LojaSuplemento,
    MetaNutricional,
    RegistroBiometria,
    RegistroDiarioNutri,
    SuplementoEstoque,
)
from models.workout_models import Exercicio, Ficha, FichaExercicio

CATALOGO_INICIAL: list[dict[str, str]] = [
    # Peito
    {"nome": "Supino Reto com Barra", "grupo_muscular": "Peito", "equipamento": "Barra"},
    {"nome": "Supino Inclinado com Halteres", "grupo_muscular": "Peito", "equipamento": "Halter"},
    {"nome": "Crucifixo na Polia (Crossover)", "grupo_muscular": "Peito", "equipamento": "Polia"},
    # Costas
    {"nome": "Puxada Alta Frontal", "grupo_muscular": "Costas", "equipamento": "Polia"},
    {"nome": "Remada Curvada Pronada", "grupo_muscular": "Costas", "equipamento": "Barra"},
    {"nome": "Remada Baixa no Triângulo", "grupo_muscular": "Costas", "equipamento": "Polia"},
    # Ombros
    {"nome": "Desenvolvimento com Halteres", "grupo_muscular": "Ombros", "equipamento": "Halter"},
    {"nome": "Elevação Lateral com Halteres", "grupo_muscular": "Ombros", "equipamento": "Halter"},
    {"nome": "Crucifixo Inverso na Máquina", "grupo_muscular": "Ombros", "equipamento": "Máquina"},
    # Bíceps
    {"nome": "Rosca Direta com Barra W", "grupo_muscular": "Bíceps", "equipamento": "Barra"},
    {"nome": "Rosca Scott na Máquina", "grupo_muscular": "Bíceps", "equipamento": "Máquina"},
    # Tríceps
    {"nome": "Tríceps Pulley na Corda", "grupo_muscular": "Tríceps", "equipamento": "Polia"},
    {"nome": "Tríceps Francês com Halter", "grupo_muscular": "Tríceps", "equipamento": "Halter"},
    # Pernas
    {"nome": "Agachamento Livre com Barra", "grupo_muscular": "Pernas", "equipamento": "Barra"},
    {"nome": "Leg Press 45°", "grupo_muscular": "Pernas", "equipamento": "Máquina"},
    {"nome": "Stiff com Barra", "grupo_muscular": "Pernas", "equipamento": "Barra"},
    {"nome": "Cadeira Extensora", "grupo_muscular": "Pernas", "equipamento": "Máquina"},
    {"nome": "Mesa Flexora", "grupo_muscular": "Pernas", "equipamento": "Máquina"},
    # Core
    {"nome": "Abdominal Infra Paralelas", "grupo_muscular": "Core", "equipamento": "Peso Corporal"},
    {"nome": "Abdominal Crunch na Polia", "grupo_muscular": "Core", "equipamento": "Polia"},
]

ITENS_NUTRI_INICIAIS: list[dict[str, Any]] = [
    {
        "titulo": "Pré-treino: Cuscuz + Pasta de Amendoim",
        "categoria": "Refeição",
        "quantidade_gramas": 180.0,
        "tipo_macro": "Carboidrato",
        "proteina_estimada_g": 12.0,
        "proteina_g": 12.0,
        "carboidrato_g": 45.0,
        "ordem": 1,
    },
    {
        "titulo": "Café Preto",
        "categoria": "Suplemento",
        "quantidade_gramas": 200.0,
        "tipo_macro": "Calorias",
        "proteina_estimada_g": 0.0,
        "proteina_g": 0.0,
        "carboidrato_g": 0.0,
        "ordem": 2,
    },
    {
        "titulo": "Whey Protein Growth",
        "categoria": "Suplemento",
        "quantidade_gramas": 30.0,
        "tipo_macro": "Proteína",
        "proteina_estimada_g": 24.0,
        "proteina_g": 24.0,
        "carboidrato_g": 2.0,
        "ordem": 3,
    },
    {
        "titulo": "Creatina Growth (5g)",
        "categoria": "Suplemento",
        "quantidade_gramas": 5.0,
        "tipo_macro": "Proteína",
        "proteina_estimada_g": 0.0,
        "proteina_g": 0.0,
        "carboidrato_g": 0.0,
        "ordem": 4,
    },
    {
        "titulo": "Refeição 1: Arroz, Feijão e Carne",
        "categoria": "Refeição",
        "quantidade_gramas": 350.0,
        "tipo_macro": "Proteína",
        "proteina_estimada_g": 45.0,
        "proteina_g": 45.0,
        "carboidrato_g": 55.0,
        "ordem": 5,
    },
    {
        "titulo": "Refeição 2: Macarrão/Arroz e Carne",
        "categoria": "Refeição",
        "quantidade_gramas": 350.0,
        "tipo_macro": "Proteína",
        "proteina_estimada_g": 45.0,
        "proteina_g": 45.0,
        "carboidrato_g": 60.0,
        "ordem": 6,
    },
]

ESTOQUE_INICIAL: list[dict[str, Any]] = [
    {
        "nome": "Creatina Growth",
        "unidade": "doses",
        "peso_total_g": 250.0,
        "peso_restante_g": 250.0,
        "dose_padrao_g": 5.0,
        "quantidade_total": 50.0,
        "quantidade_atual": 50.0,
        "consumo_diario_padrao": 1.0,
        "alerta_minimo_percentual": 20.0,
    },
    {
        "nome": "Whey Protein Growth",
        "unidade": "doses",
        "peso_total_g": 1000.0,
        "peso_restante_g": 1000.0,
        "dose_padrao_g": 30.0,
        "quantidade_total": 33.0,
        "quantidade_atual": 33.0,
        "consumo_diario_padrao": 1.0,
        "alerta_minimo_percentual": 20.0,
    },
]


LOJAS_INICIAIS: list[dict[str, str]] = [
    {"nome": "Growth Supplements", "url": "https://www.gsuplementos.com.br"},
    {"nome": "Max Titanium", "url": "https://www.maxtitanium.com.br"},
    {"nome": "Integralmedica", "url": "https://www.integralmedica.com.br"},
    {"nome": "Dark Lab", "url": "https://www.darklabsuplementos.com.br"},
]


def init_db() -> None:
    """Cria as tabelas do banco SQLite e popula o catálogo de treino, nutrição, biometria e estoque."""
    _ = (
        RegistroDiarioNutri,
        CheckItemDiario,
        RegistroBiometria,
        LojaSuplemento,
        SuplementoEstoque,
        SessaoCardio,
    )
    Base.metadata.create_all(bind=engine)

    with get_db_session() as session:
        colunas_atuais = {
            str(row[1])
            for row in session.execute(
                text("PRAGMA table_info(sessoes_treino)")
            ).all()
        }
        novas_colunas = [
            ("duracao_segundos", "INTEGER"),
            ("fc_media", "INTEGER"),
            ("calorias_estimadas", "INTEGER"),
            ("percepcao_esforco", "INTEGER"),
        ]
        for col_nome, col_tipo in novas_colunas:
            if col_nome not in colunas_atuais:
                session.execute(
                    text(
                        f"ALTER TABLE sessoes_treino ADD COLUMN {col_nome} {col_tipo}"
                    )
                )

        colunas_estoque = {
            str(row[1])
            for row in session.execute(
                text("PRAGMA table_info(suplementos_estoque)")
            ).all()
        }
        if "loja_id" not in colunas_estoque:
            session.execute(
                text(
                    "ALTER TABLE suplementos_estoque ADD COLUMN loja_id INTEGER "
                    "REFERENCES lojas_suplementos(id) ON DELETE SET NULL"
                )
            )
        novas_colunas_estoque = [
            ("peso_total_g", "FLOAT NOT NULL DEFAULT 300.0"),
            ("peso_restante_g", "FLOAT NOT NULL DEFAULT 300.0"),
            ("dose_padrao_g", "FLOAT NOT NULL DEFAULT 5.0"),
        ]
        for col_n, col_def in novas_colunas_estoque:
            if col_n not in colunas_estoque:
                session.execute(
                    text(
                        f"ALTER TABLE suplementos_estoque ADD COLUMN {col_n} {col_def}"
                    )
                )

        colunas_checklist = {
            str(row[1])
            for row in session.execute(
                text("PRAGMA table_info(itens_checklist_nutri)")
            ).all()
        }
        novas_colunas_checklist = [
            ("quantidade_gramas", "FLOAT NOT NULL DEFAULT 100.0"),
            ("tipo_macro", "VARCHAR(30) NOT NULL DEFAULT 'Proteína'"),
            ("proteina_g", "FLOAT NOT NULL DEFAULT 0.0"),
            ("carboidrato_g", "FLOAT NOT NULL DEFAULT 0.0"),
        ]
        for col_n, col_def in novas_colunas_checklist:
            if col_n not in colunas_checklist:
                session.execute(
                    text(
                        f"ALTER TABLE itens_checklist_nutri ADD COLUMN {col_n} {col_def}"
                    )
                )

        colunas_ficha_ex = {
            str(row[1])
            for row in session.execute(
                text("PRAGMA table_info(ficha_exercicios)")
            ).all()
        }
        if "observacoes" not in colunas_ficha_ex:
            session.execute(
                text(
                    "ALTER TABLE ficha_exercicios ADD COLUMN observacoes VARCHAR(255)"
                )
            )
        session.flush()
        total_exercicios = session.scalar(select(func.count(Exercicio.id))) or 0
        if total_exercicios == 0:
            exercicios_map: dict[str, Exercicio] = {}
            for item in CATALOGO_INICIAL:
                exercicio = Exercicio(
                    nome=item["nome"],
                    grupo_muscular=item["grupo_muscular"],
                    equipamento=item["equipamento"],
                )
                session.add(exercicio)
                exercicios_map[item["nome"]] = exercicio

            session.flush()

            ficha_padrao = Ficha(
                nome="Full Body / Upper Inicial",
                descricao="Ficha base focada em compostos e tensão mecânica progressiva.",
                ativa=True,
            )
            session.add(ficha_padrao)
            session.flush()

            exercicios_ficha = [
                ("Supino Reto com Barra", 4, "6-8", 120),
                ("Puxada Alta Frontal", 4, "8-12", 90),
                ("Desenvolvimento com Halteres", 3, "8-10", 90),
                ("Agachamento Livre com Barra", 4, "6-8", 150),
            ]

            for ordem, (nome_ex, series, reps, descanso) in enumerate(exercicios_ficha, start=1):
                exercicio_obj = exercicios_map[nome_ex]
                vinculo = FichaExercicio(
                    ficha_id=ficha_padrao.id,
                    exercicio_id=exercicio_obj.id,
                    ordem=ordem,
                    series_alvo=series,
                    reps_alvo=reps,
                    descanso_segundos=descanso,
                )
                session.add(vinculo)

        meta_existente = session.get(MetaNutricional, 1)
        if meta_existente is None:
            session.add(
                MetaNutricional(
                    id=1,
                    meta_proteina_g=160.0,
                    meta_agua_ml=3500,
                    doses_creatina_alvo=4,
                )
            )

        total_itens_nutri = session.scalar(select(func.count(ItemChecklistNutri.id))) or 0
        if total_itens_nutri == 0:
            for item_n in ITENS_NUTRI_INICIAIS:
                session.add(
                    ItemChecklistNutri(
                        titulo=str(item_n["titulo"]),
                        categoria=str(item_n["categoria"]),
                        quantidade_gramas=float(item_n.get("quantidade_gramas", 100.0)),
                        tipo_macro=str(item_n.get("tipo_macro", "Proteína")),
                        proteina_estimada_g=float(item_n["proteina_estimada_g"]),
                        proteina_g=float(item_n.get("proteina_g", item_n["proteina_estimada_g"])),
                        carboidrato_g=float(item_n.get("carboidrato_g", 0.0)),
                        ativo=True,
                        ordem=int(item_n["ordem"]),
                    )
                )
        else:
            # Sincroniza proteina_g e tipo_macro nos itens antigos quando ainda zerados
            itens_existentes = list(
                session.scalars(select(ItemChecklistNutri)).all()
            )
            for it_ex in itens_existentes:
                if it_ex.proteina_g == 0.0 and it_ex.proteina_estimada_g > 0.0:
                    it_ex.proteina_g = float(it_ex.proteina_estimada_g)
                if "cuscuz" in it_ex.titulo.lower() and it_ex.carboidrato_g == 0.0:
                    it_ex.tipo_macro = "Carboidrato"
                    it_ex.carboidrato_g = 45.0
                    it_ex.quantidade_gramas = 180.0

        total_biometria = session.scalar(select(func.count(RegistroBiometria.id))) or 0
        if total_biometria == 0:
            session.add(
                RegistroBiometria(
                    peso_kg=77.6,
                    altura_cm=190.0,
                    notas="Biometria inicial padrão",
                )
            )

        total_lojas = session.scalar(select(func.count(LojaSuplemento.id))) or 0
        if total_lojas == 0:
            for lj in LOJAS_INICIAIS:
                session.add(
                    LojaSuplemento(
                        nome=lj["nome"],
                        url=lj["url"],
                        ativa=True,
                    )
                )
            session.flush()

        loja_growth = session.scalar(
            select(LojaSuplemento).where(LojaSuplemento.nome == "Growth Supplements")
        )
        growth_id = loja_growth.id if loja_growth is not None else None

        total_estoque = session.scalar(select(func.count(SuplementoEstoque.id))) or 0
        if total_estoque == 0:
            for sup in ESTOQUE_INICIAL:
                session.add(
                    SuplementoEstoque(
                        nome=str(sup["nome"]),
                        unidade=str(sup["unidade"]),
                        peso_total_g=float(sup["peso_total_g"]),
                        peso_restante_g=float(sup["peso_restante_g"]),
                        dose_padrao_g=float(sup["dose_padrao_g"]),
                        quantidade_total=float(sup["quantidade_total"]),
                        quantidade_atual=float(sup["quantidade_atual"]),
                        consumo_diario_padrao=float(sup["consumo_diario_padrao"]),
                        alerta_minimo_percentual=float(sup["alerta_minimo_percentual"]),
                        ativo=True,
                        loja_id=growth_id,
                    )
                )
        else:
            todos_sups = list(session.scalars(select(SuplementoEstoque)).all())
            for sup_item in todos_sups:
                if growth_id is not None and sup_item.loja_id is None and "growth" in sup_item.nome.lower():
                    sup_item.loja_id = growth_id
                if "whey" in sup_item.nome.lower() and sup_item.peso_total_g == 300.0 and sup_item.dose_padrao_g == 5.0:
                    sup_item.dose_padrao_g = 30.0
                    sup_item.peso_total_g = round(float(sup_item.quantidade_total) * 30.0, 1)
                    sup_item.peso_restante_g = round(float(sup_item.quantidade_atual) * 30.0, 1)
                elif "creatina" in sup_item.nome.lower() and sup_item.peso_total_g == 300.0:
                    sup_item.dose_padrao_g = 3.0 if sup_item.quantidade_total >= 80 else 5.0
                    sup_item.peso_total_g = round(float(sup_item.quantidade_total) * float(sup_item.dose_padrao_g), 1)
                    sup_item.peso_restante_g = round(float(sup_item.quantidade_atual) * float(sup_item.dose_padrao_g), 1)
