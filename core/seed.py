from typing import Any

from sqlalchemy import func, select

from core.database import Base, engine, get_db_session
from models.nutrition_models import (
    CheckItemDiario,
    ItemChecklistNutri,
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
        "proteina_estimada_g": 18.0,
        "ordem": 1,
    },
    {
        "titulo": "Café Preto",
        "categoria": "Suplemento",
        "proteina_estimada_g": 0.0,
        "ordem": 2,
    },
    {
        "titulo": "Whey Protein Growth",
        "categoria": "Suplemento",
        "proteina_estimada_g": 24.0,
        "ordem": 3,
    },
    {
        "titulo": "Creatina Growth (4 doses)",
        "categoria": "Suplemento",
        "proteina_estimada_g": 0.0,
        "ordem": 4,
    },
    {
        "titulo": "Refeição 1: Arroz, Feijão e Carne",
        "categoria": "Refeição",
        "proteina_estimada_g": 45.0,
        "ordem": 5,
    },
    {
        "titulo": "Refeição 2: Macarrão/Arroz e Carne",
        "categoria": "Refeição",
        "proteina_estimada_g": 45.0,
        "ordem": 6,
    },
]

ESTOQUE_INICIAL: list[dict[str, Any]] = [
    {
        "nome": "Creatina Growth",
        "unidade": "doses",
        "quantidade_total": 80.0,
        "quantidade_atual": 80.0,
        "consumo_diario_padrao": 4.0,
        "alerta_minimo_percentual": 20.0,
    },
    {
        "nome": "Whey Protein Growth",
        "unidade": "doses",
        "quantidade_total": 33.0,
        "quantidade_atual": 33.0,
        "consumo_diario_padrao": 1.0,
        "alerta_minimo_percentual": 20.0,
    },
]


def init_db() -> None:
    """Cria as tabelas do banco SQLite e popula o catálogo de treino, nutrição, biometria e estoque."""
    _ = (RegistroDiarioNutri, CheckItemDiario, RegistroBiometria, SuplementoEstoque)
    Base.metadata.create_all(bind=engine)

    with get_db_session() as session:
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
                        proteina_estimada_g=float(item_n["proteina_estimada_g"]),
                        ativo=True,
                        ordem=int(item_n["ordem"]),
                    )
                )

        total_biometria = session.scalar(select(func.count(RegistroBiometria.id))) or 0
        if total_biometria == 0:
            session.add(
                RegistroBiometria(
                    peso_kg=77.6,
                    altura_cm=190.0,
                    notas="Biometria inicial padrão",
                )
            )

        total_estoque = session.scalar(select(func.count(SuplementoEstoque.id))) or 0
        if total_estoque == 0:
            for sup in ESTOQUE_INICIAL:
                session.add(
                    SuplementoEstoque(
                        nome=str(sup["nome"]),
                        unidade=str(sup["unidade"]),
                        quantidade_total=float(sup["quantidade_total"]),
                        quantidade_atual=float(sup["quantidade_atual"]),
                        consumo_diario_padrao=float(sup["consumo_diario_padrao"]),
                        alerta_minimo_percentual=float(sup["alerta_minimo_percentual"]),
                        ativo=True,
                    )
                )
