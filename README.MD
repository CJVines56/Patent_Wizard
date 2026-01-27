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
$env:COLBERT_VARIANTS="768_f32,768_f16,128_f32,128_f16"
$env:WEAVIATE_BATCH_SIZE="128"
$env:LMDB_MAP_GROW_GB="10"
$env:LMDB_MAP_SIZE="21474836480"
$env:LMDB_PATH_768_F32="backend/lmdb/colbert_768_f32.lmdb"
$env:LMDB_PATH_768_F16="backend/lmdb/colbert_768_f16.lmdb"
$env:LMDB_PATH_128_F32="backend/lmdb/colbert_128_f32.lmdb"
$env:LMDB_PATH_128_F16="backend/lmdb/colbert_128_f16.lmdb"
```

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

## LMDB lookup + deserialization
```python
from backend.app.store import load_colbert_from_lmdb

# claim_uuid is the Weaviate Claim object UUID
vecs = load_colbert_from_lmdb("backend/lmdb/colbert_768_f16.lmdb", claim_uuid)
print(vecs.shape, vecs.dtype)  # [tokens, dim]
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
