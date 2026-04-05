from fastapi import APIRouter, Query, Request  # Router groups related endpoints; Query validates URL params
from typing import Dict, Any, List #Typing hints
from ..models.search import SearchResponse
from ..services.retrieval import naive_filter, first_k
from ..services.orchestrator_fake import make_fake_answer
from backend.orchestrator.tools import retrieve_context

router = APIRouter(prefix="/api", tags=["search"])  # All routes here start with /api
'''curl "http://localhost:8000/healthz"
curl "http://localhost:8000/api/search?q=power&k=3"
curl "http://localhost:8000/api/search?q=power&k=3&rag=true"'''
#navigate to Patent_Wizard folder in terminal, activate venv, then proceed below
#To start api server, run "uvicorn backend.app.main:app --reload" in terminal from the Patent_Wizard folder
#Tests defined in README.md

@router.get("/search", response_model=SearchResponse)  # GET /api/search
async def search(
    request: Request,
    q: str = Query("", description="User query string"),                # ?q=...
    k: int = Query(5, ge=1, le=50, description="Top-k results to return"), # cited items count
    k_extra: int = Query(5, ge=0, le=100, description="Additional non-cited results to include"),
    rag: bool = Query(True, description="If true, synthesize a fake RAG answer"), # default to RAG mode
    retrieval_mode: str | None = Query(None, description="Weaviate retrieval mode: vector | bm25 | hybrid"),
    hybrid_alpha: float | None = Query(None, ge=0.0, le=1.0, description="Hybrid alpha (0=bm25, 1=vector)"),
):
    def _map_contexts_to_items(contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        mapped: List[Dict[str, Any]] = []
        for idx, ctx in enumerate(contexts, start=1):
            md = ctx.get("metadata") or {}
            text = ctx.get("text", "") or ""
            snippet = md.get("snippet") or text[:500]
            mapped.append({
                "id": md.get("id", idx),
                "title": md.get("title", ""),
                "snippet": snippet,
                "search_text": md.get("search_text", text),
                "doc_id": md.get("doc_id", ""),
                "claim_id": md.get("claim_id", ""),
                "claim_type": md.get("claim_type", ""),
                "distance": md.get("distance"),
                "filing_date": md.get("filing_date", ""),
                "classification": md.get("classification", ""),
                "authors": md.get("authors", []),
                "kind": md.get("kind", ""),
            })
        return mapped

    page = 1
    page_size = k
    answer = None
    mapped_items: List[Dict[str, Any]] = []
    graph = getattr(request.app.state, "graph", None)

    def _retrieve_payload(query_text: str) -> Dict[str, Any]:
        payload_args: Dict[str, Any] = {"query": query_text}
        if retrieval_mode:
            payload_args["retrieval_mode"] = retrieval_mode
        if hybrid_alpha is not None:
            payload_args["hybrid_alpha"] = hybrid_alpha
        return retrieve_context.invoke(payload_args)

    if rag and graph is not None:
        # Prefer graph-backed RAG, but keep retrieval resilient if the graph
        # decides not to call tools or returns empty contexts.
        try:
            final_state = graph.invoke({"messages": [{"role": "user", "content": q}]})
        except Exception:
            final_state = {}

        mapped_items = _map_contexts_to_items(final_state.get("contexts") or [])
        answer = final_state.get("answer", "")
        if isinstance(answer, list):
            answer = "\n".join(str(x) for x in answer)
        elif not isinstance(answer, str):
            answer = str(answer)

        if not mapped_items:
            payload = _retrieve_payload(q)
            mapped_items = _map_contexts_to_items(payload.get("chunks") or [])
    elif not rag:
        payload = _retrieve_payload(q)
        mapped_items = _map_contexts_to_items(payload.get("chunks") or [])
    else:
        # Fallback path if graph is unavailable.
        items = naive_filter(q)           # token substring match against title/snippet
        top = first_k(items, k)
        others = items[k: k + k_extra] if k_extra else []
        contexts: list[Dict[str, Any]] = [
            {"id": it.id, "title": it.title, "snippet": it.snippet}
            for it in top
        ]
        answer = make_fake_answer(q, contexts, k)  # include bracketed [n] citations in the text
        return SearchResponse(
            query=q,
            total=len(items),
            page=page,
            page_size=page_size,
            items=top,
            cited_items=top,
            other_items=others,
            mode="rag",
            answer=answer,
        )

    total = len(mapped_items)
    cited_items = mapped_items[:k]
    other_items = mapped_items[k: k + k_extra] if k_extra else []

    return SearchResponse(
        query=q,
        total=total,
        page=page,
        page_size=page_size,
        items=cited_items,
        cited_items=cited_items,
        other_items=other_items,
        mode="rag" if rag else "basic",
        answer=answer,
    )
