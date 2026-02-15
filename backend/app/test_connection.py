"""
Utility script for ingest/export workflows.
- Build fake data for quick smoke tests.
- Run real ingestion of USPTO data, optionally exporting embeddings for offline storage.
- Re-import previously saved embeddings into Weaviate.
"""

import os
import json
import gzip
import time
import subprocess
from datetime import datetime, timedelta
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
EST_TOTAL_BATCHES = int(os.environ.get("EST_TOTAL_BATCHES", "0"))
LMDB_VECTOR_DTYPE = os.environ.get(
    "TOKEN_VECTOR_DTYPE",
    os.environ.get("LMDB_VECTOR_DTYPE", "float16"),
).lower()
_BYTES_PER_FLOAT = 2 if LMDB_VECTOR_DTYPE == "float16" else 4


def _build_weekly_dates(start_date: str, weeks_back: int) -> list[str]:
    anchor = datetime.strptime(start_date, "%Y-%m-%d")
    count = max(0, int(weeks_back))
    return [
        (anchor - timedelta(days=7 * i)).strftime("%Y-%m-%d")
        for i in range(count + 1)
    ]


def _compact_util_shards(util_shards: set[str]) -> None:
    if not util_shards:
        return
    print(f"[post] Compacting {len(util_shards)} util LMDB shard(s)...")
    for util in sorted(util_shards):
        try:
            subprocess.run(
                ["poetry", "run", "python", "backend/app/scripts/compact_lmdb.py", "--util-shard", util],
                check=True,
            )
        except Exception as e:
            print(f"[post] LMDB compact failed for {util}: {e}")
    util_shards.clear()


def _load_completed_ingest_dates(path: Path) -> set[str]:
    if not path.exists():
        return set()
    done: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            value = line.strip()
            if not value or value.startswith("#"):
                continue
            done.add(value)
    return done


