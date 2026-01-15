from pathlib import Path

from embed import embed_query, tokenizer, model
from store import get_client, ensure_collection


def search_top_k(query: str, k: int = 10):
    # 1) Embed the query using your existing ColBERT model
    query_vec_2d = embed_query(query, tokenizer, model, max_length=256)
    # embed_query returns shape (1, D); Weaviate wants a flat list
    query_vector = query_vec_2d.flatten().tolist()

    # 2) Connect to Weaviate and get the PatentData collection
    client = get_client()
    try:
        ensure_collection(client)
        collection = client.collections.get("PatentData")

        # 3) Run nearest-vector search
        result = collection.query.near_vector(
            near_vector=query_vector,
            limit=k,
            return_metadata=["distance"],
        )

        # 4) Pretty-print results
        print(f"\nTop {k} results for: {query!r}\n" + "-" * 80)
        for rank, obj in enumerate(result.objects, start=1):
            props = obj.properties
            dist = getattr(obj.metadata, "distance", None)

            doc_id = props.get("doc_id", "")
            title = props.get("title", "")
            section = props.get("section", "")
            chunk_index = props.get("chunk_index", 0)
            content = props.get("content", "")

            print(f"#{rank}  distance={dist:.4f}" if dist is not None else f"#{rank}")
            print(f"  doc_id      : {doc_id}")
            print(f"  title       : {title}")
            print(f"  section     : {section}  |  chunk_index: {chunk_index}")
            print(f"  content     : {content[:300].replace('\\n', ' ')}{'...' if len(content) > 300 else ''}")
            print("-" * 80)
    finally:
        client.close()


if __name__ == "__main__":
    while True:
        q = input("\nEnter query (blank to exit): ").strip()
        if not q:
            break
        search_top_k(q, k=10)
