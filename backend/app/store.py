
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
LMDB_PATH_128_F32 = Path(os.environ.get("LMDB_PATH_128_F32", _LMDB_DIR / "colbert_128_f32.lmdb"))
LMDB_PATH_128_F16 = Path(os.environ.get("LMDB_PATH_128_F16", _LMDB_DIR / "colbert_128_f16.lmdb"))
LMDB_MAP_SIZE = int(os.environ.get("LMDB_MAP_SIZE", str(10 * 1024**3)))
LMDB_MAP_GROW_GB = int(os.environ.get("LMDB_MAP_GROW_GB", "10"))
LMDB_VECTOR_DTYPE = os.environ.get(
    "TOKEN_VECTOR_DTYPE",
    os.environ.get("LMDB_VECTOR_DTYPE", "float16"),
).lower()
WEAVIATE_BATCH_SIZE = int(os.environ.get("WEAVIATE_BATCH_SIZE", "128"))

LMDB_VARIANT_PATHS = {
    "768_f32": LMDB_PATH_768_F32,
    "768_f16": LMDB_PATH_768_F16,
    "128_f32": LMDB_PATH_128_F32,
    "128_f16": LMDB_PATH_128_F16,
}


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
    arr = np.asarray(vectors)
    buffer = io.BytesIO()
    np.save(buffer, arr, allow_pickle=False)
    return buffer.getvalue()


def _deserialize_colbert(payload: bytes) -> np.ndarray:
    buffer = io.BytesIO(payload)
    return np.load(buffer, allow_pickle=False)


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
    env = _open_lmdb_env(Path(lmdb_path), readonly=True)
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
    lmdb_envs: dict[str, lmdb.Environment] = {
        name: _open_lmdb_env(path) for name, path in LMDB_VARIANT_PATHS.items()
    }
    lmdb_env_legacy = _open_lmdb_env(LMDB_PATH)
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
                DataObject(properties=props)
                for props in patent_by_doc.values()
            ]
            result = patent_collection.data.insert_many(patent_objects)
            if result.has_errors:
                print(f"[warn] patent batch insert had {len(result.errors)} error(s)")

        for start in range(0, len(embeddings), WEAVIATE_BATCH_SIZE):
            batch = embeddings[start:start + WEAVIATE_BATCH_SIZE]
            objects = []
            for i, emb in enumerate(batch):
                claim_number = emb.get("claim_number")
                if isinstance(claim_number, str) and claim_number.isdigit():
                    claim_number = int(claim_number)
                props = {
                    "claim_id": emb.get("claim_id", ""),
                    "claim_type": emb.get("claim_type", ""),
                    "doc_id": emb.get("doc_id", ""),
                    "text": emb.get("text") or emb.get("chunk", ""),
                }
                if isinstance(claim_number, int):
                    props["claim_number"] = claim_number
                dense_vec = emb.get("embedding", [])
                vecs = {"colbert": [dense_vec] if dense_vec else []}
                objects.append(DataObject(properties=props, vector=vecs))

            result = claim_collection.data.insert_many(objects)
            if result.has_errors:
                print(f"[warn] batch insert had {len(result.errors)} error(s)")

            lmdb_rows_by_variant: dict[str, list[tuple[str, list]]] = {
                name: [] for name in lmdb_envs.keys()
            }
            lmdb_rows_legacy: list[tuple[str, list]] = []
            for idx, obj_id in result.uuids.items():
                emb = batch[idx]
                colbert_variants = emb.get("colbert_variants") or {}
                if colbert_variants:
                    for name, vecs in colbert_variants.items():
                        if name not in lmdb_rows_by_variant:
                            continue
                        size = getattr(vecs, "size", None)
                        if size is None:
                            try:
                                size = len(vecs)
                            except Exception:
                                size = 0
                        if size:
                            lmdb_rows_by_variant[name].append((str(obj_id), vecs))
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
                            lmdb_rows_legacy.append((str(obj_id), colbert_vectors))
            for name, rows in lmdb_rows_by_variant.items():
                if rows:
                    _write_lmdb_vectors(lmdb_envs[name], rows)
            if lmdb_rows_legacy:
                _write_lmdb_vectors(lmdb_env_legacy, lmdb_rows_legacy)

        print(f"Uploaded {len(embeddings)} claims to database.")
    finally:
        for env in lmdb_envs.values():
            env.close()
        lmdb_env_legacy.close()
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
