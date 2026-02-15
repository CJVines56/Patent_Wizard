
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

_LMDB_DIR = Path(__file__).resolve().parents[1] / "lmdb"
LMDB_PATH = Path(os.environ.get("LMDB_PATH", _LMDB_DIR / "colbert_vectors.lmdb"))
LMDB_PATH_768_F32 = Path(os.environ.get("LMDB_PATH_768_F32", _LMDB_DIR / "colbert_768_f32.lmdb"))
LMDB_PATH_768_F16 = Path(os.environ.get("LMDB_PATH_768_F16", _LMDB_DIR / "colbert_768_f16.lmdb"))
LMDB_PATH_768_I8 = Path(os.environ.get("LMDB_PATH_768_I8", _LMDB_DIR / "colbert_768_i8.lmdb"))
LMDB_PATH_128_F32 = Path(os.environ.get("LMDB_PATH_128_F32", _LMDB_DIR / "colbert_128_f32.lmdb"))
LMDB_PATH_128_F16 = Path(os.environ.get("LMDB_PATH_128_F16", _LMDB_DIR / "colbert_128_f16.lmdb"))
LMDB_SHARD_ROOT_768_F16 = Path(
    os.environ.get("LMDB_SHARD_ROOT_768_F16", _LMDB_DIR / "colbert_768_f16_shards")
)
LMDB_SHARDING_MODE = os.environ.get("LMDB_SHARDING_MODE", "util").strip().lower()
LMDB_MAP_SIZE = int(os.environ.get("LMDB_MAP_SIZE", str(10 * 1024**3)))
LMDB_MAP_GROW_GB = int(os.environ.get("LMDB_MAP_GROW_GB", "10"))
LMDB_VECTOR_DTYPE = os.environ.get(
    "TOKEN_VECTOR_DTYPE",
    os.environ.get("LMDB_VECTOR_DTYPE", "float16"),
).lower()
WEAVIATE_BATCH_SIZE = int(os.environ.get("WEAVIATE_BATCH_SIZE", "128"))
WRITE_LMDB = os.environ.get("WRITE_LMDB", "1").strip() not in {"0", "false", "False", "no", "NO"}

LMDB_VARIANT_PATHS = {
    "768_f32": LMDB_PATH_768_F32,
    "768_f16": LMDB_PATH_768_F16,
    "768_i8": LMDB_PATH_768_I8,
    "128_f32": LMDB_PATH_128_F32,
    "128_f16": LMDB_PATH_128_F16,
}
LMDB_WRITE_VARIANTS = {
    v.strip().lower() for v in os.environ.get("LMDB_WRITE_VARIANTS", "768_f16").split(",") if v.strip()
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
    variant = variant.lower()
    if variant not in LMDB_VARIANT_PATHS:
        raise ValueError(f"Unknown LMDB variant: {variant}")
    if variant == "768_f16" and LMDB_SHARDING_MODE == "util":
        shard = _normalize_util_shard(dataset_shard) or _util_shard_from_doc_id(doc_id)
        if shard:
            return LMDB_SHARD_ROOT_768_F16 / shard / "colbert_768_f16.lmdb"
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


def _deserialize_colbert(payload: bytes) -> np.ndarray:
    buffer = io.BytesIO(payload)
    obj = np.load(buffer, allow_pickle=False)
    if isinstance(obj, np.lib.npyio.NpzFile):
        data = obj["data"]
        scale = obj["scale"]
        obj.close()
        return data.astype(np.float32) * scale
    return obj


def _write_lmdb_vectors(
    lmdb_env: lmdb.Environment,
    rows: list[tuple[str, list]],
):
    if not rows:
        return
    while True:
        try:
            with lmdb_env.begin(write=True) as txn:
                for obj_id, colbert_vectors in rows:
                    payload = _serialize_colbert(colbert_vectors)
                    txn.put(obj_id.encode("utf-8"), payload)
            return
        except lmdb.MapFullError:
            current = lmdb_env.info()["map_size"]
            grow = LMDB_MAP_GROW_GB * 1024**3
            lmdb_env.set_mapsize(current + grow)
            print(f"[lmdb] MapFullError: increased map size to {current + grow:,} bytes")


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


def get_client():
    return weaviate.connect_to_local(
        host="localhost",
        port=8080,
        grpc_port=50051,
    )


def ensure_collection(client):
    existing = client.collections.list_all()

    if "Patent" not in existing:
        props = [
            Property(name="doc_id", data_type=DataType.TEXT),
            Property(name="filing_date", data_type=DataType.TEXT),
            Property(name="classification", data_type=DataType.TEXT),
            Property(name="authors", data_type=DataType.TEXT_ARRAY),
            Property(name="title", data_type=DataType.TEXT),
            Property(name="kind", data_type=DataType.TEXT),
        ]
        client.collections.create(
            name="Patent",
            vectorizer_config=Configure.Vectorizer.none(),
            properties=props,
        )
        print("Created collection: Patent")
    else:
        print("Collection Patent already exists")

    if "Claim" not in existing:
        props = [
            Property(name="claim_id", data_type=DataType.TEXT),
            Property(name="claim_number", data_type=DataType.INT),
            Property(name="claim_type", data_type=DataType.TEXT),
            Property(name="doc_id", data_type=DataType.TEXT),
            Property(name="text", data_type=DataType.TEXT),
        ]
        try:
            client.collections.create(
                name="Claim",
                properties=props,
                vector_config=[
                    Configure.MultiVectors.self_provided(
                        name="colbert",
                        encoding=Configure.VectorIndex.MultiVector.Encoding.muvera(),
                    ),
                ],
            )
            print("Created collection: Claim")
        except TypeError:
            client.collections.create(
                name="Claim",
                vectorizer_config=Configure.Vectorizer.none(),
                properties=props,
            )
            print(
                "Created collection: Claim (warning: vector_config not supported by this "
                "weaviate-client version; MUVERA multi-vector config not applied)"
            )
    else:
        print("Collection Claim already exists")


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

        patent_by_doc: dict[str, dict] = {}
        for emb in embeddings:
            doc_id = emb.get("doc_id")
            if not doc_id or doc_id in patent_by_doc:
                continue
            authors = emb.get("authors", [])
            if isinstance(authors, str):
                authors = [a.strip() for a in authors.split(";") if a.strip()]
            patent_by_doc[doc_id] = {
                "doc_id": doc_id,
                "filing_date": emb.get("filing_date", ""),
                "classification": emb.get("classification", ""),
                "authors": authors,
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
            for i, emb in enumerate(batch):
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
                dense_vec = emb.get("embedding", [])
                vecs = {"colbert": [dense_vec] if dense_vec else []}
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

            if WRITE_LMDB:
                lmdb_rows_by_path: dict[Path, list[tuple[str, list]]] = {}
                for emb in batch:
                    claim_key = _claim_identity(emb)
                    doc_id = emb.get("doc_id")
                    dataset_shard = emb.get("dataset_shard")
                    colbert_variants = emb.get("colbert_variants") or {}
                    if colbert_variants:
                        for name, vecs in colbert_variants.items():
                            name = str(name).lower()
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
                                    "768_f16",
                                    doc_id=doc_id,
                                    dataset_shard=dataset_shard,
                                )
                                lmdb_rows_by_path.setdefault(lmdb_path, []).append((key, colbert_vectors))
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
