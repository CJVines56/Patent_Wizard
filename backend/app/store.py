
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
import weaviate
from weaviate.classes.config import Property, DataType
from weaviate.classes.init import Auth

def get_client():
    return weaviate.connect_to_local(
        host="localhost",
        port=8080,
        grpc_port=50051,
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
                Property(name="doc_id", data_type=DataType.TEXT),      # For retrieving original patent 
                Property(name="chunk_index", data_type=DataType.INT),       # Number of chunk within patent
                Property(name="section", data_type=DataType.TEXT),          # Label for what section within patent
                Property(name="content", data_type=DataType.TEXT),          # Snippet of chunk text
                Property(name="priority_date", data_type=DataType.TEXT),    # Date patent was filed
                Property(name="classification", data_type=DataType.TEXT),         # Contains information on patent classification
                Property(name="authors", data_type=DataType.TEXT_ARRAY),
                Property(name="title", data_type=DataType.TEXT),
                Property(name="kind", data_type=DataType.TEXT),
            ]
        )
        print("Created collection: PatentData")
    else:
        print("Collection PatentData already exists")

def _normalize_authors(value):
    # Weaviate wants a list of strings for TEXT_ARRAY
    if value is None:
        return []
    if isinstance(value, list):
        # ensure everything is str
        return [str(a) for a in value]
    # if it's a single string (or anything else), wrap it in a list
    return [str(value)]

def store_embeddings(embeddings):
    client = get_client()
    ensure_collection(client)
    collection = client.collections.get("PatentData")

    print(f"Uploading {len(embeddings)} embeddings...")

    # docid, authors, filing date, classification, chunk, ## Added in embed --> ## label, embeddings
    for i, emb in enumerate(embeddings):
        vector = emb.get("embedding", [])
        if hasattr(vector, "tolist"):
            vector = vector.tolist()

        collection.data.insert(
            properties={
                "chunk_index": i,
                "doc_id": emb.get("doc_id", ""),
                "authors": _normalize_authors(emb.get("authors", [])),
                "priority_date": emb.get("priority_date", ""),
                "classification": emb.get("classification", ""),
                "content": emb.get("chunk", ""),
                "section": emb.get("section", ""),

                "title": emb.get("title", ""),
                "kind": emb.get("kind", "")
            },
            vector=vector,
        )

    print(f"Uploaded {len(embeddings)} chunks to database.")
    client.close()

def clear_patentdata():
    """
    Drop and recreate the PatentData collection.
    Use this before re-loading embeddings to start fresh.
    """
    client = get_client()
    try:
        # list_all() returns a list of collection names (strings) in this client version
        existing = set(client.collections.list_all())

        if "PatentData" in existing:
            print("Dropping PatentData collection...")
            client.collections.delete("PatentData")
            print("PatentData collection dropped.")

        ensure_collection(client)
        print("PatentData collection recreated (empty).")
    finally:
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
