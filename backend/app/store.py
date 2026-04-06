
# 11/3/2025 Rewrote code to take in list of dictionaries with all patent data
# Old client for weaviate cluster
'''
def get_client():
    # This call connects to my cluster and that authenitcates connection w/API key.
    return weaviate.connect_to_weaviate_cloud(
        cluster_url="https://iyulz7xksmozhh8hzqf9w.c0.us-west3.gcp.weaviate.cloud",
        auth_credentials=Auth.api_key("enNFY0pkMGY5RENrcEljTV9lblU2UkV6U2JhZjBvZGFEWDQ2MnlHakNNWVE3VUIyTlFDRVdOQjA5WjVNPV92MjAw"),
    )
'''
import io
import json
import os
import re
import uuid
import hashlib
from pathlib import Path
from typing import Any

import lmdb
import numpy as np
import weaviate
from weaviate.config import AdditionalConfig, Timeout
from weaviate.collections.classes.data import DataObject
from weaviate.classes.config import Property, DataType, Configure
from weaviate.classes.init import Auth
from weaviate.exceptions import WeaviateBatchError
from backend.app.vector_config import (
    ALLOWED_VARIANTS,
    PRIMARY_COLBERT_VARIANT,
    TOKEN_VECTOR_DIM,
    TOKEN_VECTOR_DTYPE,
    assert_128_variant,
)

try:
    from weaviate.classes.config import Reconfigure
except Exception:
    Reconfigure = None

_LMDB_DIR = Path(__file__).resolve().parents[1] / "lmdb"
LMDB_PATH = Path(os.environ.get("LMDB_PATH", _LMDB_DIR / "colbert_vectors.lmdb"))
LMDB_PATH_128_F32 = Path(os.environ.get("LMDB_PATH_128_F32", _LMDB_DIR / "colbert_128_f32.lmdb"))
LMDB_PATH_128_F16 = Path(os.environ.get("LMDB_PATH_128_F16", _LMDB_DIR / "colbert_128_f16.lmdb"))
LMDB_PATH_PATENT_METADATA = Path(
    os.environ.get("LMDB_PATH_PATENT_METADATA", _LMDB_DIR / "patent_metadata.lmdb")
)
LMDB_PATH_CLAIM_PAYLOAD = Path(
    os.environ.get("LMDB_PATH_CLAIM_PAYLOAD", _LMDB_DIR / "claim_payloads.lmdb")
)
LMDB_SHARDING_MODE = os.environ.get("LMDB_SHARDING_MODE", "none").strip().lower()
LMDB_MAP_SIZE = int(os.environ.get("LMDB_MAP_SIZE", str(10 * 1024**3)))
LMDB_MAP_GROW_GB = int(os.environ.get("LMDB_MAP_GROW_GB", "10"))
LMDB_VECTOR_DTYPE = TOKEN_VECTOR_DTYPE
WEAVIATE_BATCH_SIZE = int(os.environ.get("WEAVIATE_BATCH_SIZE", "128"))
WEAVIATE_HNSW_EF = int(os.environ.get("WEAVIATE_HNSW_EF", "-1"))
WEAVIATE_HNSW_DYNAMIC_EF_MIN = int(os.environ.get("WEAVIATE_HNSW_DYNAMIC_EF_MIN", "100"))
WEAVIATE_HNSW_DYNAMIC_EF_MAX = int(os.environ.get("WEAVIATE_HNSW_DYNAMIC_EF_MAX", "1200"))
WEAVIATE_HNSW_DYNAMIC_EF_FACTOR = int(os.environ.get("WEAVIATE_HNSW_DYNAMIC_EF_FACTOR", "8"))
WEAVIATE_HNSW_FLAT_SEARCH_CUTOFF = int(os.environ.get("WEAVIATE_HNSW_FLAT_SEARCH_CUTOFF", "40000"))
WEAVIATE_HNSW_VECTOR_CACHE_MAX_OBJECTS = int(
    os.environ.get("WEAVIATE_HNSW_VECTOR_CACHE_MAX_OBJECTS", "0")
)
WEAVIATE_PQ_ENABLED = os.environ.get("WEAVIATE_PQ_ENABLED", "1").strip() not in {
    "0",
    "false",
    "False",
    "no",
    "NO",
}
WEAVIATE_PQ_CENTROIDS = int(os.environ.get("WEAVIATE_PQ_CENTROIDS", "256"))
WEAVIATE_PQ_SEGMENTS = int(os.environ.get("WEAVIATE_PQ_SEGMENTS", "0"))
WEAVIATE_PQ_TRAINING_LIMIT = int(os.environ.get("WEAVIATE_PQ_TRAINING_LIMIT", "50000"))
WEAVIATE_PQ_BIT_COMPRESSION = os.environ.get("WEAVIATE_PQ_BIT_COMPRESSION", "0").strip() in {
    "1",
    "true",
    "True",
    "yes",
    "YES",
}
WEAVIATE_APPLY_HNSW_UPDATE = os.environ.get("WEAVIATE_APPLY_HNSW_UPDATE", "1").strip() not in {
    "0",
    "false",
    "False",
    "no",
    "NO",
}
WRITE_LMDB = os.environ.get("WRITE_LMDB", "1").strip() not in {"0", "false", "False", "no", "NO"}
STRICT_COLBERT_VECTORS = os.environ.get("STRICT_COLBERT_VECTORS", "0").strip() in {
    "1",
    "true",
    "True",
    "yes",
    "YES",
}
WEAVIATE_CONNECT_MODE = os.environ.get("WEAVIATE_CONNECT_MODE", "local").strip().lower() or "local"
WEAVIATE_LOCAL_HOST = os.environ.get("WEAVIATE_LOCAL_HOST", "localhost").strip() or "localhost"
WEAVIATE_LOCAL_PORT = int(os.environ.get("WEAVIATE_LOCAL_PORT", "8080"))
WEAVIATE_LOCAL_GRPC_PORT = int(os.environ.get("WEAVIATE_LOCAL_GRPC_PORT", "50051"))
WEAVIATE_HTTP_HOST = os.environ.get("WEAVIATE_HTTP_HOST", WEAVIATE_LOCAL_HOST).strip() or WEAVIATE_LOCAL_HOST
WEAVIATE_HTTP_PORT = int(os.environ.get("WEAVIATE_HTTP_PORT", str(WEAVIATE_LOCAL_PORT)))
WEAVIATE_GRPC_HOST = os.environ.get("WEAVIATE_GRPC_HOST", WEAVIATE_LOCAL_HOST).strip() or WEAVIATE_LOCAL_HOST
WEAVIATE_GRPC_PORT = int(os.environ.get("WEAVIATE_GRPC_PORT", str(WEAVIATE_LOCAL_GRPC_PORT)))
WEAVIATE_HTTP_SECURE = os.environ.get("WEAVIATE_HTTP_SECURE", "0").strip() in {
    "1",
    "true",
    "True",
    "yes",
    "YES",
}
WEAVIATE_GRPC_SECURE = os.environ.get("WEAVIATE_GRPC_SECURE", "0").strip() in {
    "1",
    "true",
    "True",
    "yes",
    "YES",
}
WEAVIATE_CLUSTER_URL = os.environ.get("WEAVIATE_CLUSTER_URL", "").strip()
WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY", "").strip()
WEAVIATE_TIMEOUT_INIT = float(os.environ.get("WEAVIATE_TIMEOUT_INIT", "10"))
WEAVIATE_TIMEOUT_QUERY = float(os.environ.get("WEAVIATE_TIMEOUT_QUERY", "60"))
WEAVIATE_TIMEOUT_INSERT = float(os.environ.get("WEAVIATE_TIMEOUT_INSERT", "300"))
_WEAVIATE_CLIENT_DEBUG_PRINTED = False

