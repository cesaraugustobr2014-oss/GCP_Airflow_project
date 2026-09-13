# Pipeline de Experiência do Cliente

Pipeline de Engenharia de Dados End-to-End usando Apache Airflow, Spark, Google Cloud Storage e BigQuery

## Visão Geral

Este projeto demonstra um **Pipeline de Experiência do Cliente** em nível de produção, construído para analisar avaliações de clientes em múltiplas fontes (Google Reviews, TripAdvisor, Yelp, Email, Redes Sociais).

O pipeline implementa uma **arquitetura de data lake em 3 camadas** (RAW → TRUSTED → CURATED) com:

- ✅ **Ingestão de dados** de CSV/JSON
- ✅ **Validação de dados** e verificações de qualidade
- ✅ **Transformação de dados** com PySpark
- ✅ **Análise de sentimentos** usando VADER
- ✅ **Orquestração** com Apache Airflow
- ✅ **Data Warehouse** no BigQuery
- ✅ **Infraestrutura como Código** com Terraform

---

## 🎯 Foco do Projeto

**Este é principalmente um projeto de ENGENHARIA DE DADOS, NÃO um projeto de Machine Learning.**

Embora a análise de sentimentos (VADER) esteja incluída, o valor central está em demonstrar:

- 📦 **Processos ETL/ELT** para grandes volumes de dados
- 🧹 **Limpeza e normalização de dados**
- 🛡️ **Aplicação de qualidade de dados**
- 🔄 **Orquestração de pipelines**
- 📊 **Modelagem de data warehouse**
- ☁️ **Arquitetura em nuvem (GCP)**
- 🧪 **Testes e observabilidade**

---

## 📊 Arquitetura

```
FONTES DE DADOS → INGESTÃO → RAW (GCS) → VALIDAÇÃO → TRANSFORMAÇÃO (Spark)
                                         ↓
                                   TRUSTED (GCS) → SENTIMENTO → CURATED (GCS)
                                         ↓
                                    BIGQUERY → ANALÍTICOS & DASHBOARDS
```

### Camadas do Data Lake

| Camada | Descrição | Formato |
|--------|-----------|---------|
| **RAW** | Dados originais (como ingestão) | Parquet ( particionado) |
| **TRUSTED** | Dados limpos e validados | Parquet (particionado) |
| **CURATED** | Dados prontos para negócios | Parquet |

---

## 🛠️ Tech Stack

| Camada | Tecnologia |
|--------|------------|
| Orquestração | Apache Airflow |
| Processamento | PySpark / Dataproc |
| Armazenamento | Google Cloud Storage (Data Lake) |
| Warehouse | BigQuery |
| Sentimento | VADER (NLTK) |
| Qualidade | Verificações customizadas |
| Infraestrutura | Terraform |
| Containerização | Docker |

---

## 🚀 Guia Rápido

### Pré-requisitos

- Python 3.10+
- Docker e Docker Compose (opcional, para Airflow)
- Conta GCP (opcional, para demo em nuvem)

### Passo 1: Instalar Dependências

```bash
cd /home/cesar/GCP_projects/customer-experience

# Instalar dependências Python
make setup

# Ou manualmente:
pip install -r requirements.txt
```

### Passo 2: Gerar Dados de Amostra

```bash
# Gerar 10.000 avaliações sintéticas
make generate-data

# Ou executar diretamente:
python scripts/generate_sample_data.py
```

### Passo 3: Executar Testes

```bash
# Executar todos os testes
make test

# Executar com cobertura
make test-coverage
```

### Passo 4: Executar Airflow (Opcional)

```bash
# Iniciar Airflow com Docker Compose
make airflow-up

# Acessar UI em http://localhost:8080
# Usuário: airflow
# Senha: airflow

# Parar quando terminar
make airflow-down
```

---

## 📂 Estrutura do Projeto

```
customer-experience-pipeline/
├── dags/                 # DAGs do Apache Airflow
├── scripts/             # Scripts utilitários
├── ingestion/           # Módulo de ingestão de dados
├── transformations/     # Limpeza e análise de sentimentos
├── spark/               # Jobs PySpark
├── data_quality/        # Verificações de qualidade de dados
├── sql/                 # Scripts SQL (BigQuery)
├── data/                # Dados gerados (GITIGNORED)
│   ├── sample/          # Dados brutos amostra
│   ├── raw/             # Camada RAW (Parquet)
│   ├── trusted/         # Camada TRUSTED (Parquet)
│   └── curated/         # Camada CURATED (Parquet)
├── tests/               # Testes unitários
├── terraform/           # Infraestrutura como Código
├── docs/                # Documentação
├── docker-compose.yml   # Configuração Airflow
├── Makefile             # Comandos de desenvolvimento
└── requirements.txt     # Dependências Python
```

---

## 📈 Etapas do Pipeline

1. **Geração de Dados** → Gerar avaliações sintéticas com problemas de qualidade
2. **Ingestão de Dados** → Ler CSV, escrever na camada RAW (Parquet)
3. **Validação de Dados** → Schema, nulos, faixas, duplicados
4. **Transformação de Dados** → Limpar, normalizar, deduplicar (PySpark)
5. **Análise de Sentimentos** → Classificação VADER (POSITIVO/NEUTRAL/NEGATIVO)
6. **Carregamento de Dados** → Criar dimensões, carregar no BigQuery

---

## 🎨 Modelo de Dados

### Schema BigQuery

**Dataset:** `customer_experience`

| Tabela | Descrição |
|--------|-----------|
| `dim_source` | Dimensão de fontes (google_reviews, tripadvisor, etc.) |
| `dim_location` | Dimensão de localização (cidade, estado, país) |
| `fact_reviews` | Tabela fato com avaliações e sentimentos |

