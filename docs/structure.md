# Estrutura do Projeto

```
customer-experience-pipeline/
│
├── README.md                    # README principal
├── Makefile                     # Comandos de desenvolvimento
├── requirements.txt             # Dependências Python
├── requirements-test.txt        # Dependências de teste
├── docker-compose.yml           # Configuração Airflow Docker
├── .env.example                 # Template de variáveis de ambiente
├── .gitignore                   # Regras de ignorar Git
├── pytest.ini                   # Configuração Pytest
│
├── dags/                        # DAGs Apache Airflow
│   ├── __init__.py
│   ├── customer_reviews_local_pipeline.py    # DAG pipeline local
│   └── customer_reviews_gcp_pipeline.py      # DAG pipeline GCP
│
├── scripts/                     # Scripts utilitários
│   ├── __init__.py
│   └── generate_sample_data.py  # Gerador de dados amostra
│
├── ingestion/                   # Módulo de ingestão de dados
│   ├── __init__.py
│   └── ingest_reviews.py        # Ingestão CSV para Parquet
│
├── transformations/             # Transformações de dados
│   ├── __init__.py
│   ├── clean_reviews.py         # Limpeza de dados
│   └── sentiment_analysis.py    # Análise de sentimentos VADER
│
├── spark/                       # Jobs Spark
│   ├── __init__.py
│   ├── transform_reviews.py     # Job de transformação PySpark
│   └── utils.py                 # Utilitários de sessão Spark
│
├── data_quality/                # Verificações de qualidade de dados
│   ├── __init__.py
│   └── checks.py                # Funções de validação
│
├── sql/                         # Scripts SQL
│   ├── create_dataset.sql       # Criação de dataset BigQuery
│   ├── create_tables.sql        # DDL de tabelas
│   ├── data_quality.sql         # Consultas de verificação de qualidade
│   └── analytics.sql            # Consultas analíticas de negócios
│
├── data/                        # Diretório de dados (GITIGNORED)
│   ├── sample/                  # Dados amostra gerados
│   ├── raw/                     # Camada RAW (Parquet)
│   ├── trusted/                 # Camada TRUSTED (Parquet)
│   └── curated/                 # Camada CURATED (Parquet)
│
├── tests/                       # Testes unitários
│   ├── __init__.py
│   ├── conftest.py              # Fixtures Pytest
│   ├── test_ingestion.py        # Testes de ingestão
│   ├── test_transformations.py  # Testes de transformação
│   ├── test_sentiment.py        # Testes de análise de sentimentos
│   ├── test_data_quality.py     # Testes de qualidade de dados
│   └── test_spark.py            # Testes de job Spark
│
├── terraform/                   # Infrastructure as Code
│   ├── main.tf                  # Configuração Terraform
│   ├── variables.tf             # Variáveis de entrada
│   ├── outputs.tf               # Variáveis de saída
│   ├── storage.tf               # Buckets GCS
│   ├── bigquery.tf              |# Recursos BigQuery
│   └── README.md                # Documentação Terraform
│
├── docs/                        # Documentação do projeto
│   ├── architecture.md
│   ├── data_model.md
│   ├── pipeline.md
│   └── images/
│
└── .github/                     # Workflows GitHub
    └── workflows/
        └── tests.yml            # Pipeline CI/CD
```

## Propósito dos Diretórios

| Diretório | Propósito |
|-----------|-----------|
| `dags/` | Definições DAGs do Airflow |
| `scripts/` | Scripts Python autônomos |
| `ingestion/` | Módulo de ingestão de dados |
| `transformations/` | Limpeza e transformação de dados |
| `spark/` | Jobs PySpark |
| `data_quality/` | Verificações de validação de dados |
| `sql/` | Scripts SQL para BigQuery |
| `data/` | Arquivos de dados gerados |
| `tests/` | Testes unitários |
| `terraform/` | Código de infraestrutura GCP |
| `docs/` | Documentação |

## Camadas de Dados

| Camada | Descrição | Formato |
|--------|-----------|---------|
| **sample/** | Dados amostra gerados | CSV |
| **raw/** | Dados de entrada (como estão) | Parquet (particionado) |
| **trusted/** | Dados limpos | Parquet (particionado) |
| **curated/** | Dados prontos para negócios | Parquet |

## Variáveis de Ambiente

Veja `.env.example` para lista completa.

Variáveis principais:
- `GCP_PROJECT_ID`: ID do seu projeto GCP
- `GCP_REGION`: Região GCP (padrão: us-central1)
- `GCS_RAW_BUCKET`: Nome do bucket para camada RAW
- `BIGQUERY_DATASET`: ID do dataset BigQuery
- `GOOGLE_APPLICATION_CREDENTIALS`: Caminho para JSON de service account
