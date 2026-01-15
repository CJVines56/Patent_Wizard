# New search, computes metrics given doc id and total chunks
"""
Helper script to run semantic searches against the PatentData collection
and optionally compute retrieval metrics for a single query.
"""

import argparse
import math

from weaviate.collections.classes.grpc import MetadataQuery

from embed import embed_query, model, tokenizer
from store import get_client


def compute_metrics(doc_ids, gold_doc_id: str, total_relevant: int):
    """
    Compute Precision@k, Recall@k, Hit@k, MRR, and nDCG@k for a single query.

    doc_ids: ordered list of doc_id strings from the search results
    gold_doc_id: the ground-truth patent doc_id
    total_relevant: total number of chunks for that patent (from your sheet)
    """
    k = len(doc_ids)
    if k == 0:
        return {
            "precision_at_k": 0.0,
            "recall_at_k": 0.0,
            "hit_at_k": 0.0,
            "mrr": 0.0,
            "ndcg_at_k": 0.0,
        }

    relevance = [1 if d == gold_doc_id else 0 for d in doc_ids]
    num_rel = sum(relevance)

    # Precision@k: how many of the top-k are relevant
    precision_at_k = num_rel / k

    # Recall@k: how many of all relevant items we recovered
    recall_at_k = (num_rel / total_relevant) if total_relevant > 0 else 0.0

    # Hit@k / Accuracy@k: did we get at least one relevant?
    hit_at_k = 1.0 if num_rel > 0 else 0.0

    # MRR: 1 / rank of the first relevant
    try:
        first_rel_rank = relevance.index(1) + 1  # ranks are 1-based
        mrr = 1.0 / first_rel_rank
    except ValueError:
        mrr = 0.0

    # nDCG@k: assume binary relevance
    dcg = 0.0
    for rank, rel in enumerate(relevance, start=1):
        if rel:
            dcg += 1.0 / math.log2(rank + 1)

    # Ideal DCG: all relevant items at the top, up to min(total_relevant, k)
    ideal_rel = min(total_relevant, k)
    idcg = 0.0
    for rank in range(1, ideal_rel + 1):
        idcg += 1.0 / math.log2(rank + 1)

    ndcg_at_k = (dcg / idcg) if idcg > 0 else 0.0

    return {
        "precision_at_k": precision_at_k,
        "recall_at_k": recall_at_k,
        "hit_at_k": hit_at_k,
        "mrr": mrr,
        "ndcg_at_k": ndcg_at_k,
    }


def search(query: str, limit: int = 5, gold_doc_id: str | None = None, total_relevant: int | None = None) -> None:
    """
    Embed the query text and run a nearest-neighbor search.
    If gold_doc_id and total_relevant are provided, also compute metrics.
    """
    query_vector = embed_query(query, tokenizer, model)[0].tolist()

    client = get_client()
    try:
        collection = client.collections.get("PatentData")
        result = collection.query.near_vector(
            near_vector=query_vector,
            limit=limit,
            return_metadata=MetadataQuery(distance=True, certainty=True),
        )
        if not result.objects:
            print("No matches.")
            return

        doc_ids_in_rank_order: list[str] = []

        print(f"Top {len(result.objects)} results for query: {query!r}")
        print("-" * 60)
        for idx, obj in enumerate(result.objects, 1):
            props = obj.properties or {}
            meta = obj.metadata
            distance = getattr(meta, "distance", None)
            certainty = getattr(meta, "certainty", None)

            doc_id = props.get("doc_id")
            section = props.get("section")
            doc_ids_in_rank_order.append(doc_id)

            print(f"{idx}. doc_id={doc_id} section={section}")
            if distance is not None or certainty is not None:
                dist_str = f"{distance:.4f}" if distance is not None else "n/a"
                cert_str = f"{certainty:.4f}" if certainty is not None else "n/a"
                print(f"   distance={dist_str} certainty={cert_str}")
            print(f"   chunk={props.get('content')}")
            print("-" * 60)

        # If we have golden info, compute metrics
        if gold_doc_id is not None and total_relevant is not None:
            metrics = compute_metrics(doc_ids_in_rank_order, gold_doc_id, total_relevant)
            print("\nMetrics (k = {}):".format(len(doc_ids_in_rank_order)))
            print(f"  Precision@k  = {metrics['precision_at_k']:.4f}")
            print(f"  Recall@k     = {metrics['recall_at_k']:.4f}")
            print(f"  Hit@k        = {metrics['hit_at_k']:.4f}")
            print(f"  MRR          = {metrics['mrr']:.4f}")
            print(f"  nDCG@k       = {metrics['ndcg_at_k']:.4f}")

    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic query over PatentData with optional metric computation.")
    parser.add_argument(
        "query",
        nargs="?",
        # ENTER QUERY BELOW #
        default="Golf club head produced by a 3D printing process where the body, face insert, and hosel are printed as a single integrated structure",
        help="Natural-language query to search for.",
    )
    parser.add_argument("--limit", type=int, default=10, help="How many matches to return.")

    # New: metric-related arguments
    parser.add_argument(
        "--gold-doc-id",        
        type=str,
        # ENTER DOC ID BELOW #
        default="12403362",
        help="Golden patent doc_id for this query (if provided, metrics will be computed).",
    )
    parser.add_argument(
        "--total-relevant",
        type=int,
        # ENTER TOTAL DOC CHUNKS BELOW #
        default=259,
        help="Total number of chunks for the golden patent (from your sheet).",
    )

    args = parser.parse_args()

    search(
        args.query,
        limit=args.limit,
        gold_doc_id=args.gold_doc_id,
        total_relevant=args.total_relevant,
    )


if __name__ == "__main__":
    main()





# Old search
'''
import argparse

from weaviate.collections.classes.grpc import MetadataQuery

from embed import embed_query, model, tokenizer
from store import get_client


def search(query: str, limit: int = 5) -> None:
    """Embed the query text and run a nearest-neighbor search."""
    query_vector = embed_query(query, tokenizer, model)[0].tolist()

    client = get_client()
    try:
        collection = client.collections.get("PatentData")
        result = collection.query.near_vector(
            near_vector=query_vector,
            limit=limit,
            return_metadata=MetadataQuery(distance=True, certainty=True),
        )
        if not result.objects:
            print("No matches.")
            return
        for idx, obj in enumerate(result.objects, 1):
            props = obj.properties or {}
            meta = obj.metadata
            distance = getattr(meta, "distance", None)
            certainty = getattr(meta, "certainty", None)
            print(f"{idx}. doc_id={props.get('doc_id')} section={props.get('section')}")
            # Note distance and certainty are weaviate metrics. Distance is literally straight line vector distance
            if distance is not None or certainty is not None:
                dist_str = f"{distance:.4f}" if distance is not None else "n/a"
                cert_str = f"{certainty:.4f}" if certainty is not None else "n/a"
                print(f"   distance={dist_str} certainty={cert_str}")
            print(f"   chunk={props.get('content')}")
            print("-" * 60)
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic query over PatentData.")
    parser.add_argument(
        "query",
        nargs="?",
        default="Imaging system for detecting robotic failure modes at different positions of a robot motion cycle",
        help="Natural-language query to search for.",
    )
    parser.add_argument("--limit", type=int, default=10, help="How many matches to return.")
    args = parser.parse_args()
    search(args.query, limit=args.limit)


if __name__ == "__main__":
    main()
'''