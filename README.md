# P4 Workout

Aplicação mobile *offline-first* desenvolvida em Python com Flet e SQLite para rastreamento de treinos de hipertrofia e força, análise de progressão de carga, monitoramento biométrico e gestão de nutrição e estoque de suplementos.

---

## Visão Geral

O **P4 Workout** foi projetado para uso pessoal em dispositivos Android, eliminando dependências de servidores externos, APIs intermediárias ou conexão contínua com a internet. Toda a persistência de dados ocorre localmente no dispositivo por meio de SQLite integrado ao SQLAlchemy 2.0, garantindo baixa latência durante o registro de séries e disponibilidade total em ambientes sem rede.

A interface segue uma identidade visual de alto contraste baseada em fundo escuro (`#0F0F0F`), Branco (`#FFFFFF`) e Azul Orcela (`#007BFF`), otimizada para operação rápida com uma mão durante o treino.

---

## Funcionalidades (v1.0)

### 1. Execução de Treino (`Treinar`)
- **Auto-fill de Cargas e Repetições:** Pré-preenchimento automático dos campos de carga (kg) e repetições com base na última sessão finalizada daquele exercício.
- **Classificação de Séries e Intensidade:** Suporte a tipos de série (`W` - Trabalho, `A` - Aquecimento, `D` - Dropset, `F` - Falha) e registro de Repetições na Reserva (`RIR`).
- **Cronômetro de Descanso Integrado:** Temporizador regressivo acionado automaticamente após a conclusão de cada série, respeitando o tempo configurado na ficha.

### 2. Gestão de Fichas e Catálogo (`Fichas`)
- Criação, visualização e exclusão de rotinas de treino personalizadas.
- Configuração individual por exercício: ordem de execução, séries alvo, faixa de repetições e tempo de descanso em segundos.
- Cadastro rápido de novos exercícios diretamente no fluxo de montagem da ficha, categorizados por grupo muscular e equipamento.

### 3. Análise de Desempenho e Biometria (`Evolução`)
- **Métricas de Treino:** Cálculo de tonelagem total acumulada ($\sum \text{Séries} \times \text{Repetições} \times \text{Carga}$), volume por grupo muscular nos últimos 30 dias e recordes pessoais (PR).
- **Estimativa de Força Máxima:** Cálculo automático de 1RM estimado pela Fórmula de Epley considerando séries válidas de trabalho e falha.
- **Biometria Corporal:** Registro histórico de peso corporal, altura e medidas, com cálculo automático de IMC, Taxa Metabólica Basal (equação de Mifflin-St Jeor), relação força/peso corporal e gráfico de evolução de peso.

### 4. Nutrição, Hidratação e Estoque (`Nutri`)
- **Controle de Metas Diárias:** Acompanhamento de ingestão proteica (g), hidratação (ml) e doses diárias de creatina com barras de progresso e botões de incremento rápido.
- **Checklist Diário Recorrente:** Registro de refeições e suplementos fixos com soma automática de proteína ingerida e navegação entre datas.
- **Gestão Inteligente de Estoque:** Controle de saldo de suplementos em doses ou gramas, estimativa de dias restantes e alertas visuais preventivos quando o estoque atinge níveis baixos ($\le 20\%$) ou críticos ($\le 5\%$).

---

## Stack Tecnológica

- **Linguagem:** Python 3.12+
- **Interface Gráfica (UI/UX):** Flet 1.1+ (Flutter engine para Python)
- **ORM e Persistência:** SQLAlchemy 2.0 (`Mapped` / `mapped_column`)
- **Banco de Dados:** SQLite 3 (local, com `PRAGMA foreign_keys=ON`)
- **Validação de Dados:** Pydantic

---

## Arquitetura do Projeto

```text
P4Workout/
├── main.py                     # Ponto de entrada, tema Azul Orcela e navegação inferior
├── requirements.txt            # Dependências do projeto
├── core/
│   ├── database.py             # Engine SQLite, pragmas e gerenciador transacional de sessão
│   └── seed.py                 # Criação de tabelas e carga inicial de exercícios, fichas e metas
├── models/
│   ├── workout_models.py       # Entidades: Exercicio, Ficha, FichaExercicio, SessaoTreino, SerieExecutada
│   └── nutrition_models.py     # Entidades: MetaNutricional, ItemChecklistNutri, RegistroDiarioNutri, RegistroBiometria, SuplementoEstoque
├── services/
│   ├── workout_service.py      # Regras de negócio de sessões, séries, auto-fill e fichas
│   ├── analytics_service.py    # Consultas de tonelagem, 1RM (Epley), IMC e TMB
│   └── nutrition_service.py    # Controle diário nutricional e baixa/reposição de estoque
└── views/
    ├── train_view.py           # Tela de execução de treino ativo e cronômetro
    ├── routines_view.py        # Tela de gerenciamento de fichas e catálogo
    ├── stats_view.py           # Tela de gráficos analíticos e biometria
    └── nutrition_view.py       # Tela de metas nutricionais, checklist e estoque

```

---

## Instalação e Execução Local

### Pré-requisitos

* Python 3.12 ou superior instalado
* Gerenciador de pacotes `pip`

### Passo a Passo

1. Clone o repositório e acesse o diretório do projeto:

```bash
git clone [https://github.com/Pablo-Cardoso-23/P4-Workout-Mobile.git](https://github.com/Pablo-Cardoso-23/P4-Workout-Mobile.git)
cd P4Workout

```

2. Crie e ative um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate

```

3. Instale as dependências:

```bash
pip install -r requirements.txt

```

4. Execute a aplicação (com suporte a recarregamento automático durante o desenvolvimento):

```bash
flet run -r main.py

```

Na primeira execução, o arquivo `p4workout.db` será criado automaticamente na raiz do projeto com o catálogo inicial de exercícios, uma ficha padrão e as metas nutricionais configuradas.

---

## Roadmap

* Adaptação do diretório de persistência do SQLite para o armazenamento interno do Android (`FLET_APP_STORAGE_DATA`).
* Configuração de metadados, ícone oficial e empacotamento para Android (`flet build apk`).
* Exportação e backup local/em nuvem do banco de dados em formato JSON ou CSV.

```

Para salvar diretamente na raiz do seu projeto pelo terminal, rode:

```bash
cat << 'EOF' > README.md

```
