import json
import os
import re
from typing import Any, Dict, List, Optional

import numpy as np
import requests
from langchain.tools import tool

from backend.app.env_bootstrap import load_project_env
from backend.app.services.download import rich_to_plain
from backend.app.store import (
    LMDB_PATH_128_F16,
    LMDB_PATH_128_F32,
    load_claim_payloads_from_lmdb,
    load_colbert_from_lmdb,
    load_patent_metadata_batch_from_lmdb,
    resolve_lmdb_path,
)
from backend.app.vector_config import WEAVIATE_NAMED_VECTOR, assert_128_variant

load_project_env()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


_DEFAULT_HTTP_HOST = os.environ.get(
    "WEAVIATE_HTTP_HOST",
    os.environ.get("WEAVIATE_LOCAL_HOST", "127.0.0.1"),
).strip() or "127.0.0.1"
_DEFAULT_HTTP_PORT = int(
    os.environ.get(
        "WEAVIATE_HTTP_PORT",
        os.environ.get("WEAVIATE_LOCAL_PORT", "8081"),
    )
)
_DEFAULT_HTTP_SCHEME = "https" if _env_bool("WEAVIATE_HTTP_SECURE", False) else "http"
_DEFAULT_WEAVIATE_HTTP_BASE = f"{_DEFAULT_HTTP_SCHEME}://{_DEFAULT_HTTP_HOST}:{_DEFAULT_HTTP_PORT}"

WEAVIATE_GRAPHQL = os.environ.get("WEAVIATE_GRAPHQL", f"{_DEFAULT_WEAVIATE_HTTP_BASE}/v1/graphql")
DEFAULT_LIMIT = int(os.environ.get("RETRIEVAL_K", "5"))
DEFAULT_CANDIDATE_LIMIT = int(os.environ.get("RETRIEVAL_CANDIDATES", str(max(DEFAULT_LIMIT, 400))))
RERANK_SHARD = assert_128_variant(
    os.environ.get("COLBERT_SHARD", "128_f16").lower(),
    context="orchestrator.RERANK_SHARD",
)
RETRIEVE_SHARD = assert_128_variant(
    os.environ.get("WEAVIATE_SHARD", RERANK_SHARD).lower(),
    context="orchestrator.RETRIEVE_SHARD",
)
RERANK_K = int(os.environ.get("RERANK_K", str(max(DEFAULT_LIMIT, 200))))
_retrieval_mode_env = os.environ.get("RETRIEVAL_MODE", os.environ.get("WEAVIATE_RETRIEVAL_MODE", "vector"))
RETRIEVAL_MODE = str(_retrieval_mode_env or "vector").strip().lower()
if RETRIEVAL_MODE not in {"vector", "bm25", "hybrid"}:
    raise ValueError(
        f"Invalid RETRIEVAL_MODE='{RETRIEVAL_MODE}'. Allowed: vector, bm25, hybrid."
    )
try:
    HYBRID_ALPHA = float(os.environ.get("HYBRID_ALPHA", os.environ.get("WEAVIATE_HYBRID_ALPHA", "0.5")))
except (TypeError, ValueError):
    HYBRID_ALPHA = 0.5
HYBRID_ALPHA = max(0.0, min(1.0, HYBRID_ALPHA))
FORCE_CLIENT_HYBRID = os.environ.get("FORCE_CLIENT_HYBRID", "1").strip() not in {
    "0",
    "false",
    "False",
    "no",
    "NO",
}
SEARCH_SCOPE_CLAIM = "claim"
SEARCH_SCOPE_PATENT = "patent"
PATENT_SCOPE_CANDIDATE_LIMIT_CAP = int(os.environ.get("PATENT_SCOPE_CANDIDATE_LIMIT_CAP", "5000"))
PATENT_SCOPE_RERANK_K_CAP = int(os.environ.get("PATENT_SCOPE_RERANK_K_CAP", "5000"))
CLAIM_PREFILTER_DOC_ID_BATCH_SIZE = int(os.environ.get("CLAIM_PREFILTER_DOC_ID_BATCH_SIZE", "200"))
PATENT_PREFILTER_PAGE_SIZE = int(os.environ.get("PATENT_PREFILTER_PAGE_SIZE", "1000"))
CLAIM_PREFILTER_FIELDS = {"claim_type"}
PATENT_PREFILTER_FIELDS = {
    "authors",
    "classification",
    "doc_id",
    "filing_date",
    "kind",
    "title",
}

SHARD_TO_PATH = {
    "128_f16": LMDB_PATH_128_F16,
    "128_f32": LMDB_PATH_128_F32,
}


