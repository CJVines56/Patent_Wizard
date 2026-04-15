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
    search_scope: str = Query("claim", description="Search scope: claim | patent"),
    k: int = Query(5, ge=1, le=50, description="Top-k results to return"), # cited items count
    k_extra: int = Query(5, ge=0, le=100, description="Additional non-cited results to include"),
    rag: bool = Query(True, description="If true, synthesize a fake RAG answer"), # default to RAG mode
    retrieval_mode: str | None = Query(None, description="Weaviate retrieval mode: vector | bm25 | hybrid"),
    alpha: float | None = Query(None, ge=0.0, le=1.0, description="Alias for hybrid alpha"),
    hybrid_alpha: float | None = Query(None, ge=0.0, le=1.0, description="Hybrid alpha (0=bm25, 1=vector)"),
    retrieval_candidates: int | None = Query(None, ge=1, le=5000, description="Candidate hits to retrieve before reranking"),
    rerank_k: int | None = Query(None, ge=1, le=5000, description="Number of hits to rerank with LMDB"),
    filter_doc_id: str | None = Query(None, description="Filter results by doc_id substring"),
    filter_claim_type: str | None = Query(None, description="Filter results by claim type"),
    filter_kind: str | None = Query(None, description="Filter results by patent kind"),
    filter_date_from: str | None = Query(None, description="Filter results by filing date lower bound"),
    filter_date_to: str | None = Query(None, description="Filter results by filing date upper bound"),
):
    def _normalize_search_scope(value: str | None) -> str:
        scope = str(value or "claim").strip().lower()
        return "patent" if scope == "patent" else "claim"

    def _normalize_date_token(value: str | None) -> str:
        if not value:
            return ""
        digits = "".join(ch for ch in str(value).strip() if ch.isdigit())
        if len(digits) >= 8:
            return digits[:8]
        return ""

    def _build_explicit_where_filter() -> Dict[str, Any]:
        filters: List[Dict[str, Any]] = []
        doc_id = str(filter_doc_id or "").strip()
        claim_type = str(filter_claim_type or "").strip()
        kind = str(filter_kind or "").strip()
        date_from = _normalize_date_token(filter_date_from)
        date_to = _normalize_date_token(filter_date_to)

        if doc_id:
            filters.append({"doc_id": {"$contains": doc_id}})
        if claim_type:
            filters.append({"claim_type": {"$eq": claim_type}})
        if kind:
            filters.append({"kind": {"$eq": kind}})
        if date_from or date_to:
            date_filter: Dict[str, str] = {}
            if date_from:
                date_filter["$gte"] = date_from
            if date_to:
                date_filter["$lte"] = date_to
            filters.append({"filing_date": date_filter})

        if not filters:
            return {}
        if len(filters) == 1:
            return filters[0]
        return {"$and": filters}

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
                "best_claim_id": md.get("best_claim_id", ""),
                "best_claim_type": md.get("best_claim_type", ""),
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
    explicit_where_filter = _build_explicit_where_filter()
    has_explicit_filters = bool(explicit_where_filter)
    display_limit = max(1, k + max(0, k_extra))
    effective_hybrid_alpha = hybrid_alpha if hybrid_alpha is not None else alpha
    effective_search_scope = _normalize_search_scope(search_scope)

    def _retrieve_payload(query_text: str) -> Dict[str, Any]:
        payload_args: Dict[str, Any] = {
            "query": query_text,
            "search_scope": effective_search_scope,
            "result_limit": display_limit,
        }
        if retrieval_mode:
            payload_args["retrieval_mode"] = retrieval_mode
        if effective_hybrid_alpha is not None:
            payload_args["hybrid_alpha"] = effective_hybrid_alpha
        if retrieval_candidates is not None:
            payload_args["candidate_limit"] = retrieval_candidates
        if rerank_k is not None:
            payload_args["rerank_k"] = rerank_k
        if explicit_where_filter:
            payload_args["where_filter"] = explicit_where_filter
        return retrieve_context.invoke(payload_args)

    if rag and graph is not None and not has_explicit_filters and effective_search_scope == "claim":
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

        if len(mapped_items) < display_limit:
            payload = _retrieve_payload(q)
            mapped_items = _map_contexts_to_items(payload.get("chunks") or [])
    elif not rag or has_explicit_filters:
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
            search_scope=effective_search_scope,
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
    if not answer:
        if effective_search_scope == "patent":
            answer = "WIP patent search mode: patents are ranked by their highest-ranked matching claim."
        elif has_explicit_filters:
            answer = "Direct claim retrieval mode with filters applied."
        elif not rag:
            answer = "Direct claim retrieval mode: returning top matching claims."

    return SearchResponse(
        query=q,
        search_scope=effective_search_scope,
        total=total,
        page=page,
        page_size=page_size,
        items=cited_items,
        cited_items=cited_items,
        other_items=other_items,
        mode="rag" if rag and effective_search_scope == "claim" and not has_explicit_filters else "basic",
        answer=answer,
    )
