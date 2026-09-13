# Modelo de Dados

## Schema BigQuery

### Dataset: `customer_experience`

## Tabelas de Dimensão

### dim_source

Armazena as fontes de avaliações suportadas.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| source_id | INT64 | Identificador único da fonte (PK) |
| source_name | STRING | Nome da fonte (google_reviews, tripadvisor, yelp, email, social_media) |

**Exemplo de Dados:**
| source_id | source_name |
|-----------|-------------|
| 1 | google_reviews |
| 2 | tripadvisor |
| 3 | yelp |
| 4 | email |
| 5 | social_media |

### dim_location

Armazena informações de localização.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| location_id | INT64 | Identificador único de localização (PK) |
| city | STRING | Nome da cidade |
| state | STRING | Sigla do estado (ex: SP, RJ, MG) |
| country | STRING | Código do país (ex: BR) |

**Exemplo de Dados:**
| location_id | city | state | country |
|-------------|------|-------|---------|
| 1 | São Paulo | SP | BR |
| 2 | Rio de Janeiro | RJ | BR |
| 3 | Belo Horizonte | MG | BR |
| 4 | Salvador | BA | BR |

## Tabela Fato

### fact_reviews

Tabela principal contendo avaliações de clientes com análise de sentimentos.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| review_id | STRING | Identificador único da avaliação (PK) |
| customer_id | STRING | Identificador do cliente |
| source_id | INT64 | Chave estrangeira para dim_source |
| location_id | INT64 | Chave estrangeira para dim_location |
| rating | INT64 | Avaliação (1-5) |
| review_text | STRING | Texto da avaliação limpo |
| sentiment | STRING | Classificação de sentimento |
| sentiment_score | FLOAT64 | Score de sentimento (-1.0 a +1.0) |
| review_date | DATE | Data da avaliação |
| ingestion_timestamp | TIMESTAMP | Quando o registro foi ingestido |
| processing_timestamp | TIMESTAMP | Quando o registro foi processado |

**PARTICIONADA POR:** `review_date` (Diariamente)

**AGRUPADA POR:** `source_id`, `location_id`, `sentiment`

## Estratégia de Particionamento

O particionamento diário em `review_date` é ótimo porque:
- Consultas normalmente filtram por intervalo de data
- Permite exclusão eficiente de dados antigos
- Suporta analíticos baseados em tempo

## Estratégia de Agrupamento

O agrupamento em `source_id`, `location_id` e `sentiment` otimiza:
- Filtro por fonte (query mais comum)
- Filtro por localização
- Filtro por sentimento (para análise de sentimentos)

**Nota:** O agrupamento é opcional e depende dos padrões de query.

## Relacionamentos de Dados

**Relacionamentos:**
- `fact_reviews.source_id` → `dim_source.source_id`
- `fact_reviews.location_id` → `dim_location.location_id`

## Fluxo ETL

```
Dados de Entrada → Limpar → Validar → Transformar → Juntar Dimensões → Carregar no BigQuery
```

### Passo a Passo

1. **Entrada**: Avaliações CSV brutas
2. **Limpeza**: Remover duplicatas, tratar nulos, normalizar texto
3. **Validação**: Verificar ratings (1-5), fontes válidas, texto não vazio
4. **Transformação**: Criar sentimento, adicionar timestamps de processamento
5. ** lookup de Dimensões**:Obter source_id e location_id das tabelas de dimensão
6. **Carregamento**: Inserir na fact_reviews

## Métricas de Qualidade

| Métrica | Descrição | Limite |
|---------|-----------|--------|
| total_records | Total de registros processados | N/A |
| valid_records | Registros passando todas as validações | > 95% do total |
| invalid_ratings | Registros com ratings inválidos | < 1% do total |
| duplicate_records | review_ids duplicados | 0 |
| null_text | Registros com texto vazio | < 1% do total |
| sentiment_distribution | Proporção Positivo/Neutro/Negativo | Definido pelo negócio |

Consulte `sql/data_quality.sql` para consultas de validação.

## Consultas Analíticas

Consulte `sql/analytics.sql` para 10+ consultas como:
1. Contar avaliações por fonte
2. Sentimento por cidade
3. Distribuição geral de sentimento
4. Avaliação média por fonte
5. Distribuição de ratings
6. Sentimento ao longo do tempo (diário)
7. Cidades com mais sentimentos negativos
8. Correlação entre rating e sentimento
9. Tendência mensal
10. Contagem de avaliações por localização
