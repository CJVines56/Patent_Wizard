# Patent Wizard Backend: Strict 128-d ColBERT Pipeline

This backend is now hard-locked to:
- `TOKEN_VECTOR_DIM=128`
- `PROJECTION_MODE=trained`
- trained projection weights loaded from `PROJECTION_PATH`

There is no 768 fallback path and no random projection path.

## Required Environment Configuration

Set these before running ingest/retrieval:

```powershell
$env:TOKEN_VECTOR_DIM="128"
$env:PROJECTION_MODE="trained"
$env:PROJECTION_PATH="C:\path\to\trained_projection.pt"   # required
$env:TOKEN_VECTOR_DTYPE="float16"                         # float16 or float32
$env:COLBERT_VARIANTS="128_f16,128_f32"
$env:LMDB_WRITE_VARIANTS="128_f16"
$env:WEAVIATE_NAMED_VECTOR="colbert"
```

Validation happens at import/startup:
- projection file must exist
- projection matrix shape must be `[128,768]` or `[768,128]` (transposed explicitly)
- dtype must be float16 or float32
- any non-128 variant request raises immediately

## Ingest Logging

At embedding init/start, logs include:
- model checkpoint
- projection path
- projection shape
- final token dim (128)
- token dtype

## Weaviate Vector Export For Reranking

Rerank source options:
- `lmdb` (default)
- `weaviate`

New function:
- `fetch_colbert_vectors_from_weaviate(object_ids: list[str]) -> dict[str, np.ndarray]`

Exact API call used:
- Endpoint: `GET /v1/objects/Claim/{uuid}?include=vector`
- Base URL: `WEAVIATE_OBJECTS` (default `http://localhost:8080/v1/objects`)
- Expected response field: `vectors["colbert"]` (or configured `WEAVIATE_NAMED_VECTOR`)

Any missing vector / wrong named vector / empty vector / non-128 last dimension causes a hard error.

## Retrieval + Rerank Commands

### Vector retrieval + LMDB rerank

```powershell
poetry run python backend/app/scripts/retrieve_rerank.py `
  --query "battery separator polymer" `
  --retrieve-shard 128_f16 `
  --rerank-shard 128_f16 `
  --retrieval-mode vector `
  --limit 400 `
  --rerank-k 200 `
  --rerank-source lmdb
```

### Vector retrieval + Weaviate-vector rerank

```powershell
poetry run python backend/app/scripts/retrieve_rerank.py `
  --query "battery separator polymer" `
  --retrieve-shard 128_f16 `
  --rerank-shard 128_f16 `
  --retrieval-mode vector `
  --limit 400 `
  --rerank-k 200 `
  --rerank-source weaviate
```

### Qrels eval with Weaviate rerank source + vector debug compare

```powershell
poetry run python backend/app/scripts/retrieve_rerank.py `
  --queries backend/validation/queries.jsonl `
  --qrels backend/validation/qrels.jsonl `
  --retrieve-shard 128_f16 `
  --rerank-shard 128_f16 `
  --retrieval-mode vector `
  --limit 400 `
  --rerank-k 200 `
  --rerank-source weaviate `
  --debug-compare-vectors `
  --debug-compare-n 10 `
  --debug-compare-max-abs-tol 0.05 `
  --metrics-csv backend/validation/metrics_l400_r200.csv `
  --per-query-csv backend/validation/per_query_diagnostics_l400_r200.csv `
  --per-query-top10-csv backend/validation/per_query_top10_l400_r200.csv
```

## Smoke Test (Embed -> Insert -> Fetch vectors -> Rerank)

```powershell
poetry run python backend/app/scripts/smoke_weaviate_colbert_rerank.py --limit 50
```

This script verifies:
1. sample text embeds to token vectors with dim 128
2. sample claims are inserted into Weaviate
3. vectors are fetched back from Weaviate and reranking succeeds

## Ingest Runner (PowerShell)

`backend/app/scripts/run_ingest_pipeline.ps1` now enforces strict trained 128 config.

Example:

```powershell
$env:PROJECTION_PATH="C:\path\to\trained_projection.pt"
.\backend\app\scripts\run_ingest_pipeline.ps1 -DropFirst -ResetWeaviate -KeepAwake
```

## Master CLI Flag Reference

### `backend/app/scripts/retrieve_rerank.py`
- `--query`
- `--limit`
- `--rerank-k`
- `--retrieval-mode` (`vector|bm25|hybrid`)
- `--hybrid-alpha`
- `--save-before-csv`
- `--save-after-csv`
- `--save-k`
- `--retrieve-shard` (`128_f16|128_f32`)
- `--rerank-shard` (`128_f16|128_f32`)
- `--rerank-source` (`lmdb|weaviate`)
- `--debug-compare-vectors` / `--no-debug-compare-vectors`
- `--debug-compare-n`
- `--debug-compare-max-abs-tol`
- `--doc-id`
- `--queries`
- `--qrels`
- `--metrics-csv`
- `--per-query-csv`
- `--per-query-top10-csv`
- `--sweep-rerank-shards`
- `--sweep-csv`
- `--filter-missing-qrels` / `--no-filter-missing-qrels`

### `backend/app/scripts/backfill_weaviate_vectors_from_lmdb.py`
- `--shard` (`128_f16|128_f32`)
- `--batch-size`
- `--max-claims`
- `--timeout-s`
- `--progress-every`
- `--start-after`
- `--patch-workers`
- `--dry-run`
- `--strict`
- `--report-csv`

### `backend/app/scripts/compact_lmdb.py`
- `--shard` (`128_f16|128_f32|claim_payloads|patent_metadata`)
- `--all`

### `backend/app/scripts/smoke_weaviate_colbert_rerank.py`
- `--limit`

### `backend/app/scripts/convert_fig_images.py`
- positional `path` (optional; defaults to sample JSONL path)

### `backend/app/scripts/run_ingest_pipeline.ps1` parameters
- `-StartDate`
- `-WeeksBack`
- `-ResetWeaviate`
- `-DropFirst`
- `-CleanOutputs`
- `-KeepAwake`
- `-ManifestPath`
- `-CheckpointPath`

## API Notes

`POST /api/qrels-eval` now supports:
- `retrieve_shard` default `128_f16`
- `rerank_shard` default `128_f16`
- `rerank_source` (`lmdb` or `weaviate`)
- existing retrieval params (`retrieval_mode`, `hybrid_alpha`, `limit`, `rerank_k`, `filter_missing_qrels`)

