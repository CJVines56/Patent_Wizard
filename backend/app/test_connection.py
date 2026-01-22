"""
Utility script for ingest/export workflows.
- Build fake data for quick smoke tests.
- Run real ingestion of USPTO data, optionally exporting embeddings for offline storage.
- Re-import previously saved embeddings into Weaviate.
"""

import os
import json
import gzip
from pathlib import Path

from embed import (
    embed_chunks,
    tokenizer,
    model,
    save_embeddings_to_file,
    load_embeddings_into_weaviate,
)
from store import store_embeddings
from services.download import bulk_dataset_download, output_file as DOWNLOAD_DIR

EXPORT_PATH = Path(os.environ.get("EMBED_EXPORT_PATH", DOWNLOAD_DIR / "chunks_with_vectors.jsonl.gz"))


def _check_weaviate():
    try:
        from store import get_client
        c = get_client()
        c.collections.list_all()
        c.close()
    except Exception as e:
        raise RuntimeError(
            "Weaviate is not reachable. Start your local Weaviate instance and try again."
        ) from e


def build_fake_patent():
    """Return a list of dictionaries matching store.py fields."""
    base_meta = {
        "doc_id": "US20250001234A1",
        "priority_date": "2025-01-15",
        "authors": ["Alex Doe", "Jamie Smith", "Priya Patel"],
        "classification": "G06F17/30",
    }

    sections = [
        ("abstract", "An adaptive drafting assistant proposes structured patent claims in real time."),
        (
            "description.background",
            "Traditional workflows cause delays and inconsistencies between engineering and legal teams.",
        ),
        (
            "description.summary",
            "The system segments disclosures, embeds sections, and recommends claim templates by CPC.",
        ),
        (
            "description.embodiment",
            "Embeddings surface similar prior art sections for language reuse and consistency.",
        ),
        (
            "claims.1",
            "A method comprising: receiving a disclosure, generating vectors per section, matching to templates, and outputting draft claims.",
        ),
        (
            "claims.2",
            "The method of claim 1 wherein ranking incorporates semantic similarity to prior patents for inline citations.",
        ),
        ("claims.3", "The method of claim 1 further comprising exporting a claim tree with annotated references."),
    ]

    data = []
    for section_label, chunk_text in sections:
        data.append({
            **base_meta,
            "section": section_label,
            "chunk": chunk_text,
        })
    return data


def run_fake_ingest(show_preview_count=3, preview_head=5):
    fake_patent = build_fake_patent()
    embedded = embed_chunks(fake_patent, tokenizer, model)

    # Preview: show vector length and first few values for a few sections
    print(f"Embedded {len(embedded)} sections.")
    for i, rec in enumerate(embedded[:show_preview_count]):
        vec = rec.get("embedding") or []
        print(f"[{i}] section={rec['section']} vec_len={len(vec)} head={vec[:preview_head]}")

    # Store to Weaviate
    store_embeddings(embedded)
    print("Upload complete.")

def real_ingest(
    show_preview_count=3,
    preview_head=5,
    *,
    store=True,
    export_path: Path | None = None,
    ingest_batch_size: int | None = 512,
):
    """
    Download, embed, and optionally store/export real patent chunks.
    When `ingest_batch_size` is set, chunks stream through in batches so we never hold
    the entire dataset in memory at once.
    """
    preview_remaining = max(0, show_preview_count)
    total_embedded = 0
    export_handle = None
    export_target = None

    if export_path:
        export_target = Path(export_path)
        export_target.parent.mkdir(parents=True, exist_ok=True)
        if export_target.suffix == ".gz":
            export_handle = gzip.open(export_target, "wt", encoding="utf-8")
        else:
            export_handle = export_target.open("w", encoding="utf-8")

    def _record_batch(batch: list[dict]):
        nonlocal preview_remaining, total_embedded
        if not batch:
            return
        embedded = embed_chunks(batch, tokenizer, model)
        total_embedded += len(embedded)
        print(f"[ingest] Embedded batch of {len(embedded)} chunks (total {total_embedded})")

        if preview_remaining > 0:
            to_show = min(preview_remaining, len(embedded))
            start_idx = show_preview_count - preview_remaining
            for rel_idx in range(to_show):
                rec = embedded[rel_idx]
                vec = rec.get("embedding") or []
                print(
                    f"[preview {start_idx + rel_idx + 1}] "
                    f"section={rec.get('section')} vec_len={len(vec)} head={vec[:preview_head]}"
                )
            preview_remaining -= to_show

        if store:
            store_embeddings(embedded)
            print(f"[store] Uploaded {len(embedded)} chunk(s) to Weaviate.")
        if export_handle:
            for rec in embedded:
                export_handle.write(json.dumps(rec, ensure_ascii=False))
                export_handle.write("\n")

    try:
        if ingest_batch_size:
            bulk_dataset_download(
                "2025-09-01",
                DOWNLOAD_DIR,
                use_manifest=True,
                sample_k=0,
                return_chunks=False,
                batch_size=ingest_batch_size,
                on_batch=_record_batch,
            )
        else:
            chunks = bulk_dataset_download("2025-09-01", DOWNLOAD_DIR, use_manifest=True, sample_k=0)
            _record_batch(chunks)
    finally:
        if export_handle:
            export_handle.close()
            print(f"[export] Saved embeddings to {export_target}")


def import_exported_embeddings(path: Path | None = None, batch_size: int = 128):
    """Load saved embeddings from disk into Weaviate."""
    target = path or EXPORT_PATH
    load_embeddings_into_weaviate(target, batch_size=batch_size)


if __name__ == "__main__":
    # Optional: to clear and replace everything, set DROP_FIRST to True,
    # then run this script once. It deletes the entire PatentData class.
    DROP_FIRST = False
    if DROP_FIRST:
        from store import get_client
        c = get_client()
        try:
            c.collections.delete("PatentData")
            print("Deleted collection PatentData")
        except Exception as e:
            print(f"Delete failed: {e}")

    mode = os.environ.get("INGEST_MODE", "real-store").lower()
    if mode in {"fake", "real-store"}:
        _check_weaviate()
    if mode == "fake":
        run_fake_ingest()
    elif mode == "export":
        real_ingest(store=False, export_path=EXPORT_PATH)
    elif mode == "import":
        import_exported_embeddings()
    else:  # default real ingest + store
        real_ingest()
