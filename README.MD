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

How it works
- `backend/app/embed.py` writes per-token vectors to `colbert` and keeps a mean-pooled `embedding` for preview/debug.
- `backend/app/store.py` configures a multi-vector named `colbert` with MUVERA encoding.
- Weaviate indexes the multi-vector field and applies MUVERA internally.

Important: recreate the collection after schema changes
If `PatentData` already exists, Weaviate will not update the vector config. Delete and recreate it once.

Steps
1) In `backend/app/test_connection.py`, set `DROP_FIRST = True` and run the script once.
2) Set `DROP_FIRST = False` and run the ingest again.

Notes
- Retrieval should use the `colbert` vector space.
- There is no separate `muvera` vector stored; MUVERA is an index-time encoding over the multi-vector input.
