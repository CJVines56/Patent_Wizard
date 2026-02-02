-------------API---------------
## Quick tests
🚀 How to Start the API (Development)

1. Open a terminal and go to the project folder

cd C:\Patent_Wizard


2. Activate the virtual environment

poetry shell


3. Start the API server

uvicorn backend.app.main:app --reload


4. Open in browser

API Docs: http://127.0.0.1:8000/docs

Health Check: http://127.0.0.1:8000/healthz

## Qrels evaluation API (TailScale)
This endpoint lets a teammate upload qrels/queries and run the rerank eval remotely.

Server setup (on your machine):
```powershell
$env:QRELS_API_KEY="WWg5_F3HfC0CXYUu8fVezCLn-eSSBO76ZIUefuh2rXg"
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Your TailScale IP:
```
100.103.151.117
```

Endpoint:
```
POST http://100.103.151.117:8000/api/qrels-eval
Header: X-API-Key: (the API key above)
```

Request (PowerShell on your friend's machine):
```powershell
$apiKey = "WWg5_F3HfC0CXYUu8fVezCLn-eSSBO76ZIUefuh2rXg"
$uri = "http://100.103.151.117:8000/api/qrels-eval"

Invoke-RestMethod -Uri $uri -Method Post -Headers @{ "X-API-Key" = $apiKey } `
  -Form @{
    qrels = Get-Item "C:\path\to\qrels.jsonl"
    # queries = Get-Item "C:\path\to\queries.jsonl"  # optional, will be derived if omitted
    shard = "768_f16"
    limit = 200
    rerank_k = 100
    filter_missing_qrels = "true"
  }
```

Request (curl):
```bash
curl -X POST "http://100.103.151.117:8000/api/qrels-eval" \
  -H "X-API-Key: WWg5_F3HfC0CXYUu8fVezCLn-eSSBO76ZIUefuh2rXg" \
  -F "qrels=@/path/to/qrels.jsonl" \
  -F "queries=@/path/to/queries.jsonl" \
  -F "shard=768_f16" \
  -F "limit=200" \
  -F "rerank_k=100" \
  -F "filter_missing_qrels=true"
```

Response includes:
- `metrics` JSON (precision/recall/ndcg/mrr)
- `metrics_csv` string (ready to save as a CSV file)

