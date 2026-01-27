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
STATS_EVERY_BATCHES = int(os.environ.get("STATS_EVERY_BATCHES", "5"))
LMDB_VECTOR_DTYPE = os.environ.get(
    "TOKEN_VECTOR_DTYPE",
    os.environ.get("LMDB_VECTOR_DTYPE", "float16"),
).lower()
_BYTES_PER_FLOAT = 2 if LMDB_VECTOR_DTYPE == "float16" else 4


class _IngestStats:
    def __init__(self):
        self.batches = 0
        self.total_chunks = 0
        self.total_tokens = 0
        self.total_vectors = 0
        self.total_bytes = 0
        self.dim = None

    def update(self, embedded: list[dict]):
        self.batches += 1
        self.total_chunks += len(embedded)
        for rec in embedded:
            vecs = rec.get("colbert")
            if vecs is None:
                continue
            size = getattr(vecs, "size", None)
            if size is None:
                try:
                    size = len(vecs)
                except Exception:
                    size = 0
            if not size:
                continue
            if self.dim is None:
                self.dim = len(vecs[0])
            tok = len(vecs)
            self.total_tokens += tok
            self.total_vectors += 1
            self.total_bytes += tok * (self.dim or 0) * _BYTES_PER_FLOAT

    def maybe_log(self):
        if STATS_EVERY_BATCHES <= 0:
            return
        if self.batches % STATS_EVERY_BATCHES != 0:
            return
        avg_tokens = (self.total_tokens / self.total_vectors) if self.total_vectors else 0
        avg_bytes = (self.total_bytes / self.total_vectors) if self.total_vectors else 0
        gb = self.total_bytes / (1024 ** 3)
        print(
            f"[stats] batches={self.batches} chunks={self.total_chunks} "
            f"avg_tokens={avg_tokens:.1f} avg_vec_bytes={avg_bytes:,.0f} "
            f"dim={self.dim or 0} dtype={LMDB_VECTOR_DTYPE} "
            f"est_lmdb_gb={gb:.2f}"
        )


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


def build_fake_claims():
    """Return a list of claim dictionaries matching store.py fields."""
    base_meta = {
        "doc_id": "US20250001234A1",
        "filing_date": "2025-01-15",
        "authors": ["Alex Doe", "Jamie Smith", "Priya Patel"],
        "classification": "G06F17/30",
        "title": "Adaptive Drafting Assistant",
        "kind": "A1",
    }

    claims = [
        (
            1,
            "independent",
            "A method comprising: receiving a disclosure, generating vectors per section, matching to templates, and outputting draft claims.",
        ),
        (
            2,
            "dependent",
            "The method of claim 1 wherein ranking incorporates semantic similarity to prior patents for inline citations.",
        ),
        (
            3,
            "dependent",
            "The method of claim 1 further comprising exporting a claim tree with annotated references.",
        ),
    ]

    data = []
    for claim_number, claim_type, claim_text in claims:
        data.append({
            **base_meta,
            "section": "claim",
            "text": claim_text,
            "claim_id": f"{base_meta['doc_id']}-CLM-{claim_number}",
            "claim_number": claim_number,
            "claim_type": claim_type,
        })
    return data


def run_fake_ingest(show_preview_count=3, preview_head=5):
    fake_claims = build_fake_claims()
    embedded = embed_chunks(fake_claims, tokenizer, model)

    # Preview: show vector length and first few values for a few sections
    print(f"Embedded {len(embedded)} claims.")
    for i, rec in enumerate(embedded[:show_preview_count]):
        vec = rec.get("embedding") or []
        print(f"[{i}] claim_id={rec.get('claim_id')} vec_len={len(vec)} head={vec[:preview_head]}")

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
    stats = _IngestStats()

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
        stats.update(embedded)
        stats.maybe_log()

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
    DROP_FIRST = True
    if DROP_FIRST:
        from store import get_client
        c = get_client()
        try:
            try:
                c.collections.delete("Claim")
                print("Deleted collection Claim")
            except Exception as e:
                print(f"Delete failed: {e}")
            try:
                c.collections.delete("Patent")
                print("Deleted collection Patent")
            except Exception as e:
                print(f"Delete failed: {e}")
        finally:
            c.close()

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
