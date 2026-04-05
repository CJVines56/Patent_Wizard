# Reingest Reference

Run all commands from repo root:

```powershell
Set-Location C:\Users\Optim\Patent_Wizard
```

## 1) Full Clean Reset (Weaviate + LMDB)

```powershell
# Stop Weaviate and remove container + volume
Set-Location backend\app
docker compose down -v
Set-Location ..\..

# Remove LMDB stores
Remove-Item -Recurse -Force backend\lmdb\*.lmdb -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force backend\lmdb\colbert_768_f16_shards -ErrorAction SilentlyContinue

# Optional: clear ingest tracking files
Remove-Item -Force backend\validation\master_patent_manifest.csv -ErrorAction SilentlyContinue
Remove-Item -Force backend\validation\ingest_completed_dates.txt -ErrorAction SilentlyContinue

# Restart Weaviate
Set-Location backend\app
docker compose up -d
Set-Location ..\..
```

## 2) Reingest (Default 768_f16 + PQ)

```powershell
$env:INGEST_MODE = "real-store"
$env:DROP_FIRST = "1"
$env:WRITE_LMDB = "1"

$env:TOKEN_VECTOR_DIM = "768"
$env:TOKEN_VECTOR_DTYPE = "float16"
$env:COLBERT_VARIANTS = "768_f16"
$env:LMDB_WRITE_VARIANTS = "768_f16"
$env:LMDB_SHARDING_MODE = "util"

$env:WEAVIATE_PQ_ENABLED = "1"
$env:WEAVIATE_PQ_CENTROIDS = "256"
$env:WEAVIATE_PQ_SEGMENTS = "0"
$env:WEAVIATE_PQ_TRAINING_LIMIT = "50000"

$env:INGEST_START_DATE = "2025-09-01"
$env:INGEST_WEEKS_BACK = "7"

poetry run python backend/app/test_connection.py
```

## 3) Evaluation Commands (L=400, R=200)

### Vector

```powershell
poetry run python backend/app/scripts/retrieve_rerank.py `
  --queries backend/validation/queries.jsonl `
  --qrels backend/validation/qrels.jsonl `
  --retrieve-shard 768_f16 `
  --rerank-shard 768_f16 `
  --limit 400 `
  --rerank-k 200 `
  --retrieval-mode vector `
  --metrics-csv backend/validation/metrics_l400_r200_vector.csv `
  --per-query-csv backend/validation/per_query_diagnostics_l400_r200_vector.csv `
  --per-query-top10-csv backend/validation/per_query_top10_l400_r200_vector.csv
```

### BM25

```powershell
poetry run python backend/app/scripts/retrieve_rerank.py `
  --queries backend/validation/queries.jsonl `
  --qrels backend/validation/qrels.jsonl `
  --retrieve-shard 768_f16 `
  --rerank-shard 768_f16 `
  --limit 400 `
  --rerank-k 200 `
  --retrieval-mode bm25 `
  --metrics-csv backend/validation/metrics_l400_r200_bm25.csv `
  --per-query-csv backend/validation/per_query_diagnostics_l400_r200_bm25.csv `
  --per-query-top10-csv backend/validation/per_query_top10_l400_r200_bm25.csv
```

### Hybrid (client-side fusion)

```powershell
$env:FORCE_CLIENT_HYBRID = "1"

poetry run python backend/app/scripts/retrieve_rerank.py `
  --queries backend/validation/queries.jsonl `
  --qrels backend/validation/qrels.jsonl `
  --retrieve-shard 768_f16 `
  --rerank-shard 768_f16 `
  --limit 400 `
  --rerank-k 200 `
  --retrieval-mode hybrid `
  --hybrid-alpha 0.2 `
  --metrics-csv backend/validation/metrics_l400_r200_hybrid_a02.csv `
  --per-query-csv backend/validation/per_query_diagnostics_l400_r200_hybrid_a02.csv `
  --per-query-top10-csv backend/validation/per_query_top10_l400_r200_hybrid_a02.csv
```

## Optional: Wrapper Script

```powershell
powershell -ExecutionPolicy Bypass -File backend/app/scripts/run_ingest_pipeline.ps1 `
  -StartDate "2025-09-01" `
  -WeeksBack 7 `
  -ResetWeaviate `
  -DropFirst `
  -CleanOutputs
```