### 1) Health check
```bash
curl "http://localhost:8000/healthz"

should output

{"status":"ok"}

curl "http://localhost:8000/api/search?q=power&k=3"

should output below (pretty print enabled)

{
  "query": "power",
  "total": 2,
  "page": 1,
  "page_size": 3,
  "items": [
    {
      "id": 1,
      "title": "Electric Power Systems",
      "snippet": "Power flow, stability, protection."
    },
    {
      "id": 6,
      "title": "Power Electronics",
      "snippet": "Converters, PWM, and switching devices."
    }
  ],
  "mode": "basic",
  "answer": null
}

curl "http://localhost:8000/api/search?q=power&k=3&rag=true"

{
  "query": "power",
  "total": 2,
  "page": 1,
  "page_size": 3,
  "items": [
    {
      "id": 1,
      "title": "Electric Power Systems",
      "snippet": "Power flow, stability, protection."
    },
    {
      "id": 6,
      "title": "Power Electronics",
      "snippet": "Converters, PWM, and switching devices."
    }
  ],
  "mode": "rag",
  "answer": "(FAKE RAG) Proposed answer for: 'power'\n\nBased on the following 2 contexts:\n- Electric Power Systems: Power flow, stability, protection.\n- Power Electronics: Converters, PWM, and switching devices.\n\n(Note: This is a fake synthesized answer string for POC; plug your real LangChain orchestrator here later.)"
}



module purge
module load GCCcore/9.3.0 GCC/9.3.0 Python/3.8.2 CUDAcore/11.0.2 CUDA/11.0.2 cuDNN/8.0.5.39-CUDA-11.0.2

## GPU setup (Windows + Poetry)
PyTorch CUDA wheels are not available for Python 3.13+ yet. Use Python 3.12.

1) Install Python 3.12
- Download the Python 3.12.10 Windows installer from python.org.
- In the installer, check "Add python.exe to PATH".
- If Windows is intercepting `python`/`py`, disable App Execution Aliases for python.exe/python3.exe.

2) Point Poetry at Python 3.12
Replace the path with your install location:
```powershell
C:\Python312\python.exe -m poetry env use C:\Python312\python.exe
```

3) Recreate the Poetry env
```powershell
poetry env remove --all
poetry install
```

4) Install CUDA-enabled torch using pip (not Poetry)
Poetry cannot resolve CUDA wheels from the default index; install torch via pip inside the Poetry env:
```powershell
poetry run python -m pip install --upgrade pip
poetry run python -m pip install --index-url https://download.pytorch.org/whl/cu124 torch
```

5) Verify CUDA is active
```powershell
poetry run python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
```
Expected output example: `2.6.0+cu124 12.4 True`

## Multi-vector ColBERT + MUVERA (Weaviate 1.31+)
This project stores ColBERT token vectors as a multi-vector field and lets Weaviate apply MUVERA encoding at index time.
We now use two collections:
- `Patent` (metadata only)
- `Claim` (claims + vectors)

How it works
- `backend/app/embed.py` writes per-token vectors to `colbert` and keeps a mean-pooled `embedding` for preview/debug.
- `backend/app/store.py` configures a multi-vector named `colbert` with MUVERA encoding.
- Weaviate indexes the multi-vector field and applies MUVERA internally.

Important: recreate the collection after schema changes
If `Patent` / `Claim` already exist, Weaviate will not update the vector config. Delete and recreate once.

Steps
1) In `backend/app/test_connection.py`, set `DROP_FIRST = True` and run the script once.
2) Set `DROP_FIRST = False` and run the ingest again.

Notes
- Retrieval should use the `colbert` vector space on `Claim`.
- There is no separate `muvera` vector stored; MUVERA is an index-time encoding over the multi-vector input.

### Weaviate batching
`store.py` uses Weaviate batch inserts to reduce round‑trips. You can tune batch size with:
```powershell
$env:WEAVIATE_BATCH_SIZE="128"
```

### LMDB ColBERT storage (4 variants + auto-grow)
ColBERT token vectors are stored in LMDB for reranking. We write four variants in parallel:
- 768_f32
- 768_f16
- 128_f32
- 128_f16

Recommended env vars:
```powershell
$env:LMDB_MAP_GROW_GB="10"
$env:LMDB_MAP_SIZE="21474836480"
$env:LMDB_PATH_768_F32="backend/lmdb/colbert_768_f32.lmdb"
$env:LMDB_PATH_768_F16="backend/lmdb/colbert_768_f16.lmdb"
$env:LMDB_PATH_128_F32="backend/lmdb/colbert_128_f32.lmdb"
$env:LMDB_PATH_128_F16="backend/lmdb/colbert_128_f16.lmdb"
```

## Quick local workflow (Weaviate + ingest)
If you only have a few hours a week, use this quick checklist:

1) Start Weaviate from the repo’s compose file:
```powershell
cd backend\app
docker compose up -d
```

2) Run the ingest:
```powershell
poetry run python backend/app/test_connection.py
```

Tip: If you change the vector schema, set `DROP_FIRST = True` once, run the script, then set it back to `False`.

Troubleshooting Docker
- If you see `dockerDesktopLinuxEngine` pipe errors, Docker Desktop isn’t running. Open Docker Desktop and wait for “Docker Engine running”.
- Run `docker info` in a new terminal to confirm the engine is up before `docker compose up -d`.

## Use cases
- Search patents by claim text and retrieve the most semantically similar claims.
- Rerank Weaviate results with ColBERT MaxSim for higher precision.
- Compare reranked vs. raw retrieval results (export to CSV for side-by-side review).
- Build evaluation runs from queries/qrels JSONL to track relevance metrics.
- Export or share LMDB shards + Weaviate data for team collaboration and offline analysis.

## Step-by-step: correct model + ingest + retrieval
Use the same 768-dim ColBERT model for both ingest and query-time retrieval.

1) Start Weaviate
```powershell
cd backend\app
docker compose up -d
```

2) Force the same ColBERT model (important)
```powershell
$env:COLBERT_MODEL_NAME="colbert-ir/colbertv2.0"
$env:MODEL_NAME=$env:COLBERT_MODEL_NAME
```

3) (Optional) disable LMDB shard creation
```powershell
$env:WRITE_LMDB="0"
```

4) Ingest to Weaviate
```powershell
cd C:\Users\Optim\Patent_Wizard
poetry run python backend/app/test_connection.py
```

5) Run retrieval + rerank
```powershell
poetry run python backend/app/scripts/retrieve_rerank.py --query "transistor system" --shard 768_f16
```

6) Or use the GUI
```powershell
poetry run python backend/app/scripts/retrieve_rerank_gui.py
```

## Environment variables (INGEST_MODE)
`backend/app/test_connection.py` reads `INGEST_MODE` from the environment. If it’s unset, it defaults to `real-store`.

Set for current PowerShell session:
```powershell
$env:INGEST_MODE="real-store"   # or "export", "import", "fake"
```

Persist for your user:
```powershell
setx INGEST_MODE "real-store"
```

## Environment variables (embedding + storage)
```powershell
$env:TOKEN_VECTOR_DIM="768"          # primary variant for emb["colbert"] (768 or 128)
$env:TOKEN_VECTOR_DTYPE="float16"    # primary dtype for emb["colbert"]
$env:USE_TOKEN_PROJECTION="1"        # required when TOKEN_VECTOR_DIM=128
$env:COLBERT_VARIANTS="768_f32,768_f16,128_f32,128_f16"  # controls which LMDB shards are created
$env:COLBERT_MODEL_NAME="colbert-ir/colbertv2.0"  # keep ingest/query dimensions aligned (768)
$env:MODEL_NAME=$env:COLBERT_MODEL_NAME
$env:WRITE_LMDB="1"                  # set to "0" to skip LMDB shard writes
$env:WEAVIATE_BATCH_SIZE="128"
$env:LMDB_MAP_GROW_GB="10"
$env:LMDB_MAP_SIZE="21474836480"
$env:LMDB_PATH_768_F32="backend/lmdb/colbert_768_f32.lmdb"
$env:LMDB_PATH_768_F16="backend/lmdb/colbert_768_f16.lmdb"
$env:LMDB_PATH_128_F32="backend/lmdb/colbert_128_f32.lmdb"
$env:LMDB_PATH_128_F16="backend/lmdb/colbert_128_f16.lmdb"
```

Storage impact notes (dtype + dimensionality)
- float32 → float16: ~2× smaller (supported)
- 768 → 128 dims: ~6× smaller
- 768_f32 → 128_f16: ~12× smaller overall
- 768_f16 → 128_f16: ~6× smaller overall

We create multiple ColBERT variants to compare size/quality tradeoffs. Anything beyond these (e.g., int8/4‑bit) would require additional quantization not implemented here.

## Weaviate search (Claim collection)
Example GraphQL nearVector search using the dense query vector:
```powershell
curl http://localhost:8080/v1/graphql -H "Content-Type: application/json" -d "{\n  \"query\": \"{ Get { Claim(nearVector: {vector: [0.1, 0.2, 0.3]}, limit: 5) { claim_id doc_id claim_type text } } }\"\n}"
```
Generate a query vector with:
```python
from backend.app.embed import embed_query, tokenizer, model
qvec = embed_query("your query", tokenizer, model)[0].tolist()
```
PowerShell-friendly version:
```powershell
$body = @{ query = "{ Get { Claim(limit: 5) { claim_id doc_id claim_type text } } }" } | ConvertTo-Json
$resp = Invoke-WebRequest -Uri "http://localhost:8080/v1/graphql" -Method Post -Headers @{ "Content-Type" = "application/json" } -Body $body -UseBasicParsing
($resp.Content | ConvertFrom-Json).data.Get.Claim
```

## LMDB lookup + deserialization
```python
from backend.app.store import load_colbert_from_lmdb