LMDB_VARIANT_PATHS = {
    "128_f32": LMDB_PATH_128_F32,
    "128_f16": LMDB_PATH_128_F16,
}
LMDB_WRITE_VARIANTS = {
    v.strip().lower() for v in os.environ.get("LMDB_WRITE_VARIANTS", "128_f16").split(",") if v.strip()
}
if TOKEN_VECTOR_DIM != 128:
    raise ValueError("store.py requires TOKEN_VECTOR_DIM=128.")
invalid_write_variants = {v for v in LMDB_WRITE_VARIANTS if "768" in v or v not in ALLOWED_VARIANTS}
if invalid_write_variants:
    raise ValueError(
        f"LMDB_WRITE_VARIANTS contains forbidden/unknown variants: {sorted(invalid_write_variants)}. "
        f"Allowed={sorted(ALLOWED_VARIANTS)}"
    )
PATENT_METADATA_EXCLUDE_KEYS = {
    "claim_id",
    "claim_number",
    "claim_type",
    "text",
    "chunk",
    "embedding",
    "colbert",
    "colbert_variants",
    "record_schema_version",
    "weaviate_claim_uuid",
    "weaviate_patent_uuid",
    "weaviate_claim_properties",
    "weaviate_patent_properties",
    "weaviate_named_vectors",
}
DATASET_LMDB_VECTOR_EXCLUDE_KEYS = {
    "embedding",
    "colbert",
    "colbert_variants",
    "weaviate_named_vectors",
}

PERSISTED_RECORD_SCHEMA_VERSION = 1
PARAMETER_SWEEP_RESET_COLLECTIONS = ("Claim", "Patent")


def _env_optional_int(name: str) -> int | None:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return None
    return int(str(raw).strip())


WEAVIATE_MUVERA_KSIM = _env_optional_int("WEAVIATE_MUVERA_KSIM")
WEAVIATE_MUVERA_DPROJECTIONS = _env_optional_int("WEAVIATE_MUVERA_DPROJECTIONS")
WEAVIATE_MUVERA_REPETITIONS = _env_optional_int("WEAVIATE_MUVERA_REPETITIONS")


def _util_shard_from_doc_id(doc_id: str | None) -> str | None:
    if not doc_id:
        return None
    digits = "".join(ch for ch in str(doc_id) if ch.isdigit())
    if len(digits) < 5:
        return None
    return f"UTIL{digits[:5]}"


def _normalize_util_shard(value: str | None) -> str | None:
    if not value:
        return None
    m = re.search(r"UTIL\d{5}", str(value).upper())
    return m.group(0) if m else None


def resolve_lmdb_path(variant: str, *, doc_id: str | None = None, dataset_shard: str | None = None) -> Path:
    variant = assert_128_variant(variant, context="resolve_lmdb_path")
    if variant not in LMDB_VARIANT_PATHS:
        raise ValueError(
            f"Unknown LMDB variant: {variant}. Allowed={sorted(LMDB_VARIANT_PATHS.keys())}"
        )
    return LMDB_VARIANT_PATHS[variant]


def _stable_uuid(kind: str, key: str) -> str:
    token = f"patent-wizard:{kind}:{(key or '').strip()}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, token))


def _claim_identity(emb: dict) -> str:
    claim_id = str(emb.get("claim_id") or "").strip()
    if claim_id:
        return claim_id
    doc_id = str(emb.get("doc_id") or "").strip()
    claim_number = emb.get("claim_number")
    if doc_id and claim_number is not None:
        return f"{doc_id}-CLM-{claim_number}"
    text = str(emb.get("text") or emb.get("chunk") or "").strip()
    if doc_id and text:
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
        return f"{doc_id}-TXT-{digest}"
    digest = hashlib.sha1(repr(sorted(emb.items())).encode("utf-8")).hexdigest()[:16]
    return f"CLAIM-{digest}"


