
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

import lmdb
import numpy as np
import weaviate
from weaviate.collections.classes.data import DataObject
from weaviate.classes.config import Property, DataType, Configure
from weaviate.classes.init import Auth
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
}


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
    return weaviate.connect_to_local(
        host="localhost",
        port=8080,
        grpc_port=50051,
    )


def _claim_hnsw_create_config():
    vector_cache_max_objects = (
        WEAVIATE_HNSW_VECTOR_CACHE_MAX_OBJECTS if WEAVIATE_HNSW_VECTOR_CACHE_MAX_OBJECTS > 0 else None
    )
    quantizer = None
    if WEAVIATE_PQ_ENABLED:
        pq_kwargs = {
            "centroids": WEAVIATE_PQ_CENTROIDS,
            "training_limit": WEAVIATE_PQ_TRAINING_LIMIT,
            "bit_compression": WEAVIATE_PQ_BIT_COMPRESSION,
        }
        if WEAVIATE_PQ_SEGMENTS > 0:
            pq_kwargs["segments"] = WEAVIATE_PQ_SEGMENTS
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


def _claim_hnsw_update_config():
    if Reconfigure is None:
        return None
    vector_cache_max_objects = (
        WEAVIATE_HNSW_VECTOR_CACHE_MAX_OBJECTS if WEAVIATE_HNSW_VECTOR_CACHE_MAX_OBJECTS > 0 else None
    )
    pq_kwargs = {
        "enabled": WEAVIATE_PQ_ENABLED,
        "centroids": WEAVIATE_PQ_CENTROIDS,
        "training_limit": WEAVIATE_PQ_TRAINING_LIMIT,
        "bit_compression": WEAVIATE_PQ_BIT_COMPRESSION,
    }
    if WEAVIATE_PQ_SEGMENTS > 0:
        pq_kwargs["segments"] = WEAVIATE_PQ_SEGMENTS
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


def _maybe_update_claim_hnsw(client):
    if not WEAVIATE_APPLY_HNSW_UPDATE:
        return
    if Reconfigure is None:
        print("[warn] weaviate Reconfigure API unavailable; skipping Claim HNSW update")
        return
    try:
        claim_collection = client.collections.get("Claim")
        claim_collection.config.update(
            vector_config=Reconfigure.Vectors.update(
                name="colbert",
                vector_index_config=_claim_hnsw_update_config(),
            )
        )
        print(
            "[config] Claim HNSW search config: "
            f"ef={WEAVIATE_HNSW_EF} "
            f"dynamicEf=[{WEAVIATE_HNSW_DYNAMIC_EF_MIN},{WEAVIATE_HNSW_DYNAMIC_EF_MAX}] "
            f"factor={WEAVIATE_HNSW_DYNAMIC_EF_FACTOR} "
            f"flatSearchCutoff={WEAVIATE_HNSW_FLAT_SEARCH_CUTOFF} "
            f"vectorCacheMaxObjects={WEAVIATE_HNSW_VECTOR_CACHE_MAX_OBJECTS or 'unchanged'} "
            f"pqEnabled={WEAVIATE_PQ_ENABLED} "
            f"pqCentroids={WEAVIATE_PQ_CENTROIDS} "
            f"pqSegments={WEAVIATE_PQ_SEGMENTS or 'auto'} "
            f"pqTrainingLimit={WEAVIATE_PQ_TRAINING_LIMIT}"
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


def ensure_collection(client):
    existing = client.collections.list_all()

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
                        encoding=Configure.VectorIndex.MultiVector.Encoding.muvera(),
                        vector_index_config=_claim_hnsw_create_config(),
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

    if "Claim" in client.collections.list_all():
        _maybe_update_claim_hnsw(client)


def store_embeddings(embeddings):
    client = get_client()
    lmdb_envs_by_path: dict[Path, lmdb.Environment] = {}
    try:
        ensure_collection(client)
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

        print(f"Uploading {len(embeddings)} claim embeddings...")
        written_doc_ids: set[str] = set()
        patent_by_doc: dict[str, dict] = {}
        for emb in embeddings:
            doc_id = str(emb.get("doc_id") or "").strip()
            if not doc_id or doc_id in patent_by_doc:
                continue
            authors = emb.get("authors", [])
            if isinstance(authors, str):
                authors = [a.strip() for a in authors.split(";") if a.strip()]
            patent_by_doc[doc_id] = {
                "doc_id": doc_id,
                "filing_date": emb.get("filing_date", ""),
                "classification": emb.get("classification", ""),
                "authors": authors if isinstance(authors, list) else [],
                "title": emb.get("title", ""),
                "kind": emb.get("kind", ""),
            }

        if patent_by_doc:
            patent_objects = [
                DataObject(
                    properties=props,
                    uuid=_stable_uuid("patent", str(props.get("doc_id", ""))),
                )
                for props in patent_by_doc.values()
            ]
            result = patent_collection.data.insert_many(patent_objects)
            if result.has_errors:
                print(f"[warn] patent batch insert had {len(result.errors)} error(s)")

        for start in range(0, len(embeddings), WEAVIATE_BATCH_SIZE):
            batch = embeddings[start:start + WEAVIATE_BATCH_SIZE]
            objects = []
            for emb in batch:
                claim_identity = _claim_identity(emb)
                claim_number = emb.get("claim_number")
                if isinstance(claim_number, str) and claim_number.isdigit():
                    claim_number = int(claim_number)
                props = {
                    "claim_id": emb.get("claim_id", "") or claim_identity,
                    "claim_type": emb.get("claim_type", ""),
                    "doc_id": emb.get("doc_id", ""),
                    "text": emb.get("text") or emb.get("chunk", ""),
                }
                if isinstance(claim_number, int):
                    props["claim_number"] = claim_number
                vecs = {"colbert": _colbert_vectors_for_weaviate(emb)}
                objects.append(
                    DataObject(
                        properties=props,
                        vector=vecs,
                        uuid=_stable_uuid("claim", claim_identity),
                    )
                )

            result = claim_collection.data.insert_many(objects)
            if result.has_errors:
                print(f"[warn] batch insert had {len(result.errors)} error(s)")

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

                if WRITE_LMDB:
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

            if patent_metadata_rows:
                env = lmdb_envs_by_path.get(LMDB_PATH_PATENT_METADATA)
                if env is None:
                    env = _open_lmdb_env(LMDB_PATH_PATENT_METADATA)
                    lmdb_envs_by_path[LMDB_PATH_PATENT_METADATA] = env
                _write_lmdb_json_records(env, patent_metadata_rows)

            if claim_payload_rows:
                env = lmdb_envs_by_path.get(LMDB_PATH_CLAIM_PAYLOAD)
                if env is None:
                    env = _open_lmdb_env(LMDB_PATH_CLAIM_PAYLOAD)
                    lmdb_envs_by_path[LMDB_PATH_CLAIM_PAYLOAD] = env
                _write_lmdb_claim_payloads(env, claim_payload_rows)

            if WRITE_LMDB:
                for lmdb_path, rows in lmdb_rows_by_path.items():
                    if rows:
                        env = lmdb_envs_by_path.get(lmdb_path)
                        if env is None:
                            env = _open_lmdb_env(lmdb_path)
                            lmdb_envs_by_path[lmdb_path] = env
                        _write_lmdb_vectors(env, rows)

        print(f"Uploaded {len(embeddings)} claims to database.")
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
