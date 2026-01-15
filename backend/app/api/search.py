from fastapi import APIRouter, Query  # Router groups related endpoints; Query validates URL params
from typing import Dict, Any #Typing hints
from ..models.search import SearchResponse
from ..services.retrieval import naive_filter, first_k
from ..services.orchestrator_fake import make_fake_answer

router = APIRouter(prefix="/api", tags=["search"])  # All routes here start with /api
'''curl "http://localhost:8000/healthz"
curl "http://localhost:8000/api/search?q=power&k=3"
curl "http://localhost:8000/api/search?q=power&k=3&rag=true"'''
#navigate to Patent_Wizard folder in terminal, activate venv, then proceed below
#To start api server, run "uvicorn backend.app.main:app --reload" in terminal from the Patent_Wizard folder
#Tests defined in README.md

@router.get("/search", response_model=SearchResponse)  # GET /api/search
async def search(
    q: str = Query("", description="User query string"),                # ?q=...
    k: int = Query(5, ge=1, le=50, description="Top-k results to return"), # cited items count
    k_extra: int = Query(5, ge=0, le=100, description="Additional non-cited results to include"),
    rag: bool = Query(True, description="If true, synthesize a fake RAG answer"), # default to RAG mode
):
    # 1) Retrieve (filter only), preserve source order
    items = naive_filter(q)           # token substring match against title/snippet
    top = first_k(items, k)           # take first k as cited items (fed to LLM)

    # Simple page framing around the top-k slice for POC
    page = 1                          # single-page POC
    page_size = k                     # page size equals k for now
    total = len(items)                # total matches before slicing

    # Non-cited results for the sidebar below "Cited Patents"
    others = items[k: k + k_extra] if k_extra else []

    if not rag:
        return SearchResponse(
            query=q,
            total=total,
            page=page,
            page_size=page_size,
            items=top,
            cited_items=top,
            other_items=others,
            mode="basic",
            answer=None,
        )

    # 2) "RAG mode" — but we fake the orchestrator's answer locally
    contexts: list[Dict[str, Any]] = [
        {"id": it.id, "title": it.title, "snippet": it.snippet}
        for it in top
    ]
    answer = make_fake_answer(q, contexts, k)  # include bracketed [n] citations in the text

    return SearchResponse(
        query=q,
        total=total,
        page=page,
        page_size=page_size,
        items=top,
        cited_items=top,
        other_items=others,
        mode="rag",
        answer=answer,
    )