**Tabela Fato PARTICIONADA POR:** `review_date`  
**Tabela Fato AGRUPADA POR:** `source_id, location_id, sentiment`

---

## ❓ Exemplos de Consultas Analíticas

```sql
-- 1. Contar avaliações por fonte
SELECT source, COUNT(*) as review_count
FROM customer_experience.fact_reviews
GROUP BY source
ORDER BY review_count DESC;

-- 2. Sentimento por cidade
SELECT city, sentiment, COUNT(*) as count
FROM customer_experience.fact_reviews
GROUP BY city, sentiment
ORDER BY city, count DESC;

-- 3. Percentual de sentimento negativo
SELECT 
  ROUND(SUM(CASE WHEN sentiment = 'NEGATIVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as negative_percentage
FROM customer_experience.fact_reviews;
```

Veja `sql/analytics.sql` para 10+ consultas.

---

## 🧪 Qualidade de Dados

O dataset sintético inclui intencionalmente problemas para demonstrar verificações de qualidade:

| Problema | Porcentagem | Descrição |
|----------|-------------|-----------|
| Duplicatas | ~1% | Mesmo review_id |
| Texto nulo | ~0.5% | Faltando texto de avaliação |
| Ratings inválidos | ~1% | Fora do intervalo 1-5 |
| Cidade ausente | ~1% | Cidade não fornecida |
| Formatos inconsistentes | ~1% | Caixa mista em nomes de fontes |

Execute `make generate-data && python scripts/data_quality.py` para ver todas as verificações.

---

## ☁️ Integração Google Cloud

### Pré-requisitos

1. **Criar Projeto GCP** e ativar APIs:
   ```bash
   gcloud services enable storage.googleapis.com
   gcloud services enable bigquery.googleapis.com
   ```

2. **Autenticar**:
   ```bash
   gcloud auth application-default login
   ```

3. **Configurar** `.env`:
   ```bash
   cp .env.example .env
   # Editar .env com detalhes do seu projeto GCP
   ```

4. **Provisionar Infraestrutura** (Terraform):
   ```bash
   cd terraform
   terraform init
   terraform apply -var="project_id=SEU_PROJECT_ID"
   ```

---

## 📝 Configuração BigQuery

### Criar Dataset

```bash
bq --project_id=SEU_PROJECT_ID mk --dataset customer_experience
```

### Criar Tabelas

```bash
bq --project_id=SEU_PROJECT_ID query --use_legacy_sql=false < sql/create_tables.sql
```

### Carregar Dados

```bash
bq --project_id=SEU_PROJECT_ID load \
  --source_format=PARQUET \
  customer_experience.reviews \
  gs://seu-bucket/curated/customer_sentiment/*.parquet
```

---

## 🧪 Testes

```bash
# Executar todos os testes
make test

# Executar arquivo específico
pytest tests/test_ingestion.py -v

# Executar com cobertura
make test-coverage

# Executar linting
make lint
```

---

## 🛠️ Comandos de Desenvolvimento

| Comando | Descrição |
|---------|-----------|
| `make setup` | Instalar dependências |
| `make generate-data` | Gerar dados de amostra |
| `make test` | Executar todos os testes |
| `make test-coverage` | Executar testes com cobertura |
| `make lint` | Executar verificações de lint |
| `make format` | Formatar código com black |
| `make airflow-up` | Iniciar Airflow com Docker |
| `make airflow-down` | Parar Airflow |
| `make clean` | Remover arquivos gerados |

---

## 📊 Considerações de Custo

### Desenvolvimento Local

- **Custo:** R$ 0 (roda na máquina local)

### Uso GCP

- **Cloud Storage:** 5GB gratuito
- **BigQuery:** 10GB gratuitos/mês de consulta, 1TB de armazenamento
- **Dataproc:** Pay-per-use, use clusters efêmeros

**Custo Mensal Estimado:**
- Desenvolvimento: R$ 0
- Produção pequena (diário, 10k registros): < R$ 20
- Produção média (horário, 1M registros): R$ 70-180

---

## 📚 Documentação

| Documento | Descrição |
|-----------|-----------|
| `README.md` | Este arquivo |
| `docs/architecture.md` | Arquitetura técnica |
| `docs/data_model.md` | Schema do banco de dados |
| `docs/pipeline.md` | Detalhes do pipeline |
| `docs/structure.md` | Estrutura de diretórios |

---

## 🚢 Implementação

### AWS (Alternativa)

- Substituir GCS por **S3**
- Substituir BigQuery por **Redshift** ou **Athena**
- Usar **MWAA** em vez de Airflow

### Azure (Alternativa)

- Substituir GCS por **Azure Data Lake**
- Substituir BigQuery por **Azure Synapse**
- Usar **Azure Data Factory**

---

## 🎓 Lições Aprendidas

Este projeto demonstra:

1. **Disiplina de Engenharia de Dados** → Camadas adequadas, validação, monitoramento
2. **Escalabilidade** → Processamento baseado em Spark lida com milhões de registros
3. **Observabilidade** → Métricas e logs claros em todo o pipeline
4. **Reprodutibilidade** → Geração de dados determinística com seed fixo
5. **Pronto para produção** → IaC, testes, CI/CD, documentação

---

## 📜 Licença

Licença MIT - Veja [LICENSE](LICENSE) para detalhes.

---

## 🤝 Contribuindo

Este é um projeto de portfólio. Sinta-se livre para explorar e usar como referência.

---

## 📞 Contato

Para dúvidas ou feedback, abra uma issue no GitHub.
