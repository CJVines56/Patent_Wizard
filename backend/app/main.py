from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from dotenv import load_dotenv
import logging
from starlette.responses import Response
import time
import json
import os


def _clear_dead_local_proxy_env() -> None:
    """
    Some local sessions export a "blackhole" proxy (127.0.0.1:9) which breaks
    outbound LLM/LangSmith calls. Remove it before importing orchestrator code.
    """
    proxy_keys = [
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ]
    for key in proxy_keys:
        value = (os.environ.get(key) or "").strip().lower()
        if "127.0.0.1:9" in value:
            os.environ.pop(key, None)


_clear_dead_local_proxy_env()

# Load orchestrator env before importing graph/nodes (Gemini clients initialize at import time).
_ORCH_DIR = Path(__file__).resolve().parents[1] / "orchestrator"
load_dotenv(_ORCH_DIR / ".env")
load_dotenv(_ORCH_DIR / "env")

from .api.search import router as search_router
from .api.eval import router as eval_router
from backend.orchestrator.graph import compile_graph

app = FastAPI(title="Patent Miner API (POC)", version="0.1.0")
#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger("api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev
        "http://localhost:3000",  # CRA dev
        # add your deployed frontend origin when ready
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)
app.include_router(eval_router)

@app.on_event("startup")
def build_graph_on_startup():
    app.state.graph = compile_graph(print_mermaid=False)
'''
@app.middleware("http")
async def request_logger(request: Request, call_next):
    """
    Logs one JSON line per request:
    - method/path
    - q/k/rag (safe-truncated)
    - status code
    - latency in ms
    """
    t0 = time.perf_counter()

    # read the query params you care about (truncate q to keep logs small)
    qp = request.query_params
    q  = (qp.get("q") or "")[:120]
    k  = qp.get("k")
    rag = qp.get("rag")

    method = request.method
    path = request.url.path
    ua = request.headers.get("user-agent", "")[:160]
    client_ip = getattr(request.client, "host", None)

    try:
        response: Response = await call_next(request)   # hand off to your route
        return response
    except Exception as e:
        # log unexpected exceptions with stack trace
        logger.exception(json.dumps({
            "event": "http_exception",
            "method": method, "path": path,
            "q": q, "k": k, "rag": rag,
            "client_ip": client_ip,
            "user_agent": ua,
            "error": repr(e),
        }))
        raise
    finally:
        # always log the request outcome
        ms = (time.perf_counter() - t0) * 1000.0
        status = response.status_code if "response" in locals() else 500
        logger.info(json.dumps({
            "event": "http_request",
            "method": method, "path": path,
            "q": q, "k": k, "rag": rag,
            "status": status,
            "ms": round(ms, 1),
            "client_ip": client_ip,
            "user_agent": ua,
        }))
'''
@app.get("/healthz")
def healthz():
    return {"status": "ok"}
