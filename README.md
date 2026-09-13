# Customer Experience Data Pipeline (GCP & Airflow)

Pipeline de Engenharia de Dados para ingestão, validação, processamento distribuído e modelagem analítica de avaliações de clientes (reviews) utilizando Apache Airflow, PySpark, Google Cloud Storage (GCS) e BigQuery.

---

## Arquitetura

O projeto adota a arquitetura de **Data Lakehouse em 3 camadas (Medallion)**:

```
[ Fontes de Dados ] (CSV / JSON / Mock Reviews)
         │
         ▼
[ Camada RAW ] (GCS / Parquet bruto com metadados de ingestão)
         │
         ▼
[ Data Quality / Validação ] (Schema, nulos, integridade e ranges)
         │
         ▼
[ PySpark Job ] (Limpeza, deduplicação e normalização)
         │
         ▼
[ Camada TRUSTED ] (GCS / Parquet particionado por ano/mês/dia)
         │
         ▼
[ Enriquecimento & Sentimento ] (Classificação léxica / VADER adaptado)
         │
         ▼
[ Camada CURATED ] (GCS / Parquet final para consumo analítico)
         │
         ▼
[ BigQuery ] (Data Warehouse - Star Schema com tabelas de Dimensão e Fato)
```

### Camadas de Armazenamento

| Camada | Formato | Particionamento | Propósito |
|---|---|---|---|
| **RAW** | Parquet | `ano/mês/dia` | Cópia fiel dos dados ingeridos, acrescida de timestamp e origem |
| **TRUSTED** | Parquet | `ano/mês/dia` | Dados limpos, deduplicados e com tipos estritamente validados |
| **CURATED** | Parquet | `ano/mês/dia` | Dados enriquecidos com score de sentimento, prontos para BI e Analytics |

---

## Modelo de Dados (BigQuery)

O Data Warehouse adota modelagem dimensional (**Star Schema**) no dataset `customer_experience`:

- **`dim_source`**: Cadastro de plataformas de origem (Google Reviews, TripAdvisor, Yelp, Email, Social).
- **`dim_location`**: Localização geográfica normalizada (cidade, estado, país).
- **`fact_reviews`**: Tabela fato contendo o texto tratado, avaliação, score e label de sentimento.
  - **Particionamento:** `review_date` (otimiza custo e varredura de dados).
  - **Clusterização:** `source_id, location_id, sentiment`.

Consultas analíticas prontas estão disponíveis em [`sql/analytics.sql`](sql/analytics.sql).

---

## Estrutura do Repositório

```
├── dags/
│   ├── customer_reviews_local_pipeline.py  # Pipeline local com LocalExecutor
│   └── customer_reviews_gcp_pipeline.py    # Pipeline integrado com GCS, Dataproc e BigQuery
├── ingestion/
│   └── ingest_reviews.py                   # Ingestão e escrita na camada RAW
├── transformations/
│   ├── clean_reviews.py                    # Limpeza, normalização e parsing
│   └── sentiment_analysis.py               # Análise de sentimento multilíngue
├── data_quality/
│   └── checks.py                           # Validações de schema, nulos e duplicatas
├── spark/
│   ├── transform_reviews.py                # PySpark Job de processamento batch
│   └── utils.py                            # Utilitários de sessão Spark
├── sql/
│   ├── create_dataset.sql                  # DDL de criação do dataset
│   ├── create_tables.sql                   # DDL das tabelas de dimensão e fato
│   ├── analytics.sql                       # Queries de negócio e KPIs
│   └── data_quality.sql                    # Queries de verificação no warehouse
├── scripts/
│   └── generate_sample_data.py             # Gerador determinístico de dados de teste
├── terraform/                              # Infraestrutura como Código (GCS + BigQuery)
├── tests/                                  # Suíte de testes unitários com pytest
├── docker-compose.yml                      # Setup do Airflow para execução local
└── Makefile                                # Automação de tarefas de desenvolvimento
```

---

## Como Executar Localmente

### Pré-requisitos
- Python 3.10+
- Docker e Docker Compose (caso deseje rodar a UI do Airflow)

### 1. Configurar o Ambiente
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt
```

### 2. Gerar Dados de Amostra
```bash
python3 scripts/generate_sample_data.py --num-records 10000
```

### 3. Rodar Testes
```bash
pytest tests/ -v
```

### 4. Orquestração com Airflow (Docker)
```bash
# Iniciar serviços (Airflow Webserver, Scheduler e Postgres)
docker compose up -d

# A interface web estará disponível em http://localhost:8080 (usuário: airflow, senha: airflow)

# Para encerrar os serviços
docker compose down
```

---

## Infraestrutura e Execução na Google Cloud Platform (GCP)

### 1. Provisionar Infraestrutura com Terraform
```bash
cd terraform
terraform init
terraform apply -var="project_id=SEU_PROJECT_ID"
```

### 2. Variáveis de Ambiente
Copie o arquivo de exemplo e preencha com as credenciais do seu projeto:
```bash
cp .env.example .env
```
Variáveis principais:
- `GCP_PROJECT_ID`: ID do projeto GCP
- `GCS_RAW_BUCKET`: Nome do bucket para a camada RAW
- `GCS_TRUSTED_BUCKET`: Nome do bucket para a camada TRUSTED
- `BIGQUERY_DATASET`: Dataset de destino (padrão: `customer_experience`)

---

## Autor

Desenvolvido por **Cesar Augusto**.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Perfil-blue?style=flat&logo=linkedin)](https://www.linkedin.com/in/cesaraugustooliveirarodrigues/)
[![GitHub](https://img.shields.io/badge/GitHub-Portfólio-darkgreen?style=flat&logo=github)](https://github.com/cesaraugustobr2014-oss)

---

## Licença

Distribuído sob a licença MIT. Consulte [`LICENSE`](LICENSE) para mais detalhes.
