# temp_loader.py (or whatever file you're using to run the load)

from pathlib import Path
from embed import load_embeddings_from_file
from store import store_embeddings, clear_patentdata  # using new helper


def load_patents_into_weaviate(
    path: Path,
    n_patents: int | None = 100,
    batch_size: int = 128,
):
    seen_doc_ids = set()
    buffer = []
    total_chunks = 0
    flushed_chunks = 0

    print(f"[loader] Reading from: {path}")
    print(f"[loader] Target patents: {n_patents if n_patents is not None else 'ALL'}")
    print(f"[loader] Batch size: {batch_size}")

    for record in load_embeddings_from_file(path):
        doc_id = record.get("doc_id")

        # New patent encountered
        if doc_id not in seen_doc_ids:
            # Stop if we have hit the patent limit (if any)
            if n_patents is not None and len(seen_doc_ids) >= n_patents:
                print("[loader] Reached target number of patents, stopping.")
                break

            seen_doc_ids.add(doc_id)
            print(f"[loader] Now processing patent {len(seen_doc_ids)}"
                  f"{'/' + str(n_patents) if n_patents is not None else ''}: {doc_id}")

        buffer.append(record)
        total_chunks += 1

        # Flush batch to Weaviate
        if len(buffer) >= batch_size:
            store_embeddings(buffer)
            flushed_chunks += len(buffer)
            buffer.clear()
            print(f"[loader] Flushed {flushed_chunks} chunks so far "
                  f"(patents seen: {len(seen_doc_ids)})")

    # Flush remaining records
    if buffer:
        store_embeddings(buffer)
        flushed_chunks += len(buffer)
        print(f"[loader] Final flush: total {flushed_chunks} chunks")

    print(f"[loader] DONE. Uploaded {flushed_chunks} chunks "
          f"from {len(seen_doc_ids)} patents.")


if __name__ == "__main__":
    jsonl_path = Path(r"C:\ECEN_403\Patent_Wizard\backend\app\chunks_with_vectors.jsonl")

    # 1) Clear existing data if you want a clean slate
    clear_patentdata()

    # 2) Load as many patents as you want
    #    - n_patents=100 for a subset
    #    - n_patents=None to stream the entire file
    load_patents_into_weaviate(
        jsonl_path,
        n_patents=None,        # None = load ALL patents in the file
        batch_size=128,
    )


'''
from pathlib import Path
from embed import load_embeddings_from_file
from store import store_embeddings  # adjust import path if needed


def load_first_n_patents_into_weaviate(path: Path, n_patents: int = 100, batch_size: int = 128):
    seen_doc_ids = set()
    buffer = []
    total_chunks = 0

    for record in load_embeddings_from_file(path):
        doc_id = record.get("doc_id")

        # Stop once we have reached N unique patents
        if doc_id not in seen_doc_ids:
            if len(seen_doc_ids) >= n_patents:
                break
            seen_doc_ids.add(doc_id)

        buffer.append(record)

        # Batch flush
        if len(buffer) >= batch_size:
            store_embeddings(buffer)
            total_chunks += len(buffer)
            buffer.clear()

    # Flush remaining records
    if buffer:
        store_embeddings(buffer)
        total_chunks += len(buffer)

    print(f"[partial upload] Uploaded {total_chunks} chunks from {len(seen_doc_ids)} patents.")


if __name__ == "__main__":
    jsonl_path = Path("chunks_with_vectors.jsonl")  # adjust if elsewhere
    load_first_n_patents_into_weaviate(jsonl_path, n_patents=100, batch_size=128)
'''