# Patent Wizard Local Runbook

This README is for the current local prototype on Christian's Windows machine, not a generic clean-room setup.

## Local Assumptions

- Repo root: `C:\ECEN_403\Patent_Wizard`
- Shell used in practice: `Git Bash`
- Python/dependencies: `Poetry`
- Frontend: Vite/React in `frontend`
- Backend: FastAPI in `backend/app`
- Vector DB: local Weaviate in Docker on `localhost:8081` HTTP and `localhost:50052` gRPC
- Search model: local ColBERTv2 snapshot in the Hugging Face cache
- Projection checkpoint: repo-local prototype 128-d projection
- GPU path, when configured correctly: `NVIDIA RTX A2000 Laptop GPU`

## Current Local Model + Projection

The backend is already set up to use the local ColBERT snapshot automatically.

Expected local model snapshot:

```text
C:\Users\Christian Casteel\.cache\huggingface\hub\models--colbert-ir--colbertv2.0\snapshots\c1e84128e85ef755c096a95bdb06b47793b13acf
```

Expected projection checkpoint:

```text
backend/app/checkpoints/colbertv2_prototype_128x768.pt
```

The orchestrator env file already points at the prototype projection:

- [env](/mnt/c/ECEN_403/Patent_Wizard/backend/orchestrator/env)

Important:

- this branch is 128-d only
- the projection is a local prototype checkpoint, not the original trained projection
- `LOCAL_MODEL_ONLY=1` is enabled, so the backend should prefer local assets instead of redownloading

## Daily Startup

Normal local startup is three things:

1. Start Docker Desktop and make sure the Weaviate container is up
2. Start the frontend
3. Start the backend

Frontend:

```bash
cd frontend
npm run dev
```

Backend, from repo root:

```bash
poetry run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Open:

```text
http://localhost:5173/
```

## Quick Health Checks

Backend health:

```bash
curl http://localhost:8000/healthz
```

Direct API search:

```bash
curl "http://localhost:8000/api/search?q=golf%20club&rag=false"
```

CLI retrieval sanity check:

```bash
poetry run python backend/app/scripts/retrieve_rerank.py --query "golf club" --retrieve-shard 128_f16 --rerank-shard 128_f16 --retrieval-mode vector --limit 20 --rerank-k 10 --rerank-source lmdb
```

## One-Time Poetry Setup

From repo root:

```bash
poetry install
```

This repo expects Python `>=3.11,<3.15` per [pyproject.toml](/mnt/c/ECEN_403/Patent_Wizard/pyproject.toml).

## CUDA / GPU Notes

If Poetry resolves a CPU-only Torch build, the backend still works, but embeddings and query encoding will be slower.

The known-good CUDA replacement flow on this machine was:

```bash
poetry run python -m pip uninstall -y torch
poetry run python -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu126 torch==2.11.0+cu126
```

Verify:

```bash
poetry run python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')"
```

Expected successful output includes:

- `2.11.0+cu126`
- `True`
- `NVIDIA RTX A2000 Laptop GPU`

## How Search Interfaces Work

Runtime path:

```text
Frontend -> FastAPI /api/search -> orchestrator/retriever -> Weaviate + LMDB + local ColBERT model
```

Important files:

- Frontend API caller: [api.js](/mnt/c/ECEN_403/Patent_Wizard/frontend/src/lib/api.js)
- Frontend results page: [Results.jsx](/mnt/c/ECEN_403/Patent_Wizard/frontend/src/Results.jsx)
- FastAPI app: [main.py](/mnt/c/ECEN_403/Patent_Wizard/backend/app/main.py)
- Search API route: [search.py](/mnt/c/ECEN_403/Patent_Wizard/backend/app/api/search.py)
- Graph/RAG workflow: [graph.py](/mnt/c/ECEN_403/Patent_Wizard/backend/orchestrator/graph.py)
- Retrieval + rerank tool: [tools.py](/mnt/c/ECEN_403/Patent_Wizard/backend/orchestrator/tools.py)
- Embedding/model loader: [embed.py](/mnt/c/ECEN_403/Patent_Wizard/backend/app/embed.py)
- Storage layer: [store.py](/mnt/c/ECEN_403/Patent_Wizard/backend/app/store.py)

Ingest path:

```text
USPTO bulk archive -> download.py parse/chunk -> embed.py -> store.py -> Weaviate + LMDB
```

Important ingest files:

- Ingest runner: [run_ingest_pipeline.ps1](/mnt/c/ECEN_403/Patent_Wizard/backend/app/scripts/run_ingest_pipeline.ps1)
- Main ingest script: [test_connection.py](/mnt/c/ECEN_403/Patent_Wizard/backend/app/test_connection.py)
- USPTO parser/downloader: [download.py](/mnt/c/ECEN_403/Patent_Wizard/backend/app/services/download.py)

## Local Data Stores

Weaviate stores:

- claim vectors for retrieval
- patent and claim collections

LMDB stores:

- claim payloads
- patent metadata
- ColBERT token vectors for reranking

Patent metadata note:

- WIP patent-search results read patent metadata from LMDB, not raw XML or the CSV manifest
- patent abstracts only appear in patent-mode results if `abstract_text` was persisted during ingest
- older local datasets may be missing that field even though the parser extracted the abstract at parse time
- if patent-mode results are missing abstracts, reingest or backfill patent metadata

Cached USPTO weekly archives currently live in the repo root, for example:

- `I20250902.tar`
- `I20200804.tar`
- `I20190108.tar`
- `I20200421.tar`

Once a dataset archive is downloaded, later ingests should reuse the local file instead of downloading it again.

## Current Search Behavior

Current frontend defaults:

- Filters tab: hidden
- Dev tuning panel: hidden

Those UI pieces were hidden, not deleted, so they can be re-enabled later in:

- [Results.jsx](/mnt/c/ECEN_403/Patent_Wizard/frontend/src/Results.jsx)
- [devTuning.js](/mnt/c/ECEN_403/Patent_Wizard/frontend/src/lib/devTuning.js)

Search API notes:

- `rag=true` uses the graph path when possible
- `rag=false` uses direct retrieval
- result count is now requested dynamically from the API instead of being stuck at the old backend default of `5`
- the frontend now exposes two search scopes:
  `claim` search is the original behavior and returns claim-level hits
  `patent` search is WIP and still retrieves claims underneath, then collapses results to one hit per `doc_id`
- in patent mode, a patent's rank is determined by its highest-ranked claim
- patent mode currently uses direct retrieval only, not the RAG graph path
- patent-mode snippets prefer stored patent `abstract_text`; if that metadata is missing, the UI falls back to claim text

## Date Semantics

Current `filing_date` means the patent's application filing date, not the grant issue date or weekly dataset date.

The parser reads it from:

- `application-reference/document-id/date`

So a patent in a 2025 grant dataset can still have a much older filing date. That is expected with the current schema.

If you need grant-date filtering later, the code will need a separate stored field for publication/grant date.

## Local RAG / API Keys

RAG answer generation uses `ChatOpenAI(...)` against the TAMU-compatible OpenAI endpoint configured in:

- [env](/mnt/c/ECEN_403/Patent_Wizard/backend/orchestrator/env)

Current key fields:

```text
OPENAI_BASE_URL=https://chat-api.tamu.ai/openai
OPENAI_API_KEY=
LANGSMITH_API_KEY=
```

Important distinction:

- `OPENAI_API_KEY` is for actual model calls
- `LANGSMITH_API_KEY` is only for tracing/logging

If you change these values, restart the backend.

## Clean Reingest Examples

Clean rebuild of the 4 specific patents used during local validation:

```bash
powershell.exe -ExecutionPolicy Bypass -File backend/app/scripts/run_ingest_pipeline.ps1 \
  -IngestDates "2020-08-04,2009-01-13,2017-09-12,2006-06-06" \
  -TargetDocIds "10735320,7477657,9762397,7058973" \
  -DropFirst \
  -CleanOutputs
