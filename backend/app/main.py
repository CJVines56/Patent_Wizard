from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .api.search import router as search_router
import logging
from starlette.responses import Response
import time
import json

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
