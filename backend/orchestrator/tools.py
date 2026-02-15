import json
import os
from typing import Any, Dict, List, Optional

import numpy as np
import requests
from langchain.tools import tool

from backend.app.services.download import rich_to_plain
from backend.app.store import (
    LMDB_PATH_768_F16,
    load_colbert_from_lmdb,
    resolve_lmdb_path,
)

WEAVIATE_GRAPHQL = os.environ.get("WEAVIATE_GRAPHQL", "http://localhost:8080/v1/graphql")
DEFAULT_LIMIT = int(os.environ.get("RETRIEVAL_K", "5"))
DEFAULT_CANDIDATE_LIMIT = int(os.environ.get("RETRIEVAL_CANDIDATES", str(max(DEFAULT_LIMIT, 50))))
RERANK_SHARD = os.environ.get("COLBERT_SHARD", "768_f16").lower()
RERANK_K = int(os.environ.get("RERANK_K", "100"))

_TOKENIZER = None
_MODEL = None

SHARD_TO_PATH = {
    "768_f16": LMDB_PATH_768_F16,
}


def _init_colbert():
    global _TOKENIZER, _MODEL
    if _TOKENIZER is not None and _MODEL is not None:
        return
    from backend.app.embed import tokenizer, model

    _TOKENIZER = tokenizer
    _MODEL = model


def _embed_query_colbert(query: str) -> List[List[float]]:
    _init_colbert()
    import torch

    tokens = _TOKENIZER(
        query,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=256,
    )
    tokens = {k: v.to(_MODEL.device) for k, v in tokens.items()}
    _MODEL.eval()
    with torch.no_grad():
        outputs = _MODEL(**tokens)

    token_embeddings = outputs.last_hidden_state.squeeze(0)
    attn_mask = tokens["attention_mask"].squeeze(0).bool()
    masked = token_embeddings[attn_mask]
    if masked.numel() == 0:
        masked = token_embeddings[:1]
    return masked.to(torch.float32).detach().cpu().numpy().tolist()


def _embed_query_tokens_for_shard(query: str, shard: str) -> np.ndarray:
    _init_colbert()
    import torch

    shard = shard.lower()
    if shard not in SHARD_TO_PATH:
        raise ValueError(f"Unknown shard '{shard}'. Choose from: {sorted(SHARD_TO_PATH)}")

    tokens = _TOKENIZER(
        query,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=256,
    )
    tokens = {k: v.to(_MODEL.device) for k, v in tokens.items()}
    _MODEL.eval()
    with torch.no_grad():
        outputs = _MODEL(**tokens)
    token_embeddings = outputs.last_hidden_state.squeeze(0)
    attn_mask = tokens["attention_mask"].squeeze(0).bool()
    masked = token_embeddings[attn_mask]
    if masked.numel() == 0:
        masked = token_embeddings[:1]

    dtype = torch.float16 if shard.endswith("f16") else torch.float32
    return masked.to(dtype).detach().cpu().numpy()


def _post_graphql(query: str) -> Dict[str, Any]:
    resp = requests.post(WEAVIATE_GRAPHQL, json={"query": query}, timeout=60)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload.get("data", {})


def _escape_text(value: str) -> str:
    return json.dumps(value)


def _extract_doc_id_filters(where_filter: Optional[Dict[str, Any]]) -> List[str]:
    if not where_filter:
        return []
    out: List[str] = []

    def walk(node: Any):
        if not isinstance(node, dict):
            return
        if "$and" in node and isinstance(node["$and"], list):
            for child in node["$and"]:
                walk(child)
            return
        if "$or" in node and isinstance(node["$or"], list):
            for child in node["$or"]:
                walk(child)
            return
        doc = node.get("doc_id")
        if isinstance(doc, str) and doc.strip():
            out.append(doc.strip())
            return
        if isinstance(doc, dict):
            for k, v in doc.items():
                if k in {"$regex", "$contains"} and isinstance(v, str) and v.strip():
                    out.append(v.strip())
                elif k == "$eq" and isinstance(v, str) and v.strip():
                    out.append(v.strip())

    walk(where_filter)
    dedup: List[str] = []
    seen = set()
    for item in out:
        if item not in seen:
            seen.add(item)
            dedup.append(item)
    return dedup


def _build_claim_where(doc_ids: List[str]) -> str:
    if not doc_ids:
        return ""
    operands = []
    for doc_id in doc_ids:
        pattern = f"*{doc_id}*"
        operands.append(
            "{path:[\"doc_id\"],operator:Like,valueText:%s}" % _escape_text(pattern)
        )
    return "where:{operator:Or,operands:[%s]}," % ",".join(operands)


