# Documentação do Pipeline

## Visão Geral

O pipeline de avaliações de clientes processa feedbacks de clientes de múltiplas fontes, realiza validação e limpeza de dados, calcula sentimentos e carrega os resultados em um data warehouse para analíticos.

## Etapas do Pipeline

### 1. Geração de Dados (Opcional)

**Propósito:** Gerar dados sintéticos de amostra para testes

**Script:** `scripts/generate_sample_data.py`

**Comando:**
```bash
make generate-data
```

**Recursos:**
- Gera 10.000 avaliações
- Inclui problemas intencionais de qualidade de dados para testes
- Usa seed 42 para reprodutibilidade

**Saída:** `data/sample/reviews.csv`

---

### 2. Ingestão de Dados

**Propósito:** Ler avaliações de CSV e escrever na camada RAW

**Módulo:** `ingestion.ingest_reviews`

**Tarefas:**
- Ler arquivo CSV
- Adicionar metadados de ingestão
- Converter para formato Parquet
- Escrever na camada RAW (particionado)

**Saída:** `data/raw/reviews/ano=AAAA/mês=MM/dia=DD/*.parquet`

---

### 3. Validação de Dados

**Propósito:** Validar qualidade de dados antes da transformação

**Módulo:** `data_quality.checks`

**Verificações:**
- Validação de schema (colunas e tipos requeridos)
- Verificações de nulos (review_id, rating, texto)
- Validação de rating (faixa 1-5)
- Validação de fonte (apenas fontes suportadas)
- Detecção de duplicatas (por review_id)
- Detecção de texto vazio

**Saída:** Relatório de validação com métricas

---

### 4. Transformação de Dados

**Propósito:** Limpar e normalizar dados

**Módulo:** `transformations.clean_reviews`

**Transformações:**
- Limpeza de texto (remover espaços extras, normalizar espaços)
- Normalização de fonte (minúsculas, mapeamento)
- Normalização de cidade/estado/país
- Validação e conversão de rating
- Validação e formatação de datas
- Remoção de duplicatas

**Saída:** Dados limpos na camada TRUSTED

---

### 5. Análise de Sentimentos

**Propósito:** Classificar sentimentos de avaliações de clientes

**Módulo:** `transformations.sentiment_analysis`

**Método:** VADER (Valence Aware Dictionary for Sentiment Reasoning)

**Saída:**
- `sentiment`: POSITIVO, NEUTRO ou NEGATIVO
- `sentiment_score`: -1.0 a +1.0

**Fórmula:**
- POSITIVO: score ≥ 0.5
- NEUTRO: -0.5 < score < 0.5
- NEGATIVO: score ≤ -0.5

**Saída:** Dataset curado na camada CURATED

---

### 6. Carregamento de Dados

**Propósito:** Carregar dados no BigQuery

**Etapas:**
1. Carregar tabelas de dimensão (dim_source, dim_location)
2. Carregar tabela fato (fact_reviews)
3. Particionar por review_date
4. Agrupar por source_id, location_id, sentiment

**Ferramentas:**
- API BigQuery
- Operadores Google Cloud do Airflow
- PySpark (opcional para grandes conjuntos de dados)

---

## Estrutura do DAG Airflow

### Pipeline Local (`customer_reviews_local_pipeline.py`)

```
gerar_ou_detectar_entrada
    ↓
ingestion_avaliacoes
    ↓
validar_dados_brutos
    ↓
transformar_avaliacoes
    ↓
calcular_sentimento
    ↓
executar_verificações_de_qualidade
```

### Pipeline GCP (`customer_reviews_gcp_pipeline.py`)

```
gerar_ou_detectar_entrada
    ↓
upload_para_gcs_raw
    ↓
obter_bucket_gcs_raw
    ↓
criar_cluster_dataproc (opcional)
    ↓
executar_job_pyspark
    ↓
carregar_no_bigquery
    ↓
executar_verificacoes_bigquery
```