```

Append patents from the recent 2025 dataset:

```bash
powershell.exe -ExecutionPolicy Bypass -File backend/app/scripts/run_ingest_pipeline.ps1 \
  -IngestDates "2025-09-02" \
  -MaxPatents 3000
```

Target just specific patents across different weekly datasets:

```bash
powershell.exe -ExecutionPolicy Bypass -File backend/app/scripts/run_ingest_pipeline.ps1 \
  -IngestDates "2020-04-21,2019-01-08" \
  -TargetDocIds "10630505,10177957"
```

Do not use `-ResetWeaviate` unless you know port `8081` is free on this machine. The known safer local reset path here has been `-DropFirst -CleanOutputs`.

## Retrieval Example

Example query that successfully surfaced a target patent and its prior art locally:

```bash
poetry run python backend/app/scripts/retrieve_rerank.py --query "multiprotocal label switching system network" --retrieve-shard 128_f16 --rerank-shard 128_f16 --retrieval-mode vector --limit 20 --rerank-k 10 --rerank-source lmdb
```

## Practical Troubleshooting

If the frontend falls back to mock data:

- make sure backend is running on `localhost:8000`
- make sure Weaviate is running on `localhost:8081`
- verify with:

```bash
curl http://localhost:8000/healthz
curl "http://localhost:8000/api/search?q=golf%20club&rag=false"
```

If embeddings fail:

- confirm Poetry env is active
- confirm CUDA Torch is installed if you expect GPU usage
- confirm local model snapshot still exists at the expected path
- confirm [env](/mnt/c/ECEN_403/Patent_Wizard/backend/orchestrator/env) still points at the prototype projection

If filters seem confusing:

- current date filtering is filing-date based
- `author` and `classification` are not fully server-backed yet
- result replacement is implemented for the server-backed filters, not the frontend-only ones
