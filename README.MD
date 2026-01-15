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