def _fetch_patent_metadata(doc_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    if not doc_ids:
        return {}

    operands = []
    for doc_id in doc_ids:
        operands.append(
            "{path:[\"doc_id\"],operator:Equal,valueText:%s}" % _escape_text(doc_id)
        )
    where = "where:{operator:Or,operands:[%s]}," % ",".join(operands)

    gql = (
        "{ Get { Patent("
        f"{where} limit:{int(max(1, len(doc_ids)))}"
        ") { doc_id title filing_date classification authors kind } } }"
    )
    data = _post_graphql(gql)
    items = data.get("Get", {}).get("Patent", []) or []
    out: Dict[str, Dict[str, Any]] = {}
    for row in items:
        key = str(row.get("doc_id", "")).strip()
        if key:
            out[key] = row
    return out


def _maxsim_score(query_tokens: np.ndarray, doc_tokens: np.ndarray) -> float:
    if query_tokens.size == 0 or doc_tokens.size == 0:
        return float("-inf")
    qt = query_tokens.astype(np.float32, copy=False)
    dt = doc_tokens.astype(np.float32, copy=False)
    if qt.ndim != 2 or dt.ndim != 2:
        return float("-inf")
    if qt.shape[1] != dt.shape[1]:
        return float("-inf")
    sims = qt @ dt.T
    return float(np.max(sims, axis=1).sum())


def _rerank_hits_with_lmdb(hits: List[Dict[str, Any]], query: str, shard: str, rerank_k: int) -> List[Dict[str, Any]]:
    shard = shard.lower()
    if shard not in SHARD_TO_PATH:
        return hits
    q_tokens = _embed_query_tokens_for_shard(query, shard)
    top = hits[: max(0, int(rerank_k))]
    scored = []
    for hit in top:
        addl = hit.get("_additional") or {}
        obj_id = addl.get("id")
        claim_id = hit.get("claim_id")
        doc_id = hit.get("doc_id")
        if not obj_id and not claim_id:
            continue
        lmdb_path = resolve_lmdb_path(shard, doc_id=doc_id)
        # Primary LMDB key is claim_id; keep UUID fallback for older ingests.
        lookup_keys = [k for k in [claim_id, obj_id] if k]
        doc_tokens = None
        for k in lookup_keys:
            doc_tokens = load_colbert_from_lmdb(lmdb_path, str(k))
            if doc_tokens is not None:
                break
        if doc_tokens is None:
            continue
        score = _maxsim_score(q_tokens, doc_tokens)
        if score == float("-inf"):
            continue
        scored.append((score, hit))
    scored.sort(key=lambda x: x[0], reverse=True)
    reranked = [hit for _, hit in scored]
    used = {id(hit) for hit in reranked}
    for hit in top:
        if id(hit) not in used:
            reranked.append(hit)
    reranked.extend(hits[int(rerank_k):])
    return reranked


@tool(response_format="content")
def retrieve_context(query: str, where_filter: Optional[Dict[str, Any]] = None):
    """Retrieve information to help answer a query, optionally using metadata filters.

    Args:
        query: Search terms to look for
        where_filter: Filter for database search
    """
    if not query or not query.strip():
        return {"query": query, "joined_text": "", "chunks": []}

    query_vector = _embed_query_colbert(query.strip())
    doc_id_filters = _extract_doc_id_filters(where_filter)
    claim_where = _build_claim_where(doc_id_filters)

    gql = (
        "{ Get { Claim("
        f"nearVector: {{vector: {json.dumps(query_vector)}, targetVectors: [\"colbert\"]}},"
        f"{claim_where} limit: {int(DEFAULT_CANDIDATE_LIMIT)}"
        ") { claim_id doc_id claim_type text _additional { id distance } } } }"
    )
    data = _post_graphql(gql)
    hits = data.get("Get", {}).get("Claim", []) or []
    try:
        hits = _rerank_hits_with_lmdb(hits, query.strip(), RERANK_SHARD, RERANK_K)
    except Exception:
        # Keep retrieval resilient if LMDB shard is missing or misconfigured.
        pass
    hits = hits[:DEFAULT_LIMIT]

    unique_doc_ids = []
    seen_doc_ids = set()
    for hit in hits:
        did = str(hit.get("doc_id", "")).strip()
        if did and did not in seen_doc_ids:
            seen_doc_ids.add(did)
            unique_doc_ids.append(did)

    patent_meta = _fetch_patent_metadata(unique_doc_ids)

    chunks: List[Dict[str, Any]] = []
    for hit in hits:
        addl = hit.get("_additional") or {}
        doc_id = str(hit.get("doc_id", "")).strip()
        patent_row = patent_meta.get(doc_id, {})
        text = rich_to_plain(hit.get("text", "") or "")
        snippet = text[:500]

        # Include SearchItem-compatible fields in metadata for API shaping.
        metadata = {
            "id": hit.get("claim_id") or addl.get("id", ""),
            "title": patent_row.get("title", ""),
            "snippet": snippet,
            "search_text": text,
            "doc_id": doc_id,
            "claim_id": hit.get("claim_id", ""),
            "claim_type": hit.get("claim_type", ""),
            "distance": addl.get("distance"),
            "filing_date": patent_row.get("filing_date", ""),
            "classification": patent_row.get("classification", ""),
            "authors": patent_row.get("authors", []),
            "kind": patent_row.get("kind", ""),
        }
        chunks.append({"text": text, "metadata": metadata})

    joined_text = "\n\n".join(c["text"] for c in chunks if c.get("text"))
    return {
        "query": query,
        "query_vector": query_vector,
        "joined_text": joined_text,
        "chunks": chunks,
    }


retriever_tool = retrieve_context