def _append_completed_ingest_date(path: Path, ingest_date: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(f"{ingest_date}\n")


class _IngestStats:
    def __init__(self):
        self.batches = 0
        self.total_chunks = 0
        self.total_tokens = 0
        self.total_vectors = 0
        self.total_bytes = 0
        self.dim = None
        self.total_batch_seconds = 0.0

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

    def maybe_log(self, batch_seconds: float):
        if STATS_EVERY_BATCHES <= 0:
            return
        if self.batches % STATS_EVERY_BATCHES != 0:
            return
        self.total_batch_seconds += batch_seconds
        avg_batch_seconds = self.total_batch_seconds / self.batches if self.batches else 0.0
        eta = ""
        if EST_TOTAL_BATCHES > 0 and self.batches > 0:
            remaining = max(EST_TOTAL_BATCHES - self.batches, 0)
            eta_seconds = int(remaining * avg_batch_seconds)
            eta_h = eta_seconds // 3600
            eta_m = (eta_seconds % 3600) // 60
            eta_s = eta_seconds % 60
            eta = f" eta~{eta_h}h {eta_m}m {eta_s}s"
        avg_tokens = (self.total_tokens / self.total_vectors) if self.total_vectors else 0
        avg_bytes = (self.total_bytes / self.total_vectors) if self.total_vectors else 0
        gb = self.total_bytes / (1024 ** 3)
        print(
            f"[stats] batches={self.batches} chunks={self.total_chunks} "
            f"avg_tokens={avg_tokens:.1f} avg_vec_bytes={avg_bytes:,.0f} "
            f"dim={self.dim or 0} dtype={LMDB_VECTOR_DTYPE} "
            f"est_lmdb_gb={gb:.2f} avg_batch_s={avg_batch_seconds:.1f}{eta}"
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
    ingest_dates: list[str] | None = None,
    master_manifest_csv: Path | None = None,
    ingest_checkpoint_path: Path | None = None,
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
    start_time = time.perf_counter()
    current_dataset_shards: set[str] = set()
    completed_dates = (
        _load_completed_ingest_dates(ingest_checkpoint_path)
        if ingest_checkpoint_path
        else set()
    )
    if completed_dates:
        print(
            f"[checkpoint] Loaded {len(completed_dates)} completed date(s) "
            f"from {ingest_checkpoint_path}"
        )

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
        batch_start = time.perf_counter()
        embedded = embed_chunks(batch, tokenizer, model)
        batch_seconds = time.perf_counter() - batch_start
        total_embedded += len(embedded)
        for rec in embedded:
            shard = rec.get("dataset_shard")
            if isinstance(shard, str):
                s = shard.strip().upper()
                if s.startswith("UTIL"):
                    current_dataset_shards.add(s)
        print(
            f"[ingest] Embedded batch of {len(embedded)} chunks "
            f"(total {total_embedded}) in {batch_seconds:.1f}s"
        )
        stats.update(embedded)
        stats.maybe_log(batch_seconds)

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
        dates = ingest_dates or ["2025-09-01"]
        if ingest_batch_size:
            for ingest_date in dates:
                if ingest_date in completed_dates:
                    print(f"[checkpoint] Skipping completed date {ingest_date}")
                    continue
                print(f"[ingest] Starting dataset for {ingest_date}")
                current_dataset_shards.clear()
                bulk_dataset_download(
                    ingest_date,
                    DOWNLOAD_DIR,
                    use_manifest=False,
                    sample_k=0,
                    max_patents=None,
                    return_chunks=False,
                    batch_size=ingest_batch_size,
                    on_batch=_record_batch,
                    master_manifest_csv=master_manifest_csv,
                )
                _compact_util_shards(current_dataset_shards)
                if ingest_checkpoint_path:
                    _append_completed_ingest_date(ingest_checkpoint_path, ingest_date)
                    completed_dates.add(ingest_date)
                    print(f"[checkpoint] Recorded completion for {ingest_date}")
        else:
            for ingest_date in dates:
                if ingest_date in completed_dates:
                    print(f"[checkpoint] Skipping completed date {ingest_date}")
                    continue
                print(f"[ingest] Starting dataset for {ingest_date}")
                current_dataset_shards.clear()
                chunks = bulk_dataset_download(
                    ingest_date,
                    DOWNLOAD_DIR,
                    use_manifest=False,
                    sample_k=0,
                    max_patents=None,
                    master_manifest_csv=master_manifest_csv,
                )
                _record_batch(chunks)
                _compact_util_shards(current_dataset_shards)
                if ingest_checkpoint_path:
                    _append_completed_ingest_date(ingest_checkpoint_path, ingest_date)
                    completed_dates.add(ingest_date)
                    print(f"[checkpoint] Recorded completion for {ingest_date}")
    finally:
        _compact_util_shards(current_dataset_shards)
        elapsed = time.perf_counter() - start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        print(f"[timing] Total ingest+embed time: {hours}h {minutes}m {seconds}s")
        print(
            "[next] Start API: "
            "poetry run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"
        )
        if export_handle:
            export_handle.close()
            print(f"[export] Saved embeddings to {export_target}")


def import_exported_embeddings(path: Path | None = None, batch_size: int = 128):
    """Load saved embeddings from disk into Weaviate."""
    target = path or EXPORT_PATH
    load_embeddings_into_weaviate(target, batch_size=batch_size)


if __name__ == "__main__":
    # Optional: to clear and replace everything, set DROP_FIRST=1 and run once.
    DROP_FIRST = os.environ.get("DROP_FIRST", "0").strip() in {"1", "true", "True", "yes", "YES"}
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
        ingest_dates_raw = os.environ.get("INGEST_DATES", "").strip()
        if ingest_dates_raw:
            ingest_dates = [
                d.strip()
                for d in ingest_dates_raw.split(",")
                if d.strip()
            ]
        else:
            ingest_start_date = os.environ.get("INGEST_START_DATE", "2025-09-01").strip()
            try:
                ingest_weeks_back = int(os.environ.get("INGEST_WEEKS_BACK", "0"))
            except ValueError:
                ingest_weeks_back = 0
            ingest_dates = _build_weekly_dates(ingest_start_date, ingest_weeks_back)
            print(
                f"[ingest] Auto-generated {len(ingest_dates)} weekly date(s) "
                f"from {ingest_start_date} with INGEST_WEEKS_BACK={max(0, ingest_weeks_back)}"
            )
        manifest_raw = os.environ.get(
            "MASTER_MANIFEST_CSV",
            "backend/validation/master_patent_manifest.csv",
        ).strip()
        manifest_csv = Path(manifest_raw) if manifest_raw else None
        checkpoint_raw = os.environ.get(
            "INGEST_CHECKPOINT_PATH",
            "backend/validation/ingest_completed_dates.txt",
        ).strip()
        checkpoint_path = Path(checkpoint_raw) if checkpoint_raw else None
        real_ingest(
            ingest_dates=ingest_dates,
            master_manifest_csv=manifest_csv,
            ingest_checkpoint_path=checkpoint_path,
        )