# claim_uuid is the Weaviate Claim object UUID
vecs = load_colbert_from_lmdb("backend/lmdb/colbert_768_f16.lmdb", claim_uuid)
print(vecs.shape, vecs.dtype)  # [tokens, dim]
```

## Compact LMDB (reclaim unused map size)
LMDB does not shrink in place. Use the compact script to rewrite shards to their actual size:
```powershell
poetry run python backend/app/scripts/compact_lmdb.py --shard 768_f16
```
Or compact all shards:
```powershell
poetry run python backend/app/scripts/compact_lmdb.py --all
```

## Retrieval + reranking (with shard selection)
Run a query:
```powershell
poetry run python backend/app/scripts/retrieve_rerank.py --query "battery separator polymer" --shard 768_f16
```

Lookup by patent ID (doc_id):
```powershell
poetry run python backend/app/scripts/retrieve_rerank.py --doc-id 12406488
```

Evaluate metrics (JSONL inputs):
```powershell
poetry run python backend/app/scripts/retrieve_rerank.py --queries backend/validation/queries.jsonl --qrels backend/validation/qrels.jsonl --shard 768_f16
```
Expected JSONL formats:
```json
{"query":"battery separator polymer"}
{"query":"solid state electrolyte"}
```
```json
{"query":"battery separator polymer","relevant_claim_ids":["12406488-CLM-1","12403066-CLM-20"]}
{"query":"solid state electrolyte","relevant_claim_ids":["12403753-CLM-1"]}
```