def _embed_query_colbert(query: str) -> List[List[float]]:
    from backend.app.embed import (
        embed_query_tokens_for_shard as shared_embed_query_tokens_for_shard,
        normalize_text_for_embedding,
    )

    query_text = normalize_text_for_embedding(query)
    vecs = np.asarray(
        shared_embed_query_tokens_for_shard(query_text, shard=RETRIEVE_SHARD, max_length=256),
        dtype=np.float32,
    )
    if vecs.ndim == 1:
        vecs = vecs.reshape(1, -1)
    return vecs.tolist()


def _embed_query_tokens_for_shard(query: str, shard: str) -> np.ndarray:
    from backend.app.embed import (
        embed_query_tokens_for_shard as shared_embed_query_tokens_for_shard,
        normalize_text_for_embedding,
    )

    shard = assert_128_variant(shard, context="orchestrator._embed_query_tokens_for_shard")
    if shard not in SHARD_TO_PATH:
        raise ValueError(f"Unknown shard '{shard}'. Choose from: {sorted(SHARD_TO_PATH)}")
    query_text = normalize_text_for_embedding(query)
    vecs = np.asarray(shared_embed_query_tokens_for_shard(query_text, shard=shard, max_length=256))
    if vecs.ndim == 1:
        vecs = vecs.reshape(1, -1)
    return vecs


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


def _batched(items: List[str], size: int):
    batch_size = max(1, int(size))
    for idx in range(0, len(items), batch_size):
        yield items[idx: idx + batch_size]


def _combine_where_nodes(operator: str, nodes: List[str]) -> str:
    cleaned = [node for node in nodes if node]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return "{operator:%s,operands:[%s]}" % (operator, ",".join(cleaned))


def _build_doc_id_where_node(doc_ids: Optional[List[str]]) -> str:
    ids = [str(doc_id).strip() for doc_id in (doc_ids or []) if str(doc_id).strip()]
    if not ids:
        return ""
    return _combine_where_nodes(
        "Or",
        [
            "{path:[\"doc_id\"],operator:Equal,valueText:%s}" % _escape_text(doc_id)
            for doc_id in ids
        ],
    )


def _claim_filter_to_where_node(where_filter: Optional[Dict[str, Any]]) -> str:
    if not where_filter:
        return ""
    if "$and" in where_filter:
        return _combine_where_nodes(
            "And",
            [_claim_filter_to_where_node(child) for child in where_filter.get("$and") or []],
        )
    if "$or" in where_filter:
        return _combine_where_nodes(
            "Or",
            [_claim_filter_to_where_node(child) for child in where_filter.get("$or") or []],
        )

    nodes: List[str] = []
    for field, condition in where_filter.items():
        if field != "claim_type":
            continue
        if isinstance(condition, dict):
            expected = condition.get("$eq")
        else:
            expected = condition
        value = _normalize_text_filter_value(expected)
        if not value:
            continue
        nodes.append(
            "{path:[\"claim_type\"],operator:Equal,valueText:%s}" % _escape_text(value)
        )
    return _combine_where_nodes("And", nodes)


def _build_claim_where(
    doc_ids: Optional[List[str]] = None,
    claim_where_filter: Optional[Dict[str, Any]] = None,
) -> str:
    combined = _combine_where_nodes(
        "And",
        [
            _build_doc_id_where_node(doc_ids),
            _claim_filter_to_where_node(claim_where_filter),
        ],
    )
    if not combined:
        return ""
    return f"where:{combined},"


def _filter_value_for_field(field: str, value: Any) -> str:
    if field == "filing_date":
        return _normalize_date_filter_value(value)
    return _normalize_text_filter_value(value)


def _patent_filter_condition_to_where_node(field: str, condition: Any) -> str:
    if isinstance(condition, list):
        return _combine_where_nodes(
            "Or",
            [_patent_filter_condition_to_where_node(field, item) for item in condition],
        )

    if not isinstance(condition, dict):
        value = _filter_value_for_field(field, condition)
        if not value:
            return ""
        return "{path:[%s],operator:Equal,valueText:%s}" % (
            _escape_text(field),
            _escape_text(value),
        )

    nodes: List[str] = []
    options = str(condition.get("$options", "") or "")
    for op, expected in condition.items():
        if op == "$options":
            continue
        value = _filter_value_for_field(field, expected)
        if not value:
            continue
        if op == "$eq":
            nodes.append(
                "{path:[%s],operator:Equal,valueText:%s}" % (
                    _escape_text(field),
                    _escape_text(value),
                )
            )
            continue
        if op in {"$contains", "$regex"}:
            if op == "$regex":
                if options not in {"", "i"}:
                    raise ValueError(f"Unsupported regex options for Weaviate patent prefilter: {options}")
                simple_pattern = str(expected or "")
                if re.search(r"[.^$+?{}\[\]\\|()]", simple_pattern):
                    raise ValueError(f"Unsupported regex for Weaviate patent prefilter: {simple_pattern}")
            nodes.append(
                "{path:[%s],operator:Like,valueText:%s}" % (
                    _escape_text(field),
                    _escape_text(f"*{value}*"),
                )
            )
            continue
        if op in {"$gt", "$gte", "$lt", "$lte"}:
            operator = {
                "$gt": "GreaterThan",
                "$gte": "GreaterThanEqual",
                "$lt": "LessThan",
                "$lte": "LessThanEqual",
            }[op]
            nodes.append(
                "{path:[%s],operator:%s,valueText:%s}" % (
                    _escape_text(field),
                    operator,
                    _escape_text(value),
                )
            )
            continue
        raise ValueError(f"Unsupported patent prefilter operator: {op}")
    return _combine_where_nodes("And", nodes)