## Dependências de Tarefas

Todas as tarefas seguem um padrão sequencial:

1. Cada tarefa depende da tarefa anterior completar com sucesso
2. Tarefas podem ser reexecutadas independentemente (idempotentes)
3. Falhas disparam retentativas (até 3 vezes)

## Idempotência

Todas as tarefas são idempotentes:
- Podem ser reexecutadas várias vezes sem problemas
- Usam modo overwrite para escrita de arquivos
- BigQuery usa WRITE_TRUNCATE para carregamentos

## Tratamento de Erros

| Cenário | Ação |
|---------|------|
| Falha de tarefa | Retentar até 3 vezes com 5 minutos de atraso |
| Falha de validação | DAG falha imediatamente (fail-fast) |
| Problemas de qualidade de dados | Registrados, opcionalmente filtrados |
| Timeout de rede | Retentar com backoff exponencial |

## Monitoramento

### UI Airflow
- Execuções de DAG visíveis em `http://localhost:8080`
- Logs de tarefas acessíveis pela UI
- Histórico de execuções de DAG rastreado

### Logging
- Todas as tarefas logam para stdout
- Airflow armazena logs no diretório `logs/`
- Logs de tarefas falhadas disponíveis na UI

### Métricas
- Contagem de registros em cada etapa
- Contagem de falhas de validação
- Distribuição de sentimentos
- Tempo de processamento

## Desempenho

### Processamento Local
- 10.000 registros: ~1-2 minutos
- Uso de memória: ~500MB
- Uso de disco: ~50MB (RAW) + ~25MB (TRUSTED) + ~25MB (CURATED)

### Processamento GCP
- Pode escalar para milhões de registros
- Cluster Dataproc auto-escala
- BigQuery lida com grande volumes de dados eficientemente

## Otimização de Custo

### Local
- Grátis (roda na máquina local)

### GCP
- Use clusters Dataproc efêmeros
- Desligue clusters após conclusão do job
- Use particionamento e agrupamento no BigQuery para reduzir custos de varredura
- Habilite otimização de armazenamento BigQuery

## Solução de Problemas

### Problemas Comuns

1. **Arquivo não encontrado**
   - Certifique-se de rodar `make generate-data`
   - Verifique caminhos de arquivos no código

2. **Erro de escrita Parquet**
   - Certifique-se de ter espaço em disco suficiente
   - Verifique permissões de diretório

3. **Falhas de validação**
   - Verifique problemas de qualidade de dados nos dados de amostra
   - Revise regras de validação em `data_quality/checks.py`

4. **DAG Airflow travada**
   - Verifique logs Airflow: `docker compose logs -f`
   - Verifique se as dependências estão instaladas: `pip install -r requirements.txt`

5. **Timeout da análise de sentimentos**
   - VADER é rápido (< 1 segundo por 1000 registros)
   - Verifique se o conjunto de dados é muito grande para a memória local

## Extensões

### Processamento em Tempo Real
- Substituir entrada CSV por tópico Pub/Sub
- Usar Dataflow para streaming

### Analíticos Avançados
- Adicionar BERT/RoBERTa para sentimentos (requer mais recursos)
- Adicionar modelagem de tópicos para extração de problemas
- Adicionar NER para reconhecimento de entidades

### Implementação
- Usar Cloud Composer para Airflow gerenciado
- Usar Cloud Build para CI/CD
- Usar Artifact Registry para imagens de container

## Melhores Práticas

1. **Sempre valide dados de entrada** antes do processamento
2. **Registre todas as transformações** para rastreio de auditoria
3. **Use particionamento** para grandes conjuntos de dados
4. **Teste localmente** antes de implementar no GCP
5. **Monitore custos** ao usar serviços GCP
6. **Use IAM de menor privilégio** para service accounts
7. **Nunca commit secrets** para o Git