def _to_jsonable(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    return str(value)


def _normalize_authors(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, tuple):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [a.strip() for a in value.split(";") if a.strip()]
    return []


def _build_patent_properties(emb: dict) -> dict:
    return {
        "doc_id": str(emb.get("doc_id") or "").strip(),
        "filing_date": str(emb.get("filing_date") or ""),
        "classification": str(emb.get("classification") or ""),
        "authors": _normalize_authors(emb.get("authors")),
        "title": str(emb.get("title") or ""),
        "kind": str(emb.get("kind") or ""),
    }


def _build_claim_properties(emb: dict) -> dict:
    claim_identity = _claim_identity(emb)
    claim_number = emb.get("claim_number")
    if isinstance(claim_number, str) and claim_number.isdigit():
        claim_number = int(claim_number)
    props = {
        "claim_id": str(emb.get("claim_id") or claim_identity),
        "claim_type": str(emb.get("claim_type") or ""),
        "doc_id": str(emb.get("doc_id") or ""),
        "text": str(emb.get("text") or emb.get("chunk") or ""),
    }
    if isinstance(claim_number, int):
        props["claim_number"] = claim_number
    return props


def _claim_uuid_for_record(emb: dict) -> str:
    explicit = str(emb.get("weaviate_claim_uuid") or "").strip()
    if explicit:
        return explicit
    return _stable_uuid("claim", _claim_identity(emb))


def _patent_uuid_for_record(emb: dict) -> str:
    explicit = str(emb.get("weaviate_patent_uuid") or "").strip()
    if explicit:
        return explicit
    return _stable_uuid("patent", str(emb.get("doc_id") or "").strip())


def _named_vectors_for_record(emb: dict) -> dict[str, list[list[float]]]:
    explicit = emb.get("weaviate_named_vectors")
    if isinstance(explicit, dict) and explicit:
        payload: dict[str, list[list[float]]] = {}
        for name, vecs in explicit.items():
            arr = np.asarray(vecs)
            if arr.ndim == 1:
                arr = arr.reshape(1, -1)
            if arr.ndim != 2 or arr.shape[0] <= 0 or arr.shape[1] != 128:
                raise ValueError(
                    f"Invalid named vector '{name}' for claim_id={_claim_identity(emb)}: shape={arr.shape}. "
                    "Expected [T,128]."
                )
            payload[str(name)] = arr.astype(np.float32, copy=False).tolist()
        return payload
    return {"colbert": _colbert_vectors_for_weaviate(emb)}


def prepare_embedding_record_for_storage(
    emb: dict,
    *,
    canonical_dataset_id: str | None = None,
) -> dict:
    """
    Enrich an embedded claim record with explicit Weaviate-ready fields.
    This keeps persisted dataset records self-contained for later upload.
    """
    record = dict(emb)
    if canonical_dataset_id and not record.get("canonical_dataset_id"):
        record["canonical_dataset_id"] = str(canonical_dataset_id)
    record.setdefault("record_schema_version", PERSISTED_RECORD_SCHEMA_VERSION)
    record["weaviate_patent_properties"] = record.get("weaviate_patent_properties") or _build_patent_properties(record)
    record["weaviate_claim_properties"] = record.get("weaviate_claim_properties") or _build_claim_properties(record)
    record["weaviate_patent_uuid"] = _patent_uuid_for_record(record)
    record["weaviate_claim_uuid"] = _claim_uuid_for_record(record)
    record["weaviate_named_vectors"] = record.get("weaviate_named_vectors") or _named_vectors_for_record(record)
    return record


def _build_patent_metadata_record(emb: dict) -> dict:
    doc_id = str(emb.get("doc_id") or "").strip()
    record: dict = {"doc_id": doc_id}
    for key, value in emb.items():
        if key in PATENT_METADATA_EXCLUDE_KEYS:
            continue
        if key == "authors" and isinstance(value, str):
            value = [a.strip() for a in value.split(";") if a.strip()]
        record[str(key)] = _to_jsonable(value)
    return record


def _open_lmdb_env(path: Path, *, readonly: bool = False) -> lmdb.Environment:
    path.parent.mkdir(parents=True, exist_ok=True)
    return lmdb.open(
        str(path),
        map_size=LMDB_MAP_SIZE,
        subdir=True,
        create=not readonly,
        lock=not readonly,
        readonly=readonly,
        readahead=False,
        max_dbs=1,
    )


def open_dataset_embeddings_lmdb(path: Path | str, *, readonly: bool = False) -> lmdb.Environment:
    return _open_lmdb_env(Path(path), readonly=readonly)


def write_dataset_embeddings_batch(
    lmdb_env: lmdb.Environment,
    embeddings: list[dict],
    *,
    canonical_dataset_id: str | None = None,
) -> dict[str, Any]:
    rows: list[tuple[str, bytes]] = []
    fieldnames: set[str] = set()
    vector_names: set[str] = set()
    doc_ids: set[str] = set()

    for emb in embeddings:
        prepared = prepare_embedding_record_for_storage(
            emb,
            canonical_dataset_id=canonical_dataset_id,
        )
        key = _dataset_embedding_storage_key(prepared)
        rows.append((key, _serialize_dataset_embedding_record(prepared)))
        doc_id = str(prepared.get("doc_id") or "").strip()
        if doc_id:
            doc_ids.add(doc_id)
        fieldnames.update(prepared.keys())
        vector_names.update((prepared.get("weaviate_named_vectors") or {"colbert": None}).keys())

    _write_lmdb_bytes(lmdb_env, rows)
    return {
        "record_count": len(rows),
        "doc_ids": doc_ids,
        "fieldnames": fieldnames,
        "vector_names": vector_names,
    }


def load_dataset_embeddings_from_lmdb(path: Path | str):
    env = open_dataset_embeddings_lmdb(path, readonly=True)
    try:
        with env.begin(write=False) as txn:
            cursor = txn.cursor()
            for _, payload in cursor:
                if payload is None:
                    continue
                yield _deserialize_dataset_embedding_record(payload)
    finally:
        env.close()


def dataset_embedding_entry_count(lmdb_env: lmdb.Environment) -> int:
    with lmdb_env.begin(write=False) as txn:
        stat = txn.stat()
    return int(stat.get("entries", 0))


def filter_new_dataset_embedding_records(
    lmdb_env: lmdb.Environment,
    records: list[dict],
) -> tuple[list[dict], int]:
    if not records:
        return [], 0
    pending: list[dict] = []
    skipped = 0
    with lmdb_env.begin(write=False) as txn:
        for record in records:
            key = str(record.get("weaviate_claim_uuid") or _claim_uuid_for_record(record)).encode("utf-8")
            if txn.get(key) is None:
                pending.append(record)
            else:
                skipped += 1
    return pending, skipped

def _serialize_colbert(vectors) -> bytes:
    buffer = io.BytesIO()
    if isinstance(vectors, dict) and "data" in vectors and "scale" in vectors:
        np.savez(buffer, data=vectors["data"], scale=vectors["scale"])
    else:
        arr = np.asarray(vectors)
        np.save(buffer, arr, allow_pickle=False)
    return buffer.getvalue()


def _serialize_json_record(record: dict) -> bytes:
    return json.dumps(_to_jsonable(record), ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _deserialize_json_record(payload: bytes) -> dict:
    try:
        value = json.loads(payload.decode("utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _dataset_embedding_storage_key(emb: dict) -> str:
    claim_uuid = str(emb.get("weaviate_claim_uuid") or "").strip()
    if claim_uuid:
        return claim_uuid
    return _claim_identity(emb)


def _dataset_embedding_metadata_record(emb: dict) -> dict:
    record: dict[str, Any] = {}
    for key, value in emb.items():
        if key in DATASET_LMDB_VECTOR_EXCLUDE_KEYS:
            continue
        record[str(key)] = _to_jsonable(value)
    return record


def _serialize_dataset_embedding_record(emb: dict) -> bytes:
    colbert_vectors = _select_full_colbert_vectors_for_lmdb(emb)
    if colbert_vectors is None or not getattr(colbert_vectors, "size", 0):
        raise ValueError(
            f"Dataset LMDB record missing token vectors for claim_id={_claim_identity(emb)} "
            f"doc_id={emb.get('doc_id', '')}"
        )
    metadata_json = json.dumps(
        _dataset_embedding_metadata_record(emb),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    buffer = io.BytesIO()
    np.savez(
        buffer,
        metadata=np.asarray(metadata_json),
        colbert=colbert_vectors.astype(np.float32, copy=False),
    )
    return buffer.getvalue()


def _deserialize_dataset_embedding_record(payload: bytes) -> dict:
    buffer = io.BytesIO(payload)
    obj = np.load(buffer, allow_pickle=False)
    try:
        metadata_raw = _np_scalar_to_str(obj["metadata"]) if "metadata" in obj else ""
        metadata = json.loads(metadata_raw) if metadata_raw else {}
        if not isinstance(metadata, dict):
            metadata = {}
        colbert = np.asarray(obj["colbert"]).astype(np.float32, copy=False)
        if colbert.ndim == 1:
            colbert = colbert.reshape(1, -1)
        metadata["colbert"] = colbert
        return metadata
    finally:
        if isinstance(obj, np.lib.npyio.NpzFile):
            obj.close()


def _select_full_colbert_vectors_for_lmdb(emb: dict) -> np.ndarray | None:
    variants = emb.get("colbert_variants") or {}
    for key in ("128_f32", "128_f16"):
        if key in variants:
            arr = np.asarray(variants[key])
            if arr.size:
                if arr.ndim == 1:
                    arr = arr.reshape(1, -1)
                if arr.ndim != 2 or arr.shape[1] != 128:
                    raise ValueError(
                        f"LMDB full-vector variant '{key}' must be [T,128], got shape={arr.shape}"
                    )
                return arr.astype(np.float32, copy=False)
    colbert_vectors = emb.get("colbert")
    if colbert_vectors is None:
        return None
    arr = np.asarray(colbert_vectors)
    if arr.size == 0:
        return None
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    if arr.ndim != 2 or arr.shape[1] != 128:
        raise ValueError(f"claim 'colbert' vectors must be [T,128], got shape={arr.shape}")
    return arr.astype(np.float32, copy=False)


def _serialize_claim_payload(payload: dict) -> bytes:
    vectors_value = payload.get("colbert")
    if vectors_value is None:
        vectors_value = payload.get("vectors")
    if vectors_value is None:
        raise ValueError("claim payload missing token vectors")
    vectors = np.asarray(vectors_value)
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)
    vectors = vectors.astype(np.float32, copy=False)
    buffer = io.BytesIO()
    np.savez(
        buffer,
        colbert=vectors,
        text=np.asarray(str(payload.get("text") or "")),
        doc_id=np.asarray(str(payload.get("doc_id") or "")),
        claim_type=np.asarray(str(payload.get("claim_type") or "")),
        claim_number=np.asarray(str(payload.get("claim_number") or "")),
    )
    return buffer.getvalue()


def _np_scalar_to_str(value) -> str:
    if isinstance(value, np.ndarray):
        if value.shape == ():
            return str(value.item())
        if value.size == 0:
            return ""
        return str(value.reshape(-1)[0])
    return str(value)


def _deserialize_claim_payload(payload: bytes) -> dict:
    buffer = io.BytesIO(payload)
    obj = np.load(buffer, allow_pickle=False)
    try:
        if not isinstance(obj, np.lib.npyio.NpzFile):
            arr = np.asarray(obj)
            if arr.ndim == 1:
                arr = arr.reshape(1, -1)
            return {
                "colbert": arr.astype(np.float32, copy=False),
                "text": "",
                "doc_id": "",
                "claim_type": "",
                "claim_number": "",
            }
        return {
            "colbert": np.asarray(obj["colbert"]).astype(np.float32, copy=False),
            "text": _np_scalar_to_str(obj["text"]),
            "doc_id": _np_scalar_to_str(obj["doc_id"]),
            "claim_type": _np_scalar_to_str(obj["claim_type"]),
            "claim_number": _np_scalar_to_str(obj["claim_number"]),
        }
    finally:
        if isinstance(obj, np.lib.npyio.NpzFile):
            obj.close()


def _colbert_vectors_for_weaviate(emb: dict) -> list[list[float]]:
    """
    Build the multi-vector payload for Weaviate from token-level 128-D ColBERT vectors.
    No fallback is allowed.
    """
    colbert_vectors = emb.get("colbert")
    if colbert_vectors is None:
        variants = emb.get("colbert_variants") or {}
        for key in ("128_f16", "128_f32"):
            if key in variants:
                colbert_vectors = variants[key]
                break

    if colbert_vectors is None:
        claim_identity = _claim_identity(emb)
        raise ValueError(
            f"Missing token-level ColBERT vectors for claim_id={claim_identity} "
            f"doc_id={emb.get('doc_id', '')}. 768 fallback is forbidden."
        )
    arr = np.asarray(colbert_vectors)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    if arr.ndim != 2 or arr.shape[0] <= 0 or arr.shape[1] != 128:
        claim_identity = _claim_identity(emb)
        raise ValueError(
            f"Invalid token-level ColBERT vectors for claim_id={claim_identity} "
            f"doc_id={emb.get('doc_id', '')}: shape={getattr(arr, 'shape', None)}. "
            "Expected [T,128]."
        )
    return arr.astype(np.float32, copy=False).tolist()


def _deserialize_colbert(payload: bytes) -> np.ndarray:
    buffer = io.BytesIO(payload)
    obj = np.load(buffer, allow_pickle=False)
    if isinstance(obj, np.lib.npyio.NpzFile):
        data = obj["data"]
        scale = obj["scale"]
        obj.close()
        return data.astype(np.float32) * scale
    return obj


def _write_lmdb_bytes(lmdb_env: lmdb.Environment, rows: list[tuple[str, bytes]]):
    if not rows:
        return
    while True:
        try:
            with lmdb_env.begin(write=True) as txn:
                for obj_id, payload in rows:
                    txn.put(obj_id.encode("utf-8"), payload)
            return
        except lmdb.MapFullError:
            current = lmdb_env.info()["map_size"]
            grow = LMDB_MAP_GROW_GB * 1024**3
            lmdb_env.set_mapsize(current + grow)
            print(f"[lmdb] MapFullError: increased map size to {current + grow:,} bytes")


def _write_lmdb_vectors(
    lmdb_env: lmdb.Environment,
    rows: list[tuple[str, list]],
):
    if not rows:
        return
    serialized = [(obj_id, _serialize_colbert(colbert_vectors)) for obj_id, colbert_vectors in rows]
    _write_lmdb_bytes(lmdb_env, serialized)


def _write_lmdb_json_records(lmdb_env: lmdb.Environment, rows: list[tuple[str, dict]]):
    if not rows:
        return
    serialized = [(obj_id, _serialize_json_record(record)) for obj_id, record in rows]
    _write_lmdb_bytes(lmdb_env, serialized)


def _write_lmdb_claim_payloads(lmdb_env: lmdb.Environment, rows: list[tuple[str, dict]]):
    if not rows:
        return
    serialized = [(obj_id, _serialize_claim_payload(record)) for obj_id, record in rows]
    _write_lmdb_bytes(lmdb_env, serialized)


def load_colbert_from_lmdb(lmdb_path: Path | str, key: str) -> np.ndarray | None:
    path = Path(lmdb_path)
    if not path.exists():
        return None
    env = _open_lmdb_env(path, readonly=True)
    try:
        with env.begin(write=False) as txn:
            payload = txn.get(str(key).encode("utf-8"))
            if payload is None:
                return None
            return _deserialize_colbert(payload)
    finally:
        env.close()


def load_patent_metadata_from_lmdb(doc_id: str) -> dict | None:
    if not doc_id:
        return None
    path = Path(LMDB_PATH_PATENT_METADATA)
    if not path.exists():
        return None
    env = _open_lmdb_env(path, readonly=True)
    try:
        with env.begin(write=False) as txn:
            payload = txn.get(str(doc_id).encode("utf-8"))
            if payload is None:
                return None
            return _deserialize_json_record(payload)
    finally:
        env.close()


def load_patent_metadata_batch_from_lmdb(doc_ids: list[str]) -> dict[str, dict]:
    ids = [str(d).strip() for d in doc_ids if str(d).strip()]
    if not ids:
        return {}
    path = Path(LMDB_PATH_PATENT_METADATA)
    if not path.exists():
        return {}
    env = _open_lmdb_env(path, readonly=True)
    try:
        out: dict[str, dict] = {}
        with env.begin(write=False) as txn:
            for doc_id in ids:
                payload = txn.get(doc_id.encode("utf-8"))
                if payload is not None:
                    out[doc_id] = _deserialize_json_record(payload)
        return out
    finally:
        env.close()


def load_claim_payload_from_lmdb(claim_id: str) -> dict | None:
    if not claim_id:
        return None
    path = Path(LMDB_PATH_CLAIM_PAYLOAD)
    if not path.exists():
        return None
    env = _open_lmdb_env(path, readonly=True)
    try:
        with env.begin(write=False) as txn:
            payload = txn.get(str(claim_id).encode("utf-8"))
            if payload is None:
                return None
            return _deserialize_claim_payload(payload)
    finally:
        env.close()


def load_claim_payloads_from_lmdb(claim_ids: list[str]) -> dict[str, dict]:
    ids = [str(c).strip() for c in claim_ids if str(c).strip()]
    if not ids:
        return {}
    path = Path(LMDB_PATH_CLAIM_PAYLOAD)
    if not path.exists():
        return {}
    env = _open_lmdb_env(path, readonly=True)
    try:
        out: dict[str, dict] = {}
        with env.begin(write=False) as txn:
            for claim_id in ids:
                payload = txn.get(claim_id.encode("utf-8"))
                if payload is not None:
                    out[claim_id] = _deserialize_claim_payload(payload)
        return out
    finally:
        env.close()


def get_client():
    global _WEAVIATE_CLIENT_DEBUG_PRINTED
    additional_config = AdditionalConfig(
        timeout=Timeout(
            init=WEAVIATE_TIMEOUT_INIT,
            query=WEAVIATE_TIMEOUT_QUERY,
            insert=WEAVIATE_TIMEOUT_INSERT,
        )
    )
    if WEAVIATE_CONNECT_MODE == "cloud":
        if not WEAVIATE_CLUSTER_URL:
            raise ValueError("WEAVIATE_CLUSTER_URL is required when WEAVIATE_CONNECT_MODE=cloud.")
        if not WEAVIATE_API_KEY:
            raise ValueError("WEAVIATE_API_KEY is required when WEAVIATE_CONNECT_MODE=cloud.")
        return weaviate.connect_to_weaviate_cloud(
            cluster_url=WEAVIATE_CLUSTER_URL,
            auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
            additional_config=additional_config,
        )
    if not _WEAVIATE_CLIENT_DEBUG_PRINTED:
        print(
            "[weaviate] connect_to_custom "
            f"http={WEAVIATE_HTTP_HOST}:{WEAVIATE_HTTP_PORT} "
            f"grpc={WEAVIATE_GRPC_HOST}:{WEAVIATE_GRPC_PORT} "
            f"http_secure={int(bool(WEAVIATE_HTTP_SECURE))} "
            f"grpc_secure={int(bool(WEAVIATE_GRPC_SECURE))}"
        )
        _WEAVIATE_CLIENT_DEBUG_PRINTED = True
    return weaviate.connect_to_custom(
        http_host=WEAVIATE_HTTP_HOST,
        http_port=WEAVIATE_HTTP_PORT,
        http_secure=WEAVIATE_HTTP_SECURE,
        grpc_host=WEAVIATE_GRPC_HOST,
        grpc_port=WEAVIATE_GRPC_PORT,
        grpc_secure=WEAVIATE_GRPC_SECURE,
        additional_config=additional_config,
    )


def _format_batch_errors(errors: Any, *, limit: int = 3) -> str:
    if isinstance(errors, dict):
        try:
            items = [errors[key] for key in sorted(errors)]
        except Exception:
            items = list(errors.values())
    else:
        try:
            items = list(errors or [])
        except Exception:
            items = [errors]
    if not items:
        return "unknown error"
    preview = " | ".join(str(item) for item in items[:limit])
    remaining = len(items) - min(len(items), limit)
    if remaining > 0:
        preview += f" | ... (+{remaining} more)"
    return preview


def _insert_many_with_retry(collection, objects: list[DataObject], *, kind: str) -> None:
    try:
        result = collection.data.insert_many(objects)
    except WeaviateBatchError as exc:
        message = str(exc).lower()
        if "deadline exceeded" in message and len(objects) > 1:
            midpoint = max(1, len(objects) // 2)
            print(
                f"[retry] {kind} batch of {len(objects)} hit gRPC deadline; "
                f"retrying as {midpoint}+{len(objects) - midpoint}"
            )
            _insert_many_with_retry(collection, objects[:midpoint], kind=kind)
            _insert_many_with_retry(collection, objects[midpoint:], kind=kind)
            return
        raise

    if getattr(result, "has_errors", False):
        error_text = _format_batch_errors(getattr(result, "errors", None))
        raise RuntimeError(
            f"{kind} insert_many had {len(getattr(result, 'errors', []) or [])} error(s) "
            f"for batch size {len(objects)}. {error_text}"
        )


def _resolved_muvera_params(overrides: dict | None = None) -> dict[str, int | None]:
    params = {
        "ksim": WEAVIATE_MUVERA_KSIM,
        "dprojections": WEAVIATE_MUVERA_DPROJECTIONS,
        "repetitions": WEAVIATE_MUVERA_REPETITIONS,
    }
    if overrides:
        for key in ("ksim", "dprojections", "repetitions"):
            if key in overrides and overrides[key] is not None:
                params[key] = int(overrides[key])
    return params


def _resolved_pq_params(overrides: dict | None = None) -> dict[str, int | bool]:
    params: dict[str, int | bool] = {
        "enabled": WEAVIATE_PQ_ENABLED,
        "centroids": WEAVIATE_PQ_CENTROIDS,
        "segments": WEAVIATE_PQ_SEGMENTS,
        "training_limit": WEAVIATE_PQ_TRAINING_LIMIT,
        "bit_compression": WEAVIATE_PQ_BIT_COMPRESSION,
    }
    if overrides:
        for key in ("enabled", "centroids", "segments", "training_limit", "bit_compression"):
            if key not in overrides or overrides[key] is None:
                continue
            if key in {"enabled", "bit_compression"}:
                params[key] = bool(overrides[key])
            else:
                params[key] = int(overrides[key])
    return params


def _claim_muvera_encoding(muvera_params: dict | None = None):
    params = _resolved_muvera_params(muvera_params)
    kwargs = {key: value for key, value in params.items() if value is not None}
    return Configure.VectorIndex.MultiVector.Encoding.muvera(**kwargs)


def _claim_hnsw_create_config(pq_params: dict | None = None):
    pq = _resolved_pq_params(pq_params)
    vector_cache_max_objects = (
        WEAVIATE_HNSW_VECTOR_CACHE_MAX_OBJECTS if WEAVIATE_HNSW_VECTOR_CACHE_MAX_OBJECTS > 0 else None
    )
    quantizer = None
    if bool(pq["enabled"]):
        pq_kwargs = {
            "centroids": int(pq["centroids"]),
            "training_limit": int(pq["training_limit"]),
            "bit_compression": bool(pq["bit_compression"]),
        }
        if int(pq["segments"]) > 0:
            pq_kwargs["segments"] = int(pq["segments"])
        quantizer = Configure.VectorIndex.Quantizer.pq(**pq_kwargs)
    return Configure.VectorIndex.hnsw(
        ef=WEAVIATE_HNSW_EF,
        dynamic_ef_min=WEAVIATE_HNSW_DYNAMIC_EF_MIN,
        dynamic_ef_max=WEAVIATE_HNSW_DYNAMIC_EF_MAX,
        dynamic_ef_factor=WEAVIATE_HNSW_DYNAMIC_EF_FACTOR,
        flat_search_cutoff=WEAVIATE_HNSW_FLAT_SEARCH_CUTOFF,
        vector_cache_max_objects=vector_cache_max_objects,
        quantizer=quantizer,
    )


def _claim_hnsw_update_config(pq_params: dict | None = None):
    if Reconfigure is None:
        return None
    pq = _resolved_pq_params(pq_params)
    vector_cache_max_objects = (
        WEAVIATE_HNSW_VECTOR_CACHE_MAX_OBJECTS if WEAVIATE_HNSW_VECTOR_CACHE_MAX_OBJECTS > 0 else None
    )
    pq_kwargs = {
        "enabled": bool(pq["enabled"]),
        "centroids": int(pq["centroids"]),
        "training_limit": int(pq["training_limit"]),
        "bit_compression": bool(pq["bit_compression"]),
    }
    if int(pq["segments"]) > 0:
        pq_kwargs["segments"] = int(pq["segments"])
    quantizer = Reconfigure.VectorIndex.Quantizer.pq(**pq_kwargs)
    return Reconfigure.VectorIndex.hnsw(
        ef=WEAVIATE_HNSW_EF,
        dynamic_ef_min=WEAVIATE_HNSW_DYNAMIC_EF_MIN,
        dynamic_ef_max=WEAVIATE_HNSW_DYNAMIC_EF_MAX,
        dynamic_ef_factor=WEAVIATE_HNSW_DYNAMIC_EF_FACTOR,
        flat_search_cutoff=WEAVIATE_HNSW_FLAT_SEARCH_CUTOFF,
        vector_cache_max_objects=vector_cache_max_objects,
        quantizer=quantizer,
    )


def _maybe_update_claim_hnsw(client, *, pq_params: dict | None = None):
    if not WEAVIATE_APPLY_HNSW_UPDATE:
        return
    if Reconfigure is None:
        print("[warn] weaviate Reconfigure API unavailable; skipping Claim HNSW update")
        return
    pq = _resolved_pq_params(pq_params)
    try:
        claim_collection = client.collections.get("Claim")
        claim_collection.config.update(
            vector_config=Reconfigure.Vectors.update(
                name="colbert",
                vector_index_config=_claim_hnsw_update_config(pq_params),
            )
        )
        print(
            "[config] Claim HNSW search config: "
            f"ef={WEAVIATE_HNSW_EF} "
            f"dynamicEf=[{WEAVIATE_HNSW_DYNAMIC_EF_MIN},{WEAVIATE_HNSW_DYNAMIC_EF_MAX}] "
            f"factor={WEAVIATE_HNSW_DYNAMIC_EF_FACTOR} "
            f"flatSearchCutoff={WEAVIATE_HNSW_FLAT_SEARCH_CUTOFF} "
            f"vectorCacheMaxObjects={WEAVIATE_HNSW_VECTOR_CACHE_MAX_OBJECTS or 'unchanged'} "
            f"pqEnabled={bool(pq['enabled'])} "
            f"pqCentroids={int(pq['centroids'])} "
            f"pqSegments={int(pq['segments']) or 'auto'} "
            f"pqTrainingLimit={int(pq['training_limit'])} "
            f"pqBitCompression={bool(pq['bit_compression'])}"
        )
    except Exception as e:
        print(f"[warn] Failed to update Claim HNSW search config: {e}")


def _ensure_collection_properties(client, collection_name: str, props: list[Property]):
    try:
        collection = client.collections.get(collection_name)
        cfg = collection.config.get()
        current_props = getattr(cfg, "properties", None) or []
        existing = {str(getattr(p, "name", "")) for p in current_props if getattr(p, "name", None)}
        for prop in props:
            prop_name = str(getattr(prop, "name", "") or "")
            if not prop_name or prop_name in existing:
                continue
            try:
                collection.config.add_property(prop)
                print(f"[config] Added missing property {collection_name}.{prop_name}")
            except Exception as e:
                print(f"[warn] Failed to add property {collection_name}.{prop_name}: {e}")
    except Exception as e:
        print(f"[warn] Could not verify properties for collection {collection_name}: {e}")


def ensure_collection(
    client,
    *,
    muvera_params: dict | None = None,
    pq_params: dict | None = None,
    update_existing_claim_hnsw: bool = True,
):
    existing = client.collections.list_all()
    claim_existed = "Claim" in existing

    patent_props = [
        Property(name="doc_id", data_type=DataType.TEXT),
        Property(name="filing_date", data_type=DataType.TEXT),
        Property(name="classification", data_type=DataType.TEXT),
        Property(name="authors", data_type=DataType.TEXT_ARRAY),
        Property(name="title", data_type=DataType.TEXT),
        Property(name="kind", data_type=DataType.TEXT),
    ]
    if "Patent" not in existing:
        client.collections.create(
            name="Patent",
            vectorizer_config=Configure.Vectorizer.none(),
            properties=patent_props,
        )
        print("Created collection: Patent")
    else:
        print("Collection Patent already exists")
        _ensure_collection_properties(client, "Patent", patent_props)

    claim_props = [
        Property(name="claim_id", data_type=DataType.TEXT),
        Property(name="claim_number", data_type=DataType.INT),
        Property(name="claim_type", data_type=DataType.TEXT),
        Property(name="doc_id", data_type=DataType.TEXT),
        Property(name="text", data_type=DataType.TEXT),
    ]
    if "Claim" not in existing:
        try:
            client.collections.create(
                name="Claim",
                properties=claim_props,
                vector_config=[
                    Configure.MultiVectors.self_provided(
                        name="colbert",
                        encoding=_claim_muvera_encoding(muvera_params),
                        vector_index_config=_claim_hnsw_create_config(pq_params),
                    ),
                ],
            )
            print("Created collection: Claim")
        except TypeError:
            client.collections.create(
                name="Claim",
                vectorizer_config=Configure.Vectorizer.none(),
                properties=claim_props,
            )
            print(
                "Created collection: Claim (warning: vector_config not supported by this "
                "weaviate-client version; MUVERA multi-vector config not applied)"
            )
    else:
        print("Collection Claim already exists")
        _ensure_collection_properties(client, "Claim", claim_props)

    if claim_existed and update_existing_claim_hnsw and "Claim" in client.collections.list_all():
        _maybe_update_claim_hnsw(client, pq_params=pq_params)


def reset_weaviate_state(
    *,
    reset_collections: tuple[str, ...] = PARAMETER_SWEEP_RESET_COLLECTIONS,
    muvera_params: dict | None = None,
    pq_params: dict | None = None,
) -> tuple[str, ...]:
    """
    Reset Patent and Claim for parameter sweeps.
    Claim alone is sufficient for retrieval correctness, but we reset Patent too because
    store_embeddings repopulates both collections and sweep disk-usage measurements are
    taken from the full Weaviate data directory.
    """
    client = get_client()
    try:
        existing = set(client.collections.list_all())
        deleted: list[str] = []
        for name in reset_collections:
            if name in existing:
                client.collections.delete(name)
                deleted.append(name)
                print(f"[reset] Deleted collection: {name}")
        ensure_collection(
            client,
            muvera_params=muvera_params,
            pq_params=pq_params,
            update_existing_claim_hnsw=False,
        )
        return tuple(deleted)
    finally:
        client.close()


def store_embeddings(
    embeddings,
    *,
    muvera_params: dict | None = None,
    pq_params: dict | None = None,
    write_lmdb: bool | None = None,
):
    client = get_client()
    lmdb_envs_by_path: dict[Path, lmdb.Environment] = {}
    try:
        ensure_collection(
            client,
            muvera_params=muvera_params,
            pq_params=pq_params,
            update_existing_claim_hnsw=False,
        )
        claim_collection = client.collections.get("Claim")
        patent_collection = client.collections.get("Patent")

        try:
            cfg = claim_collection.config.get().vector_config
            mv = None
            if isinstance(cfg, dict):
                mv = cfg.get("colbert")
            elif isinstance(cfg, list):
                for item in cfg:
                    if getattr(item, "name", None) == "colbert":
                        mv = item
                        break
            vector_index_cfg = getattr(mv, "vector_index_config", None) or getattr(mv, "vectorIndexConfig", None)
            multivector_cfg = getattr(vector_index_cfg, "multi_vector", None) or getattr(vector_index_cfg, "multivector", None)
            if not mv or not vector_index_cfg or not multivector_cfg:
                raise RuntimeError(
                    "Collection 'Claim' is not configured for multi-vector 'colbert'. "
                    "Set DROP_FIRST=True and recreate the collection."
                )
        except Exception:
            raise RuntimeError(
                "Unable to verify multi-vector config for 'colbert' in Claim. "
                "Upgrade weaviate-client and recreate the collection."
            )

        prepared_embeddings = [prepare_embedding_record_for_storage(emb) for emb in embeddings]
        write_lmdb_enabled = WRITE_LMDB if write_lmdb is None else bool(write_lmdb)

        print(f"Uploading {len(prepared_embeddings)} claim embeddings...")
        written_doc_ids: set[str] = set()
        patent_by_doc: dict[str, dict] = {}
        patent_uuid_by_doc: dict[str, str] = {}
        for emb in prepared_embeddings:
            patent_props = emb.get("weaviate_patent_properties") or _build_patent_properties(emb)
            doc_id = str(patent_props.get("doc_id") or emb.get("doc_id") or "").strip()
            if not doc_id or doc_id in patent_by_doc:
                continue
            patent_by_doc[doc_id] = patent_props
            patent_uuid_by_doc[doc_id] = _patent_uuid_for_record(emb)

        if patent_by_doc:
            patent_objects = [
                DataObject(
                    properties=props,
                    uuid=patent_uuid_by_doc.get(str(props.get("doc_id", "")).strip(), _stable_uuid("patent", str(props.get("doc_id", "")))),
                )
                for props in patent_by_doc.values()
            ]
            _insert_many_with_retry(patent_collection, patent_objects, kind="patent")

        for start in range(0, len(prepared_embeddings), WEAVIATE_BATCH_SIZE):
            batch = prepared_embeddings[start:start + WEAVIATE_BATCH_SIZE]
            objects = []
            for emb in batch:
                claim_identity = _claim_identity(emb)
                props = emb.get("weaviate_claim_properties") or _build_claim_properties(emb)
                vecs = _named_vectors_for_record(emb)
                objects.append(
                    DataObject(
                        properties=props,
                        vector=vecs,
                        uuid=_claim_uuid_for_record(emb),
                    )
                )

            _insert_many_with_retry(claim_collection, objects, kind="claim")

            lmdb_rows_by_path: dict[Path, list[tuple[str, list]]] = {}
            patent_metadata_rows: list[tuple[str, dict]] = []
            claim_payload_rows: list[tuple[str, dict]] = []
            for emb in batch:
                claim_key = _claim_identity(emb)
                doc_id = str(emb.get("doc_id") or "").strip()
                dataset_shard = emb.get("dataset_shard")

                if doc_id and doc_id not in written_doc_ids:
                    written_doc_ids.add(doc_id)
                    patent_metadata_rows.append((doc_id, _build_patent_metadata_record(emb)))

                claim_text = str(emb.get("text") or emb.get("chunk") or "")
                full_vectors = _select_full_colbert_vectors_for_lmdb(emb)
                if full_vectors is not None and full_vectors.size:
                    claim_payload_rows.append(
                        (
                            str(claim_key),
                            {
                                "text": claim_text,
                                "doc_id": doc_id,
                                "claim_type": str(emb.get("claim_type") or ""),
                                "claim_number": emb.get("claim_number"),
                                "colbert": full_vectors,
                            },
                        )
                    )

                if write_lmdb_enabled:
                    colbert_variants = emb.get("colbert_variants") or {}
                    if colbert_variants:
                        for name, vecs in colbert_variants.items():
                            name = str(name).lower()
                            if "768" in name:
                                raise ValueError(f"Forbidden 768 variant encountered during ingest: {name}")
                            if name not in LMDB_WRITE_VARIANTS:
                                continue
                            size = getattr(vecs, "size", None)
                            if size is None:
                                try:
                                    size = len(vecs)
                                except Exception:
                                    size = 0
                            if size:
                                key = str(claim_key)
                                lmdb_path = resolve_lmdb_path(
                                    name,
                                    doc_id=doc_id,
                                    dataset_shard=dataset_shard,
                                )
                                lmdb_rows_by_path.setdefault(lmdb_path, []).append((key, vecs))
                    else:
                        colbert_vectors = emb.get("colbert")
                        if colbert_vectors is not None:
                            size = getattr(colbert_vectors, "size", None)
                            if size is None:
                                try:
                                    size = len(colbert_vectors)
                                except Exception:
                                    size = 0
                            if size:
                                key = str(claim_key)
                                lmdb_path = resolve_lmdb_path(
                                    PRIMARY_COLBERT_VARIANT,
                                    doc_id=doc_id,
                                    dataset_shard=dataset_shard,
                                )
                                lmdb_rows_by_path.setdefault(lmdb_path, []).append((key, colbert_vectors))

            if write_lmdb_enabled and patent_metadata_rows:
                env = lmdb_envs_by_path.get(LMDB_PATH_PATENT_METADATA)
                if env is None:
                    env = _open_lmdb_env(LMDB_PATH_PATENT_METADATA)
                    lmdb_envs_by_path[LMDB_PATH_PATENT_METADATA] = env
                _write_lmdb_json_records(env, patent_metadata_rows)

            if write_lmdb_enabled and claim_payload_rows:
                env = lmdb_envs_by_path.get(LMDB_PATH_CLAIM_PAYLOAD)
                if env is None:
                    env = _open_lmdb_env(LMDB_PATH_CLAIM_PAYLOAD)
                    lmdb_envs_by_path[LMDB_PATH_CLAIM_PAYLOAD] = env
                _write_lmdb_claim_payloads(env, claim_payload_rows)

            if write_lmdb_enabled:
                for lmdb_path, rows in lmdb_rows_by_path.items():
                    if rows:
                        env = lmdb_envs_by_path.get(lmdb_path)
                        if env is None:
                            env = _open_lmdb_env(lmdb_path)
                            lmdb_envs_by_path[lmdb_path] = env
                        _write_lmdb_vectors(env, rows)

        print(f"Uploaded {len(prepared_embeddings)} claims to database.")
    finally:
        for env in lmdb_envs_by_path.values():
            env.close()
        client.close()

'''
# 10/27/2025 New store function: sends embeddings to weaviate. This sends it to the TEMPORARY   #
# CLUSTER, and thus will need to be updated when we create a local databse                      #

import weaviate
from weaviate.classes.config import Property, DataType
from weaviate.classes.init import Auth

def get_client():
    # This call connects to my cluster and that authenitcates connection w/API key.
    return weaviate.connect_to_weaviate_cloud(
        cluster_url="https://iyulz7xksmozhh8hzqf9w.c0.us-west3.gcp.weaviate.cloud",
        auth_credentials=Auth.api_key("enNFY0pkMGY5RENrcEljTV9lblU2UkV6U2JhZjBvZGFEWDQ2MnlHakNNWVE3VUIyTlFDRVdOQjA5WjVNPV92MjAw"),
    )

def ensure_collection(client):
    # .collections lets you use commands that manage collections.
    existing = client.collections.list_all()
    # Build a new collection if the collection does not already exist (Should run once.)
    if "PatentData" not in existing:
        client.collections.create(
            name="PatentData",
            vectorizer_config=None,  # since we're providing custom vectors
            properties=[
                Property(name="document_id", data_type=DataType.TEXT),      # For retrieving original patent 
                Property(name="chunk_index", data_type=DataType.INT),       # Number of chunk within patent
                Property(name="section", data_type=DataType.TEXT),          # Label for what section within patent
                Property(name="content", data_type=DataType.TEXT),          # Snippet of chunk text
                Property(name="priority_date", data_type=DataType.TEXT),    # Date patent was filed
                Property(name="cpc_code", data_type=DataType.TEXT),         # Contains information on patent classification
            ]
        )
        print("Created collection: PatentData")
    else:
        print("Collection PatentData already exists")


def store_embeddings(embeddings, chunks, metadata):
    client = get_client()
    ensure_collection(client)
    collection = client.collections.get("PatentData")

    print(f"Uploading {len(embeddings)} embeddings...")



    # docid, authors, filing date, classification, chunk, ## Added in embed --> ## chunk number, embeddings
    for i, emb in enumerate(embeddings):
        vector = emb["vector"]
        label = emb["label"]

        collection.data.insert(
            properties={
                "doc_id": metadata.get("doc_id", "unknown"),
                "chunk_index": i,
                "section": label,
                "content": chunks[i] if chunks else "",
                "priority_date": metadata.get("priority_date", ""),
                "code": metadata.get("code", "")
            },
            vector=vector.tolist()
        )

    print(f"Uploaded {len(embeddings)} chunks to cluster.")
    client.close()
'''

# 10/20/2025 Created basic store function. Only will store vectors in FAISS index.              #
# Takes in array of vectors from embed, then outputs them to an FAISS index.

'''
import faiss
import numpy as np

def store_embeddings(embeddings, index_path="patent_index.faiss"):
    """
    Stores the given embeddings in a FAISS index file.

    Parameters:
    embeddings (list or np.ndarray): List of embeddings from embed.py
    index_path (str): Path to save the FAISS index file
    """

    # Convert to a NumPy array if not already (Should already be in that form)
    if isinstance(embeddings, list):
        embeddings = np.vstack(embeddings)

    # Get embedding shape
    dim = embeddings.shape[1]

    # Create an index (Flat - basic index : IP - inner product)
    index = faiss.IndexFlatL2(dim)

    # Add vectors to index as float32 (necessary data type)
    index.add(embeddings.astype("float32"))

    # Save index to disk
    faiss.write_index(index, index_path)

    print(f"Stored {embeddings.shape[0]} embeddings in {index_path}")

    return index
'''