def _patent_filter_to_where_node(where_filter: Optional[Dict[str, Any]]) -> str:
    if not where_filter:
        return ""
    if "$and" in where_filter:
        return _combine_where_nodes(
            "And",
            [_patent_filter_to_where_node(child) for child in where_filter.get("$and") or []],
        )
    if "$or" in where_filter:
        return _combine_where_nodes(
            "Or",
            [_patent_filter_to_where_node(child) for child in where_filter.get("$or") or []],
        )

    nodes: List[str] = []
    for field, condition in where_filter.items():
        if field not in PATENT_PREFILTER_FIELDS:
            raise ValueError(f"Unsupported patent prefilter field: {field}")
        nodes.append(_patent_filter_condition_to_where_node(field, condition))
    return _combine_where_nodes("And", nodes)


def _combine_filter_nodes(operator: str, children: List[Optional[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
    cleaned = [child for child in children if child]
    if not cleaned:
        return None
    if len(cleaned) == 1:
        return cleaned[0]
    return {operator: cleaned}


def _split_prefilter_scopes(
    where_filter: Optional[Dict[str, Any]],
) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    if not where_filter or not isinstance(where_filter, dict):
        return None, None, None

    if "$and" in where_filter:
        patent_nodes: List[Optional[Dict[str, Any]]] = []
        claim_nodes: List[Optional[Dict[str, Any]]] = []
        residual_nodes: List[Optional[Dict[str, Any]]] = []
        for child in where_filter.get("$and") or []:
            patent_node, claim_node, residual_node = _split_prefilter_scopes(child)
            patent_nodes.append(patent_node)
            claim_nodes.append(claim_node)
            residual_nodes.append(residual_node)
        return (
            _combine_filter_nodes("$and", patent_nodes),
            _combine_filter_nodes("$and", claim_nodes),
            _combine_filter_nodes("$and", residual_nodes),
        )

    if "$or" in where_filter:
        child_splits = [_split_prefilter_scopes(child) for child in where_filter.get("$or") or []]
        if child_splits and all(patent and not claim and not residual for patent, claim, residual in child_splits):
            return (
                _combine_filter_nodes("$or", [patent for patent, _, _ in child_splits]),
                None,
                None,
            )
        if child_splits and all(claim and not patent and not residual for patent, claim, residual in child_splits):
            return (
                None,
                _combine_filter_nodes("$or", [claim for _, claim, _ in child_splits]),
                None,
            )
        return None, None, where_filter

    patent_node: Dict[str, Any] = {}
    claim_node: Dict[str, Any] = {}
    residual_node: Dict[str, Any] = {}
    for field, condition in where_filter.items():
        if field in PATENT_PREFILTER_FIELDS:
            patent_node[field] = condition
        elif field in CLAIM_PREFILTER_FIELDS:
            claim_node[field] = condition
        else:
            residual_node[field] = condition
    return (
        patent_node or None,
        claim_node or None,
        residual_node or None,
    )


def _normalize_text_filter_value(value: Any) -> str:
    return str(value or "").strip()


def _normalize_date_filter_value(value: Any) -> str:
    raw = _normalize_text_filter_value(value)
    if not raw:
        return ""
    digits = re.sub(r"\D", "", raw)
    if len(digits) >= 8:
        return digits[:8]
    return raw


def _metadata_values_for_field(
    field: str,
    hit: Dict[str, Any],
    claim_payload: Dict[str, Any],
    patent_row: Dict[str, Any],
) -> List[str]:
    if field == "doc_id":
        return [
            _normalize_text_filter_value(
                hit.get("doc_id") or claim_payload.get("doc_id") or patent_row.get("doc_id")
            )
        ]
    if field == "claim_type":
        return [
            _normalize_text_filter_value(
                hit.get("claim_type") or claim_payload.get("claim_type")
            )
        ]
    if field == "classification":
        return [_normalize_text_filter_value(patent_row.get("classification"))]
    if field == "kind":
        return [_normalize_text_filter_value(patent_row.get("kind"))]
    if field == "filing_date":
        return [_normalize_date_filter_value(patent_row.get("filing_date"))]
    if field == "title":
        return [_normalize_text_filter_value(patent_row.get("title"))]
    if field == "authors":
        authors = patent_row.get("authors") or []
        if isinstance(authors, list):
            return [_normalize_text_filter_value(author) for author in authors if _normalize_text_filter_value(author)]
        return [_normalize_text_filter_value(authors)]
    return []


def _matches_single_condition(field: str, candidate: str, op: str, expected: Any, *, options: str = "") -> bool:
    candidate = _normalize_date_filter_value(candidate) if field == "filing_date" else _normalize_text_filter_value(candidate)
    expected_value = (
        _normalize_date_filter_value(expected)
        if field == "filing_date"
        else _normalize_text_filter_value(expected)
    )
    if op == "$regex":
        if not expected_value:
            return True
        flags = re.IGNORECASE if "i" in str(options) else 0
        try:
            return re.search(str(expected), candidate, flags) is not None
        except re.error:
            return expected_value.lower() in candidate.lower()
    if op == "$contains":
        if not expected_value:
            return True
        return expected_value.lower() in candidate.lower()
    if op == "$eq":
        return candidate.lower() == expected_value.lower()
    if op in {"$gt", "$gte", "$lt", "$lte"}:
        left = candidate
        right = expected_value
        if not left or not right:
            return False
        if op == "$gt":
            return left > right
        if op == "$gte":
            return left >= right
        if op == "$lt":
            return left < right
        return left <= right
    return False


def _matches_field_condition(field: str, values: List[str], condition: Any) -> bool:
    cleaned = [value for value in values if _normalize_text_filter_value(value)]
    if isinstance(condition, dict):
        options = str(condition.get("$options", "") or "")
        for op, expected in condition.items():
            if op == "$options":
                continue
            if op in {"$gt", "$gte", "$lt", "$lte", "$eq", "$contains", "$regex"}:
                if not any(
                    _matches_single_condition(field, value, op, expected, options=options)
                    for value in cleaned
                ):
                    return False
        return True
    if isinstance(condition, list):
        return any(_matches_field_condition(field, cleaned, item) for item in condition)
    return any(
        _matches_single_condition(field, value, "$eq", condition)
        for value in cleaned
    )


def _matches_where_filter(
    where_filter: Optional[Dict[str, Any]],
    hit: Dict[str, Any],
    claim_payload: Dict[str, Any],
    patent_row: Dict[str, Any],
) -> bool:
    if not where_filter:
        return True
    if "$and" in where_filter:
        return all(
            _matches_where_filter(child, hit, claim_payload, patent_row)
            for child in where_filter.get("$and") or []
        )
    if "$or" in where_filter:
        return any(
            _matches_where_filter(child, hit, claim_payload, patent_row)
            for child in where_filter.get("$or") or []
        )
    for field, condition in where_filter.items():
        values = _metadata_values_for_field(field, hit, claim_payload, patent_row)
        if not _matches_field_condition(field, values, condition):
            return False
    return True


def _build_retrieval_clause(query: str, mode: str, hybrid_alpha: float, query_vector: List[List[float]]) -> str:
    if mode == "bm25":
        return f"bm25:{{query:{_escape_text(query)}}},"
    if mode == "hybrid":
        alpha = max(0.0, min(1.0, float(hybrid_alpha)))
        # Avoid Weaviate edge-case instability on hybrid alpha=0 by using native BM25.
        if alpha <= 0.0:
            return f"bm25:{{query:{_escape_text(query)}}},"
        if alpha >= 1.0:
            return f'nearVector:{{vector:{json.dumps(query_vector)},targetVectors:["{WEAVIATE_NAMED_VECTOR}"]}},'
        return (
            "hybrid:{"
            f"query:{_escape_text(query)},"
            f"alpha:{alpha:.6f},"
            f"vector:{json.dumps(query_vector)},"
            f'targetVectors:["{WEAVIATE_NAMED_VECTOR}"]'
            "},"
        )
    return f'nearVector:{{vector:{json.dumps(query_vector)},targetVectors:["{WEAVIATE_NAMED_VECTOR}"]}},'


def _query_claim_rows(retrieval_clause: str, claim_where: str, limit: int) -> List[Dict[str, Any]]:
    gql = (
        "{ Get { Claim("
        f"{retrieval_clause}"
        f"{claim_where} limit: {int(limit)}"
        ") { claim_id doc_id claim_type text _additional { id distance } } } }"
    )
    data = _post_graphql(gql)
    return data.get("Get", {}).get("Claim", []) or []


def _query_claim_rows_unranked(claim_where: str, limit: int) -> List[Dict[str, Any]]:
    if not claim_where:
        return []
    gql = (
        "{ Get { Claim("
        f"{claim_where} limit: {int(limit)}"
        ") { claim_id doc_id claim_type text _additional { id } } } }"
    )
    data = _post_graphql(gql)
    return data.get("Get", {}).get("Claim", []) or []


def _query_patent_rows(
    patent_where_node: str,
    *,
    limit: int,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    args = []
    if patent_where_node:
        args.append(f"where:{patent_where_node}")
    args.append(f"limit:{int(limit)}")
    if offset:
        args.append(f"offset:{int(offset)}")
    gql = (
        "{ Get { Patent("
        f"{','.join(args)}"
        ") { doc_id filing_date classification authors title kind } } }"
    )
    data = _post_graphql(gql)
    return data.get("Get", {}).get("Patent", []) or []


def _claim_row_key(hit: Dict[str, Any]) -> str:
    addl = hit.get("_additional") or {}
    return str(hit.get("claim_id") or addl.get("id") or hit.get("doc_id") or "")


def _fuse_hybrid_rows(
    vector_rows: List[Dict[str, Any]],
    bm25_rows: List[Dict[str, Any]],
    alpha: float,
    limit: int,
    *,
    rrf_k: int = 60,
) -> List[Dict[str, Any]]:
    alpha = max(0.0, min(1.0, float(alpha)))
    weights = {
        "vector": alpha,
        "bm25": 1.0 - alpha,
    }
    score_by_key: Dict[str, float] = {}
    row_by_key: Dict[str, Dict[str, Any]] = {}

    for source, rows in (("vector", vector_rows), ("bm25", bm25_rows)):
        w = weights[source]
        if w <= 0.0:
            continue
        for rank, row in enumerate(rows, start=1):
            key = _claim_row_key(row)
            if not key:
                continue
            if key not in row_by_key:
                row_by_key[key] = row
            else:
                existing_addl = row_by_key[key].get("_additional") or {}
                candidate_addl = row.get("_additional") or {}
                if existing_addl.get("distance") is None and candidate_addl.get("distance") is not None:
                    merged = dict(row_by_key[key])
                    merged["_additional"] = {
                        **existing_addl,
                        "distance": candidate_addl.get("distance"),
                    }
                    row_by_key[key] = merged
            score_by_key[key] = score_by_key.get(key, 0.0) + (w / float(rrf_k + rank))

    ranked_keys = sorted(score_by_key, key=lambda k: score_by_key[k], reverse=True)[: int(limit)]
    return [row_by_key[k] for k in ranked_keys]


def _retrieve_hybrid_client_fusion(
    query_text: str,
    claim_where: str,
    query_vector: List[List[float]],
    alpha: float,
    limit: int,
) -> List[Dict[str, Any]]:
    vec_clause = (
        f'nearVector:{{vector:{json.dumps(query_vector)},targetVectors:["{WEAVIATE_NAMED_VECTOR}"]}},'
    )
    bm25_clause = f"bm25:{{query:{_escape_text(query_text)}}},"
    vec_rows: List[Dict[str, Any]] = []
    bm25_rows: List[Dict[str, Any]] = []
    try:
        vec_rows = _query_claim_rows(vec_clause, claim_where, int(limit))
    except Exception as ve:
        print(f"[warn] hybrid nearVector leg failed: {ve}")
    try:
        bm25_rows = _query_claim_rows(bm25_clause, claim_where, int(limit))
    except Exception as be:
        print(f"[warn] hybrid bm25 leg failed: {be}")
    if not vec_rows and not bm25_rows:
        raise RuntimeError("both hybrid legs failed (nearVector and bm25)")
    return _fuse_hybrid_rows(vec_rows, bm25_rows, alpha, int(limit))


def _normalize_retrieval_mode(value: str | None) -> str:
    mode = str(value or RETRIEVAL_MODE).strip().lower()
    if mode not in {"vector", "bm25", "hybrid"}:
        raise ValueError(f"Unknown retrieval mode '{value}'. Choose from: vector, bm25, hybrid.")
    return mode


def _resolve_positive_int(value: Any, default: int, *, minimum: int = 1) -> int:
    try:
        resolved = int(value)
    except (TypeError, ValueError):
        return int(default)
    return max(int(minimum), resolved)


def _is_missing_metadata_value(value: Any) -> bool:
    return value is None or value == "" or value == []


def _normalize_search_scope(value: str | None) -> str:
    scope = str(value or SEARCH_SCOPE_CLAIM).strip().lower()
    return SEARCH_SCOPE_PATENT if scope == SEARCH_SCOPE_PATENT else SEARCH_SCOPE_CLAIM


def _patent_candidate_limit_default(result_limit: int) -> int:
    return min(
        PATENT_SCOPE_CANDIDATE_LIMIT_CAP,
        max(DEFAULT_CANDIDATE_LIMIT * 2, int(result_limit) * 80),
    )


def _patent_rerank_k_default(result_limit: int) -> int:
    return min(
        PATENT_SCOPE_RERANK_K_CAP,
        max(RERANK_K * 2, int(result_limit) * 40),
    )


def _fetch_patent_metadata(doc_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    ordered_doc_ids: List[str] = []
    seen = set()
    for doc_id in doc_ids:
        value = str(doc_id or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        ordered_doc_ids.append(value)
    if not ordered_doc_ids:
        return {}

    rows_by_doc_id: Dict[str, Dict[str, Any]] = {}
    try:
        for doc_id_batch in _batched(ordered_doc_ids, CLAIM_PREFILTER_DOC_ID_BATCH_SIZE):
            patent_where_node = _build_doc_id_where_node(doc_id_batch)
            for row in _query_patent_rows(patent_where_node, limit=max(1, len(doc_id_batch))):
                doc_id = str(row.get("doc_id") or "").strip()
                if doc_id:
                    rows_by_doc_id[doc_id] = row
    except Exception as exc:
        print(f"[warn] patent metadata fetch from Weaviate failed; using LMDB fallback: {exc}")

    for doc_id, overlay in load_patent_metadata_batch_from_lmdb(ordered_doc_ids).items():
        merged = dict(rows_by_doc_id.get(doc_id) or {})
        for key, value in (overlay or {}).items():
            if key in {"abstract", "abstract_text"}:
                if value:
                    merged[key] = value
                continue
            if _is_missing_metadata_value(merged.get(key)) and not _is_missing_metadata_value(value):
                merged[key] = value
        if merged:
            rows_by_doc_id[doc_id] = merged

    return rows_by_doc_id


def _prefilter_doc_ids_from_patent_metadata(where_filter: Optional[Dict[str, Any]]) -> Optional[List[str]]:
    if not where_filter:
        return None
    doc_ids: List[str] = []
    seen = set()
    page_size = max(1, int(PATENT_PREFILTER_PAGE_SIZE))
    try:
        patent_where_node = _patent_filter_to_where_node(where_filter)
        offset = 0
        while True:
            rows = _query_patent_rows(patent_where_node, limit=page_size, offset=offset)
            for patent_row in rows:
                doc_id = str(patent_row.get("doc_id") or "").strip()
                if not doc_id or doc_id in seen:
                    continue
                seen.add(doc_id)
                doc_ids.append(doc_id)
            if len(rows) < page_size:
                break
            offset += page_size
        return doc_ids
    except Exception as exc:
        print(f"[warn] Weaviate patent prefilter query failed; falling back to full patent scan: {exc}")

    offset = 0
    while True:
        rows = _query_patent_rows("", limit=page_size, offset=offset)
        for patent_row in rows:
            if not _matches_where_filter(where_filter, {}, {}, patent_row):
                continue
            doc_id = str(patent_row.get("doc_id") or "").strip()
            if not doc_id or doc_id in seen:
                continue
            seen.add(doc_id)
            doc_ids.append(doc_id)
        if len(rows) < page_size:
            break
        offset += page_size
    return doc_ids


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
    shard = assert_128_variant(shard, context="orchestrator._rerank_hits_with_lmdb")
    if shard not in SHARD_TO_PATH:
        raise ValueError(f"Unknown shard '{shard}'. Choose from: {sorted(SHARD_TO_PATH)}")
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
            raise RuntimeError(f"Missing LMDB vectors for claim_id={claim_id} doc_id={doc_id}")
        arr = np.asarray(doc_tokens)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if arr.ndim != 2 or arr.shape[1] != 128:
            raise ValueError(
                f"LMDB vectors must be [T,128] for claim_id={claim_id}; got shape={arr.shape}"
            )
        score = _maxsim_score(q_tokens, doc_tokens)
        if score == float("-inf"):
            raise RuntimeError(f"Invalid MaxSim score for claim_id={claim_id}")
        scored.append((score, hit))
    scored.sort(key=lambda x: x[0], reverse=True)
    reranked = [hit for _, hit in scored]
    used = {id(hit) for hit in reranked}
    for hit in top:
        if id(hit) not in used:
            reranked.append(hit)
    reranked.extend(hits[int(rerank_k):])
    return reranked


def _collapse_hits_to_patents(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    collapsed: List[Dict[str, Any]] = []
    seen_keys = set()
    for hit in hits:
        addl = hit.get("_additional") or {}
        key = str(hit.get("doc_id") or hit.get("claim_id") or addl.get("id") or "").strip()
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)
        collapsed.append(hit)
    return collapsed


def _preferred_result_text(search_scope: str, patent_row: Dict[str, Any], fallback_text: str) -> str:
    if search_scope == SEARCH_SCOPE_PATENT:
        abstract_text = rich_to_plain(str(patent_row.get("abstract_text") or patent_row.get("abstract") or ""))
        if abstract_text:
            return abstract_text
    return fallback_text


def _retrieve_claim_rows(
    query_text: str,
    retrieval_clause: str,
    claim_where: str,
    query_vector: List[List[float]],
    effective_mode: str,
    effective_alpha: float,
    limit: int,
) -> List[Dict[str, Any]]:
    if effective_mode == "hybrid" and 0.0 < effective_alpha < 1.0 and FORCE_CLIENT_HYBRID:
        return _retrieve_hybrid_client_fusion(
            query_text,
            claim_where,
            query_vector,
            effective_alpha,
            int(limit),
        )
    try:
        return _query_claim_rows(retrieval_clause, claim_where, int(limit))
    except Exception as exc:
        if effective_mode != "hybrid" or effective_alpha <= 0.0 or effective_alpha >= 1.0:
            raise
        print(f"[warn] server-side hybrid failed; using client-side fusion fallback: {exc}")
        return _retrieve_hybrid_client_fusion(
            query_text,
            claim_where,
            query_vector,
            effective_alpha,
            int(limit),
        )


def _retrieve_unranked_prefilter_hits(
    prefiltered_doc_ids: List[str],
    claim_prefilter: Optional[Dict[str, Any]],
    limit: int,
) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    seen_hit_keys = set()
    for doc_id_batch in _batched(prefiltered_doc_ids, CLAIM_PREFILTER_DOC_ID_BATCH_SIZE):
        claim_where = _build_claim_where(doc_id_batch, claim_prefilter)
        batch_hits = _query_claim_rows_unranked(claim_where, int(limit))
        for hit in batch_hits:
            hit_key = _claim_row_key(hit)
            if not hit_key or hit_key in seen_hit_keys:
                continue
            seen_hit_keys.add(hit_key)
            hits.append(hit)
    return hits


@tool(response_format="content")
def retrieve_context(
    query: str,
    where_filter: Optional[Dict[str, Any]] = None,
    retrieval_mode: Optional[str] = None,
    hybrid_alpha: Optional[float] = None,
    search_scope: Optional[str] = None,
    result_limit: Optional[int] = None,
    candidate_limit: Optional[int] = None,
    rerank_k: Optional[int] = None,
):
    """Retrieve information to help answer a query, optionally using metadata filters.

    Args:
        query: Search terms to look for
        where_filter: Filter for database search
    """
    if not query or not query.strip():
        return {"query": query, "joined_text": "", "chunks": []}

    query_text = query.strip()
    effective_mode = _normalize_retrieval_mode(retrieval_mode)
    effective_search_scope = _normalize_search_scope(search_scope)
    effective_alpha = HYBRID_ALPHA if hybrid_alpha is None else max(0.0, min(1.0, float(hybrid_alpha)))
    effective_limit = _resolve_positive_int(result_limit, DEFAULT_LIMIT, minimum=1)
    candidate_default = (
        _patent_candidate_limit_default(effective_limit)
        if effective_search_scope == SEARCH_SCOPE_PATENT
        else max(DEFAULT_CANDIDATE_LIMIT, effective_limit)
    )
    effective_candidate_limit = _resolve_positive_int(
        candidate_limit,
        candidate_default,
        minimum=effective_limit,
    )
    rerank_default = (
        _patent_rerank_k_default(effective_limit)
        if effective_search_scope == SEARCH_SCOPE_PATENT
        else max(RERANK_K, effective_limit)
    )
    effective_rerank_k = _resolve_positive_int(
        rerank_k,
        rerank_default,
        minimum=effective_limit,
    )
    query_vector = _embed_query_colbert(query_text) if effective_mode in {"vector", "hybrid"} else []
    retrieval_clause = _build_retrieval_clause(query_text, effective_mode, effective_alpha, query_vector)
    patent_prefilter, claim_prefilter, _residual_filter = _split_prefilter_scopes(where_filter)
    prefiltered_doc_ids = _prefilter_doc_ids_from_patent_metadata(patent_prefilter)
    used_prefilter_batches = False

    if patent_prefilter and prefiltered_doc_ids == []:
        hits: List[Dict[str, Any]] = []
    elif prefiltered_doc_ids and len(prefiltered_doc_ids) > CLAIM_PREFILTER_DOC_ID_BATCH_SIZE:
        used_prefilter_batches = True
        hits = []
        seen_hit_keys = set()
        for doc_id_batch in _batched(prefiltered_doc_ids, CLAIM_PREFILTER_DOC_ID_BATCH_SIZE):
            claim_where = _build_claim_where(doc_id_batch, claim_prefilter)
            batch_hits = _retrieve_claim_rows(
                query_text,
                retrieval_clause,
                claim_where,
                query_vector,
                effective_mode,
                effective_alpha,
                int(effective_candidate_limit),
            )
            for hit in batch_hits:
                hit_key = _claim_row_key(hit)
                if not hit_key or hit_key in seen_hit_keys:
                    continue
                seen_hit_keys.add(hit_key)
                hits.append(hit)
    else:
        claim_where = _build_claim_where(prefiltered_doc_ids, claim_prefilter)
        hits = _retrieve_claim_rows(
            query_text,
            retrieval_clause,
            claim_where,
            query_vector,
            effective_mode,
            effective_alpha,
            int(effective_candidate_limit),
        )

    if not hits and prefiltered_doc_ids:
        used_prefilter_batches = True
        hits = _retrieve_unranked_prefilter_hits(
            prefiltered_doc_ids,
            claim_prefilter,
            int(effective_candidate_limit),
        )

    if where_filter and hits:
        candidate_claim_ids = [
            str(hit.get("claim_id", "")).strip()
            for hit in hits
            if str(hit.get("claim_id", "")).strip()
        ]
        candidate_claim_payloads = load_claim_payloads_from_lmdb(candidate_claim_ids)
        candidate_doc_ids: List[str] = []
        seen_candidate_doc_ids = set()
        for hit in hits:
            claim_id = str(hit.get("claim_id", "")).strip()
            payload = candidate_claim_payloads.get(claim_id) or {}
            doc_id = str(hit.get("doc_id", "") or payload.get("doc_id") or "").strip()
            if doc_id and doc_id not in seen_candidate_doc_ids:
                seen_candidate_doc_ids.add(doc_id)
                candidate_doc_ids.append(doc_id)
        candidate_patent_meta = _fetch_patent_metadata(candidate_doc_ids)
        hits = [
            hit
            for hit in hits
            if _matches_where_filter(
                where_filter,
                hit,
                candidate_claim_payloads.get(str(hit.get("claim_id", "")).strip()) or {},
                candidate_patent_meta.get(
                    str(
                        hit.get("doc_id", "")
                        or (candidate_claim_payloads.get(str(hit.get("claim_id", "")).strip()) or {}).get("doc_id")
                        or ""
                    ).strip(),
                    {},
                ),
            )
        ]

    rerank_window = len(hits) if used_prefilter_batches else effective_rerank_k
    hits = _rerank_hits_with_lmdb(hits, query.strip(), RERANK_SHARD, rerank_window)
    if effective_search_scope == SEARCH_SCOPE_PATENT:
        hits = _collapse_hits_to_patents(hits)
    hits = hits[:effective_limit]

    claim_payloads = load_claim_payloads_from_lmdb(
        [str(hit.get("claim_id", "")).strip() for hit in hits if str(hit.get("claim_id", "")).strip()]
    )

    unique_doc_ids = []
    seen_doc_ids = set()
    for hit in hits:
        claim_id = str(hit.get("claim_id", "")).strip()
        payload = claim_payloads.get(claim_id) or {}
        did = str(hit.get("doc_id", "") or payload.get("doc_id") or "").strip()
        if did and did not in seen_doc_ids:
            seen_doc_ids.add(did)
            unique_doc_ids.append(did)

    patent_meta = _fetch_patent_metadata(unique_doc_ids)

    chunks: List[Dict[str, Any]] = []
    for hit in hits:
        addl = hit.get("_additional") or {}
        claim_id = str(hit.get("claim_id", "")).strip()
        payload = claim_payloads.get(claim_id) or {}
        doc_id = str(hit.get("doc_id", "") or payload.get("doc_id") or "").strip()
        patent_row = patent_meta.get(doc_id, {})
        claim_text = rich_to_plain(str(payload.get("text") or hit.get("text") or ""))
        text = _preferred_result_text(effective_search_scope, patent_row, claim_text)
        snippet = text[:500]
        best_claim_type = str(payload.get("claim_type") or hit.get("claim_type") or "")

        # Include SearchItem-compatible fields in metadata for API shaping.
        metadata = {
            "id": doc_id if effective_search_scope == SEARCH_SCOPE_PATENT else hit.get("claim_id") or addl.get("id", ""),
            "title": patent_row.get("title", ""),
            "snippet": snippet,
            "search_text": text,
            "doc_id": doc_id,
            "claim_id": claim_id,
            "claim_type": best_claim_type,
            "best_claim_id": claim_id,
            "best_claim_type": best_claim_type,
            "distance": addl.get("distance"),
            "filing_date": patent_row.get("filing_date", ""),
            "classification": patent_row.get("classification", ""),
            "authors": patent_row.get("authors", []),
            "kind": patent_row.get("kind", ""),
            "abstract_text": rich_to_plain(str(patent_row.get("abstract_text") or patent_row.get("abstract") or "")),
        }
        chunks.append({"text": text, "metadata": metadata})

    joined_text = "\n\n".join(c["text"] for c in chunks if c.get("text"))
    return {
        "query": query,
        "search_scope": effective_search_scope,
        "query_vector": query_vector,
        "retrieval_mode": effective_mode,
        "hybrid_alpha": effective_alpha,
        "result_limit": effective_limit,
        "candidate_limit": effective_candidate_limit,
        "rerank_k": effective_rerank_k,
        "joined_text": joined_text,
        "chunks": chunks,
    }


retriever_tool = retrieve_context
