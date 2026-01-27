# --- Import required libraries ---
import requests        # Used for sending HTTP requests (GET, POST) to web APIs
import json            # Used for parsing and formatting JSON data
from lxml import etree            # Imported but not used here (could be for XML parsing later)
from datetime import datetime, timedelta  # Used for date and time manipulation
from pathlib import Path
import os
from zipfile import ZipFile
import tarfile
import io
import sys
import time as _time
import time
import random
import builtins
import hashlib
import csv
import re
import base64
import mimetypes
import urllib.parse
from typing import Callable, Optional
import sys

# --- API key and HTTP header setup ---
api_key = 'elnzwmbevfqhjgiisukhijthvlqwfr'

headers = {
    "x-api-key": api_key,             # Required header to authenticate with the USPTO API
    "Content-Type": "application/json"  # Tells the API that we are sending/expecting JSON data
}
from pathlib import Path
FAILED_DIR = Path("failed_xmls"); FAILED_DIR.mkdir(exist_ok=True)

def save_failed(i, xml_blob, reason, doc_id=None):
    name = f"{i:05d}_{doc_id or 'unknown'}_{reason[:40].replace(' ', '_')}.xml"
    (FAILED_DIR / name).write_bytes(xml_blob)

DATA_ROOT = Path(os.environ.get("USPTO_DATA_ROOT", Path(".").resolve()))
output_file = DATA_ROOT
output_file.mkdir(parents=True, exist_ok=True)

# --- Simple stdout progress helpers ---
def _progress_bar_str(current: int, total: int | None, width: int = 40) -> str:
    if total and total > 0:
        ratio = min(1.0, max(0.0, current / float(total)))
        done = int(width * ratio)
        return f"[{'#' * done}{'.' * (width - done)}] {int(ratio*100):3d}%"
    else:
        # Unknown total; simple ticker
        dots = (current // 1_000_000) % width
        return f"[{'>' * (dots or 1)}{'.' * (width - (dots or 1))}]   ?%"


def _print_progress(prefix: str, current: int, total: int | None):
    bar = _progress_bar_str(current, total)
    suffix = f" {current:,}" + (f"/{total:,}" if total else "")
    sys.stdout.write(f"\r{prefix} {bar}{suffix}")
    sys.stdout.flush()
    if total is not None and current >= total:
        sys.stdout.write("\n")
        sys.stdout.flush()

# Verbosity toggle (compact by default)
VERBOSE: bool = False

def _log(msg: str):
    if VERBOSE:
        print(msg)
def make_parser():
    return etree.XMLParser(
        resolve_entities=False, load_dtd=False, no_network=True,
        huge_tree=True, recover=False, remove_comments=True
    )


def elem_to_rich_text(elem) -> str:
    """Serialize an element's content preserving basic inline formatting.
    Keeps tags: b, i, u, em, strong, sup, sub, br. Drops other tags but
    retains their textual content. Useful to carry formatting context.
    """
    allowed = {"b", "i", "u", "em", "strong", "sup", "sub", "br"}

    def ser(node):
        if not isinstance(node, etree._Element):
            return "" if node is None else str(node)
        # Some nodes (e.g., comments, PIs) have non-string tag; avoid QName on those
        tag_local = etree.QName(node).localname.lower() if isinstance(node.tag, str) else None
        use_tag = (tag_local in allowed) if tag_local else False
        parts = []
        if use_tag and tag_local != "br":
            parts.append(f"<{tag_local}>")
        elif tag_local == "br":
            # self-closing break
            parts.append("<br/>")
        # node text
        if node.text:
            parts.append(node.text)
        # children
        for child in node:
            parts.append(ser(child))
            if child.tail:
                parts.append(child.tail)
        if use_tag and tag_local != "br":
            parts.append(f"</{tag_local}>")
        return "".join(parts)

    return ser(elem)


def rich_to_plain(rich: str) -> str:
    """Convert simplified rich text to plain text for printing/embeddings.
    - Convert <br> to newlines
    - Strip other tags
    - Collapse whitespace
    """
    if not rich:
        return ""
    s = re.sub(r"<br\s*/?>", "\n", rich, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", "", s)
    # Normalize whitespace but keep newlines from <br>
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    return s.strip()


def _token_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+", text or ""))


def _split_sentences(text: str) -> list[str]:
    if not text:
        return []
    parts: list[str] = []
    for block in re.split(r"\n+", text):
        block = block.strip()
        if not block:
            continue
        splits = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", block)
        for s in splits:
            s = s.strip()
            if s:
                parts.append(s)
    return parts


def _tail_overlap(sentences: list[str], overlap_tokens: int) -> tuple[list[str], int]:
    if overlap_tokens <= 0:
        return [], 0
    overlap: list[str] = []
    count = 0
    for s in reversed(sentences):
        count += _token_count(s)
        overlap.insert(0, s)
        if count >= overlap_tokens:
            break
    return overlap, count


def _split_long_text(text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    sentences = _split_sentences(text)
    if not sentences:
        sentences = [text]
    parts: list[str] = []
    current: list[str] = []
    current_tokens = 0
    for sent in sentences:
        sent_tokens = _token_count(sent)
        if sent_tokens > max_tokens:
            if current:
                parts.append(" ".join(current).strip())
                current = []
                current_tokens = 0
            words = re.findall(r"\S+", sent)
            if not words:
                continue
            step = max(1, max_tokens - max(0, overlap_tokens))
            start = 0
            while start < len(words):
                end = min(len(words), start + max_tokens)
                parts.append(" ".join(words[start:end]).strip())
                if overlap_tokens <= 0:
                    start = end
                else:
                    start = max(0, end - overlap_tokens)
            continue

        if current_tokens + sent_tokens <= max_tokens or not current:
            current.append(sent)
            current_tokens += sent_tokens
            continue

        parts.append(" ".join(current).strip())
        overlap, overlap_count = _tail_overlap(current, overlap_tokens)
        current = overlap
        current_tokens = overlap_count
        if current_tokens + sent_tokens <= max_tokens or not current:
            current.append(sent)
            current_tokens += sent_tokens
        else:
            current = [sent]
            current_tokens = sent_tokens

    if current:
        parts.append(" ".join(current).strip())
    return parts


def _extract_claim_number(claim, fallback_index: int) -> int:
    raw = None
    for key in ("num", "claim-num", "claim_number", "claim-number", "id"):
        raw = claim.get(key)
        if raw:
            break
    if not raw:
        return fallback_index
    match = re.search(r"\d+", str(raw))
    if not match:
        return fallback_index
    try:
        return int(match.group(0))
    except Exception:
        return fallback_index


def _extract_claim_type(claim, claim_text: str) -> str:
    raw = claim.get("claim-type") or claim.get("type")
    if raw:
        val = str(raw).strip().lower()
        if "depend" in val:
            return "dependent"
        if "independ" in val:
            return "independent"
    refs = claim.xpath(
        ".//*[contains(local-name(), 'claim-ref') or contains(local-name(), 'claim-reference')]"
    )
    if refs:
        return "dependent"
    if re.search(r"\bclaim\s+\d+", claim_text or "", flags=re.IGNORECASE):
        return "dependent"
    return "independent"


def _is_util_member(name: str) -> bool:
    parts = name.replace("\\", "/").split("/")
    return any(p.upper().startswith("UTIL") for p in parts)

def _merge_list_fields(left: list | None, right: list | None) -> list:
    merged: list = []
    for item in left or []:
        if item not in merged:
            merged.append(item)
    for item in right or []:
        if item not in merged:
            merged.append(item)
    return merged


def _merge_chunks(base: dict, other: dict) -> dict:
    merged = dict(base)
    merged["chunk"] = (base.get("chunk", "").rstrip() + "\n\n" + other.get("chunk", "").lstrip()).strip()
    if "fig_refs" in base or "fig_refs" in other:
        merged["fig_refs"] = _merge_list_fields(base.get("fig_refs"), other.get("fig_refs"))
    if "fig_images" in base or "fig_images" in other:
        merged["fig_images"] = _merge_list_fields(base.get("fig_images"), other.get("fig_images"))
    return merged


def _split_chunk_if_needed(chunk: dict, max_tokens: int, overlap_tokens: int) -> list[dict]:
    plain = rich_to_plain(chunk.get("chunk", ""))
    if not plain:
        return [chunk]
    if _token_count(plain) <= max_tokens:
        return [chunk]
    parts = _split_long_text(plain, max_tokens, overlap_tokens)
    out: list[dict] = []
    part_count = len(parts)
    for idx, part in enumerate(parts, start=1):
        new_chunk = dict(chunk)
        new_chunk["chunk"] = part
        if part_count > 1:
            new_chunk["part_index"] = idx
            new_chunk["part_count"] = part_count
        out.append(new_chunk)
    return out


def _rebalance_doc_chunks(
    chunks: list[dict],
    *,
    min_tokens: int = 80,
    max_tokens: int = 180,
    overlap_tokens: int = 30,
    no_merge_sections: set[str] | None = None,
) -> list[dict]:
    if not chunks:
        return chunks
    if no_merge_sections is None:
        no_merge_sections = {"claim", "abstract", "sequence-summary", "sequence-metadata"}
    out: list[dict] = []
    buffer: dict | None = None
    buffer_tokens = 0
    buffer_section: str | None = None

    def flush_buffer():
        nonlocal buffer, buffer_tokens, buffer_section
        if not buffer:
            return
        out.extend(_split_chunk_if_needed(buffer, max_tokens, overlap_tokens))
        buffer = None
        buffer_tokens = 0
        buffer_section = None

    for ch in chunks:
        raw = ch.get("chunk", "")
        if not raw and (ch.get("fig_images") or ch.get("sequence")):
            flush_buffer()
            out.append(ch)
            continue
        plain = rich_to_plain(raw)
        if not plain:
            continue
        section = ch.get("section")
        tok = _token_count(plain)

        if section in no_merge_sections:
            flush_buffer()
            out.extend(_split_chunk_if_needed(ch, max_tokens, overlap_tokens))
            continue

        if buffer and buffer_section != section:
            flush_buffer()

        if not buffer:
            buffer = dict(ch)
            buffer_tokens = tok
            buffer_section = section
            continue

        if buffer_tokens < min_tokens:
            merged = _merge_chunks(buffer, ch)
            merged_tokens = _token_count(rich_to_plain(merged.get("chunk", "")))
            if merged_tokens <= max_tokens:
                buffer = merged
                buffer_tokens = merged_tokens
                continue
            flush_buffer()
            buffer = dict(ch)
            buffer_tokens = tok
            buffer_section = section
            continue

        flush_buffer()
        buffer = dict(ch)
        buffer_tokens = tok
        buffer_section = section

    flush_buffer()
    return out


def _finalize_doc_chunks(
    collector: list,
    doc_buffer: list[dict],
    *,
    sample_enabled: bool,
) -> tuple[list[dict] | None, int]:
    if doc_buffer:
        collector.extend(doc_buffer)
    doc_chunks = list(doc_buffer) if sample_enabled else None
    return doc_chunks, len(doc_buffer)


def count_docs_in_zip(zip_path: Path) -> int:
    """Count number of patent XML sub-documents inside a weekly USPTO zip.

    Streams the inner XML and counts documents using iter_uspto_subdocs without
    parsing, so it is fast and memory-efficient.
    """
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip not found: {zip_path}")
    with ZipFile(zip_path, mode='r') as zf:
        members = [n for n in zf.namelist() if n.lower().endswith(".xml")]
        if not members:
            raise FileNotFoundError("No .xml found inside ZIP")
        inner_xml_name = members[0]
        count = 0
        with zf.open(inner_xml_name, "r") as xml_stream:
            for _ in iter_uspto_subdocs(xml_stream):
                count += 1
        return count


def _slugify(value: str, max_len: int = 80) -> str:
    s = re.sub(r"[^0-9A-Za-z._-]+", "-", value or "").strip("-")
    if not s:
        s = "untitled"
    return s[:max_len]


def write_random_patent_sample(chunks: list[dict], k: int, out_dir: Path, *, seed: int | None = None, assets_by_doc: dict | None = None) -> list[str]:
    """Write k random patents to individual Markdown files in per‑patent folders.

    - Groups chunks by doc_id
    - Randomly samples k distinct doc_ids
    - For each sampled doc, creates a folder under `<out_dir>/sampled/` named
      `<doc_id>_<title-slug>` and writes the original long filename inside it
    - Writes a CSV manifest (no patent text) with key metadata for quick review
    Returns list of written Markdown file paths (as strings).
    """
    # Group by doc_id
    by_doc: dict[str, list[dict]] = {}
    for ch in chunks:
        doc_id = ch.get("doc_id")
        if not doc_id:
            continue
        by_doc.setdefault(doc_id, []).append(ch)

    doc_ids = list(by_doc.keys())
    if not doc_ids:
        print("[warn] no doc_ids found to sample")
        return []

    sample_size = min(k, len(doc_ids))
    rnd = random.Random(seed) if seed is not None else random
    sample_ids = rnd.sample(doc_ids, sample_size)

    # Ensure base output directory exists and create a subfolder for samples
    out_dir.mkdir(parents=True, exist_ok=True)
    sample_dir = out_dir / "sampled"
    sample_dir.mkdir(parents=True, exist_ok=True)

    written = []
    manifest_rows = []

    print(f"[samples] Preparing to write {len(sample_ids)} sample(s) to {(out_dir / 'sampled').resolve()}")
    for idx, did in enumerate(sample_ids, start=1):
        doc_chunks = by_doc[did]
        # Derive metadata from the first chunk (all chunks for a patent share these)
        meta = next((c for c in doc_chunks if c.get("section") in ("abstract","description","claim","sequence-summary","sequence-metadata")), doc_chunks[0])
        title = meta.get("title") or ""
        filing_date = meta.get("filing_date") or ""
        classification = meta.get("classification") or ""
        authors = meta.get("authors") or ""

        # Build Markdown content
        heading = f"# {title or 'Untitled'} (Doc {did})\n\n"
        meta_md = (
            f"- Doc ID: {did}\n"
            f"- Title: {title}\n"
            f"- Filing Date: {filing_date}\n"
            f"- Classification: {classification}\n"
            f"- Authors: {authors}\n\n"
        )

        # Sections: keep order Abstract -> Description -> Claims -> Supplemental -> Sequence listing (if any)
        def section_md(name: str, items: list[str]) -> str:
            if not items:
                return ""
            body = "\n\n".join(items)
            return f"## {name}\n\n{body}\n\n"

        abs_items = [c.get("chunk","") for c in doc_chunks if c.get("section") == "abstract"]
        # For description and claim chunks, preserve association with any figure refs
        desc_chunks = [c for c in doc_chunks if c.get("section") == "description"]
        claim_chunks = [c for c in doc_chunks if c.get("section") == "claim"]
        seq_chunks = [c for c in doc_chunks if c.get("section") == "sequence-metadata"]
        seq_sum = [c.get("chunk","") for c in doc_chunks if c.get("section") == "sequence-summary"]
        supp_items = [c.get("chunk","") for c in doc_chunks if c.get("section") == "supplemental"]

        # If no chunks carry fig_images but assets exist, add a dedicated figures chunk
        if assets_by_doc and did in assets_by_doc:
            has_figs = any(c.get("fig_images") for c in doc_chunks)
            if not has_figs:
                fig_payloads = _images_to_payloads(
                    assets_by_doc[did].get("images"),
                    limit=6,
                    convert_to_png=True,
                )
                if fig_payloads:
                    doc_chunks.append({
                        "section": "figures",
                        "chunk": "",
                        "filing_date": filing_date,
                        "doc_id": did,
                        "kind": None,
                        "authors": authors,
                        "classification": classification,
                        "title": title,
                        "fig_images": fig_payloads,
                    })

        # Build structured table for sequence metadata if available
        seq_table_md = ""
        if seq_chunks:
            # Check if any chunk has structured 'sequence' dict
            has_struct = any(isinstance(c.get("sequence"), dict) for c in seq_chunks)
            if has_struct:
                headers = ["SEQ ID NO", "Title", "Molecule", "Organism", "Feature", "Product", "Comment"]
                seq_table_md += "## Sequence Listing - Metadata\n\n"
                seq_table_md += "| " + " | ".join(headers) + " |\n"
                seq_table_md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                for sc in seq_chunks:
                    sd = sc.get("sequence") or {}
                    row = [
                        sd.get("seq_id") or "",
                        sd.get("title") or "",
                        sd.get("molecule") or "",
                        sd.get("organism") or "",
                        sd.get("feature") or "",
                        sd.get("product") or "",
                        sd.get("comment") or "",
                    ]
                    # Escape vertical bars for Markdown table cells
                    row = [str(x).replace("|", r"\|") for x in row]
                    seq_table_md += "| " + " | ".join(row) + " |\n"
                seq_table_md += "\n"
            else:
                # Fallback to raw lines if structure missing
                raw_lines = [c.get("chunk", "") for c in seq_chunks]
                seq_table_md += section_md("Sequence Listing - Metadata", raw_lines)

        # Save any images for this doc_id (if provided)
        img_dir_rel = None
        img_map = {}
        if assets_by_doc and did in assets_by_doc:
            patent_dir_name = f"{_slugify(did)}_{_slugify(title, 40)}" if title else f"{_slugify(did)}"
            patent_dir = sample_dir / patent_dir_name
            images_dir = patent_dir / "images"
            images_dir.mkdir(parents=True, exist_ok=True)
            conv_assets, file_map = _convert_doc_assets_to_png(assets_by_doc[did])
            _remap_chunk_fig_images(doc_chunks, file_map)
            for img in conv_assets.get("images", []):
                fname = img.get("file")
                data = img.get("data")
                if not fname or data is None:
                    continue
                outp = images_dir / fname
                try:
                    if not outp.exists():
                        outp.write_bytes(data)
                    # map fig ids that point to this file
                    for fig_id in img.get("fig_ids", []) or []:
                        img_map.setdefault(fig_id, str(Path("images") / fname))
                    # also map by numeric figure number if present
                    if img.get("num"):
                        img_map.setdefault(str(img.get("num")), str(Path("images") / fname))
                except Exception:
                    pass
            img_dir_rel = "images"

        # Build description markdown with inline images (if any figure refs present)
        def render_chunks_with_images(name: str, items: list[dict]) -> str:
            if not items:
                return ""
            parts = []
            for it in items:
                parts.append(it.get("chunk", ""))
                refs = it.get("fig_refs") or []
                # Attach images after the paragraph if available
                imgs_for_para = []
                for r in refs:
                    fp = img_map.get(r)
                    if fp and fp not in imgs_for_para:
                        imgs_for_para.append(fp)
                if imgs_for_para:
                    for fp in imgs_for_para:
                        parts.append(f"\n![Figure]({fp})\n")
            body = "\n\n".join(parts)
            return f"## {name}\n\n{body}\n\n"

        content = (
            heading + meta_md +
            section_md("Abstract", abs_items) +
            render_chunks_with_images("Description", desc_chunks) +
            render_chunks_with_images("Claims", claim_chunks) +
            section_md("Supplemental", supp_items) +
            seq_table_md +
            section_md("Sequence Listing - Summary", seq_sum)
        )

        # Build a per‑patent directory to avoid overwriting across runs/documents
        patent_dir_name = f"{_slugify(did)}_{_slugify(title, 40)}" if title else f"{_slugify(did)}"
        patent_dir = sample_dir / patent_dir_name
        patent_dir.mkdir(parents=True, exist_ok=True)

        # Keep the original long filename, but place it inside the patent folder
        fname = f"sample_{idx:02d}_{_slugify(did)}_{_slugify(title, 40)}.md"
        fpath = patent_dir / fname
        fpath.write_text(content, encoding="utf-8")
        written.append(str(fpath))
        # Progress update instead of per-file log
        _print_progress("[samples]", idx, len(sample_ids))

        # Manifest row (no text)
        manifest_rows.append({
            "index": idx,
            "doc_id": did,
            "title": title,
            "filing_date": filing_date,
            "classification": classification,
            "authors": authors,
            "abstract_chunks": len(abs_items),
            "description_chunks": len(desc_chunks),
            "claim_chunks": len(claim_chunks),
            "sequence_metadata_chunks": len(seq_chunks),
            "sequence_summary_chunks": len(seq_sum),
        })

    # Write manifest CSV (no patent text)
    manifest_path = sample_dir / "sample_manifest.csv"
    fieldnames = list(manifest_rows[0].keys()) if manifest_rows else ["index","doc_id","title","filing_date","classification","authors"]
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(manifest_rows)

    # Also write sampled chunks to backend/app/db for demo backend loading
    try:
        # Determine db directory relative to this file: backend/app/db
        db_dir = Path(__file__).resolve().parent.parent / "db"
        db_dir.mkdir(parents=True, exist_ok=True)
        chunks_path = db_dir / "sample_chunks.jsonl"

        # Collect chunks for sampled doc_ids and write as JSONL
        import json as _json
        with chunks_path.open("w", encoding="utf-8") as f:
            for did in sample_ids:
                for ch in by_doc.get(did, []):
                    # Ensure only serializable types
                    f.write(_json.dumps(ch, ensure_ascii=False) + "\n")
        print(f"Wrote sampled chunks JSONL: {chunks_path}")
    except Exception as e:
        print(f"[warn] failed to write sampled chunks jsonl: {e}")

    print(f"Wrote {len(written)} markdown samples and manifest at {sample_dir}")
    return written

class _ChunkCollector(list):
    """Collect chunks conditionally and emit batches via a callback."""
    def __init__(self, *, collect: bool, batch_size: int | None, on_batch: Callable[[list[dict]], None] | None):
        super().__init__()
        self._collect = bool(collect)
        self._batch_size = max(0, batch_size or 0)
        self._on_batch = on_batch
        self._pending: list[dict] = []

    def append(self, value):  # type: ignore[override]
        if self._collect:
            super().append(value)
        self._handle_batch(value)

    def extend(self, iterable):  # type: ignore[override]
        for item in iterable:
            self.append(item)

    def _handle_batch(self, value):
        if not self._on_batch:
            return
        self._pending.append(value)
        if self._batch_size and len(self._pending) >= self._batch_size:
            self._flush_pending()

    def flush(self):
        if not self._on_batch or not self._pending:
            return
        self._flush_pending()

    def _flush_pending(self):
        batch = self._pending
        self._pending = []
        self._on_batch(batch)


class BatchHashRecorder:
    """Stream-friendly helper to hash each emitted batch and append run results to CSV."""
    def __init__(self, csv_path: Path):
        self.csv_path = Path(csv_path)
        self._rows: list[dict] = []
        self._reset_run_state()

    def _reset_run_state(self):
        self._run_digest: hashlib._Hash | None = None
        self._batch_hashes: list[str] = []
        self._batch_count: int = 0
        self._chunk_count: int = 0
        self._run_meta: dict | None = None
        self._started_at: str | None = None

    def start_run(self, *, run_index: int, input_date: str | datetime, dataset_product: str):
        self._run_digest = hashlib.sha256()
        self._batch_hashes = []
        self._batch_count = 0
        self._chunk_count = 0
        self._started_at = datetime.utcnow().isoformat() + "Z"
        self._run_meta = {
            "input_date": input_date if isinstance(input_date, str) else input_date.strftime("%Y-%m-%d"),
            "dataset_product": dataset_product,
            "run_index": run_index,
        }

    def on_batch(self, batch: list[dict]):
        if self._run_digest is None:
            raise RuntimeError("BatchHashRecorder.on_batch called before start_run")
        # Serialize deterministically and hash batch + running stream
        payload = json.dumps(batch, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        batch_hash = hashlib.sha256(payload).hexdigest()
        self._run_digest.update(payload)
        self._batch_hashes.append(batch_hash)
        self._batch_count += 1
        self._chunk_count += len(batch)

    def end_run(self):
        if self._run_digest is None or self._run_meta is None:
            return
        self._rows.append({
            **self._run_meta,
            "run_hash": self._run_digest.hexdigest(),
            "batch_count": self._batch_count,
            "chunk_count": self._chunk_count,
            "batch_hashes": ";".join(self._batch_hashes),
            "started_at": self._started_at or "",
            "completed_at": datetime.utcnow().isoformat() + "Z",
        })
        self._reset_run_state()

    def flush_to_csv(self):
        if not self._rows:
            return
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = ["input_date", "dataset_product", "run_index", "run_hash", "batch_count", "chunk_count", "batch_hashes", "started_at", "completed_at"]
        header_needed = not self.csv_path.exists() or self.csv_path.stat().st_size == 0
        with self.csv_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if header_needed:
                writer.writeheader()
            writer.writerows(self._rows)
        self._rows = []


def _flush_collector(chunks):
    flush = getattr(chunks, "flush", None)
    if callable(flush):
        flush()


def _dataset_file_base(input_date: str | datetime, path: Path, dataset_product: str) -> tuple[Path, str, datetime, str]:
    """Return (base path without extension, ext hint, last_tuesday, product_upper)."""
    path = Path(path)
    start_date = datetime.strptime(input_date, "%Y-%m-%d") if isinstance(input_date, str) else input_date
    days_since_tuesday = (start_date.weekday() - 1)
    last_tuesday = start_date - timedelta(days=days_since_tuesday)
    dataset_product = str(dataset_product)
    product_upper = dataset_product.upper()
    if product_upper == "PTGRDT":
        file_stem = f"I{last_tuesday:%Y%m%d}"
        ext_hint = ".tar"
    else:
        file_stem = f"ipg{last_tuesday:%y}{last_tuesday:%m}{last_tuesday:%d}"
        ext_hint = ".zip"
    base = path / file_stem
    return base, ext_hint, last_tuesday, product_upper


def _find_existing_archive(base: Path) -> Path | None:
    for ext in [".tar", ".tar.gz", ".tgz", ".zip"]:
        p = Path(str(base) + ext) if ext in (".tar.gz", ".tgz") else base.with_suffix(ext)
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


def _delete_dataset_archives(input_date: str | datetime, path: Path, dataset_product: str):
    base, ext_hint, _, _ = _dataset_file_base(input_date, path, dataset_product)
    removed = []
    for ext in [".tar", ".tar.gz", ".tgz", ".zip", ext_hint]:
        p = Path(str(base) + ext) if ext in (".tar.gz", ".tgz") else base.with_suffix(ext)
        try:
            if p.exists():
                p.unlink()
                removed.append(p)
            part = p.with_suffix(p.suffix + ".part")
            if part.exists():
                part.unlink()
        except Exception:
            pass
    if removed:
        _log(f"[determinism] removed cached archives: {', '.join(str(r) for r in removed)}")


def _download_with_retry(file_url: str, file_path: Path, tmp_path: Path, *, max_retries: int = 3):
    """Download with basic retry on HTTP/connection errors (esp. 5xx)."""
    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            with requests.get(file_url, stream=True, headers=headers, timeout=60) as r:
                status = r.status_code
                if status >= 500:
                    raise requests.HTTPError(f"{status} Server Error", response=r)
                r.raise_for_status()
                total = None
                try:
                    total = int(r.headers.get("Content-Length") or 0) or None
                except Exception:
                    total = None
                downloaded = 0
                t0 = _time.time()
                with open(tmp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1_048_576):  # 1 MB chunks
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total is None or (downloaded // (4*1024*1024)) != ((downloaded - len(chunk)) // (4*1024*1024)):
                            elapsed = max(1e-6, _time.time() - t0)
                            speed = downloaded / elapsed  # bytes/sec
                            _print_progress("[download]", downloaded, total)
                            sys.stdout.write(f"  {speed/1_048_576:.2f} MB/s")
                            sys.stdout.flush()
                if total is not None:
                    _print_progress("[download]", downloaded, total)
                else:
                    sys.stdout.write("\n")
            tmp_path.replace(file_path)
            print(f"Saved: {file_path} ({file_path.stat().st_size:,} bytes)")
            return
        except Exception as e:
            last_err = e
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception:
                pass
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"[download] retry {attempt}/{max_retries} after error: {e} (sleep {wait}s)")
                _time.sleep(wait)
                continue
            break
    if last_err:
        raise last_err

def validate_batch_determinism(
    input_date: str | datetime,
    *,
    runs: int = 3,
    path: Path = Path("."),
    dataset_product: str = "PTGRDT",
    batch_size: int = 500,
    csv_path: Path = Path("determinism_hashes.csv"),
    verbose: bool = False,
    delete_between_runs: bool = False,
    validate_metadata: bool = False,
    metadata_mismatch_csv: Path | None = None,
) -> list[dict]:
    """
    Run the ingestion pipeline multiple times on the same input and record hashes for each run.

    - Streams batches through a BatchHashRecorder so we never hold the entire output in memory.
    - Each run produces a deterministic SHA-256 of the serialized batches plus per-batch hashes.
    - Results are appended to `csv_path` for quick comparison across runs.
    """
    runs = max(1, int(runs))
    path = Path(path)
    dataset_product = str(dataset_product)
    recorder = BatchHashRecorder(csv_path)
    results: list[dict] = []
    for run_idx in range(1, runs + 1):
        if delete_between_runs:
            _delete_dataset_archives(input_date, path, dataset_product)
        recorder.start_run(run_index=run_idx, input_date=input_date, dataset_product=dataset_product)
        bulk_dataset_download(
            input_date,
            path,
            sample_k=0,  # disable sampling to keep memory stable and avoid extra I/O
            sample_out_dir=None,
            sample_seed=None,
            use_manifest=False,
            dataset_product=dataset_product,
            verbose=verbose,
            return_chunks=False,
            batch_size=batch_size,
            on_batch=recorder.on_batch,
            validate_metadata=validate_metadata,
            metadata_mismatch_csv=metadata_mismatch_csv,
        )
        recorder.end_run()
        if delete_between_runs and run_idx < runs:
            _delete_dataset_archives(input_date, path, dataset_product)
    rows = list(recorder._rows)
    recorder.flush_to_csv()
    # Return in-memory rows for immediate inspection/testing
    return rows


def report_hash_consistency(csv_path: Path) -> None:
    """Inspect a determinism CSV, print pass/fail plus simple diagnostics."""
    csv_path = Path(csv_path)
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        print(f"[determinism] FAIL: CSV missing or empty at {csv_path}")
        return
    # Allow very large fields (batch_hashes may be long)
    try:
        csv.field_size_limit(sys.maxsize)
    except (OverflowError, ValueError):
        pass

    def _is_sha256_hex(val: str | None) -> bool:
        return bool(val) and len(val) == 64 and all(c in "0123456789abcdef" for c in val.lower())

    rows = list(csv.DictReader(csv_path.open("r", encoding="utf-8")))
    run_hashes = []
    invalid_rows = 0
    invalid_batches = 0
    for row in rows:
        rh = row.get("run_hash", "")
        if not _is_sha256_hex(rh):
            invalid_rows += 1
        run_hashes.append(rh)
        bh_raw = (row.get("batch_hashes") or "").split(";") if row.get("batch_hashes") else []
        for bh in bh_raw:
            if bh and not _is_sha256_hex(bh):
                invalid_batches += 1

    distinct = len(set(run_hashes)) if run_hashes else 0
    passed = invalid_rows == 0 and invalid_batches == 0 and distinct <= 1 and len(run_hashes) > 0
    if passed:
        print(f"[determinism] PASS: {len(run_hashes)} run(s); run_hash={run_hashes[0]}")
    else:
        reason = "unknown"
        if invalid_rows or invalid_batches:
            reason = "invalid_hash_format"
        elif distinct > 1:
            reason = "hash_mismatch"
        print(
            f"[determinism] FAIL ({reason}): "
            f"runs={len(run_hashes)}, distinct_run_hashes={distinct}, "
            f"invalid_run_hash_rows={invalid_rows}, invalid_batch_hashes={invalid_batches}"
        )

def _append_chunk(collector: list, doc_chunks: list[dict] | None, record: dict):
    """Append a chunk to the global collector and the per-doc buffer."""
    collector.append(record)
    if doc_chunks is not None:
        doc_chunks.append(record)


def _load_manifest_doc_ids(manifest_path: Path) -> list[str]:
    if not manifest_path.exists():
        print(f"[warn] manifest not found at {manifest_path}; falling back to random sampling")
        return []
    doc_ids: list[str] = []
    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                did = (row.get("doc_id") or "").strip()
                if did:
                    doc_ids.append(did)
    except Exception as e:
        print(f"[warn] failed to read manifest at {manifest_path}: {e}")
    return doc_ids


class StreamingSampler:
    """Keeps only the sampled docs in memory and writes them out at the end."""
    def __init__(self, *, k: int, out_dir: Path, seed: int | None = None, manifest_doc_ids: list[str] | None = None):
        self.k = max(0, int(k))
        self.out_dir = out_dir
        self.random = random.Random(seed) if seed is not None else random.Random()
        self.manifest_doc_ids = manifest_doc_ids or []
        self._manifest_order = {doc_id: idx for idx, doc_id in enumerate(self.manifest_doc_ids)} if self.manifest_doc_ids else None
        self._manifest_selected: dict[str, dict] = {}
        self._reservoir: list[dict] = []
        self._docs_seen = 0

    def consider(self, doc_id: str | None, doc_chunks: list[dict] | None, doc_assets: dict | None):
        if not self.k or not doc_id or not doc_chunks:
            return
        entry = {
            "doc_id": doc_id,
            "chunks": doc_chunks,
            "assets": doc_assets or {},
        }
        if self._manifest_order is not None:
            if doc_id in self._manifest_order and doc_id not in self._manifest_selected:
                self._manifest_selected[doc_id] = entry
            return
        self._docs_seen += 1
        if len(self._reservoir) < self.k:
            self._reservoir.append(entry)
        else:
            j = self.random.randint(1, self._docs_seen)
            if j <= self.k:
                idx = self.random.randrange(self.k)
                self._reservoir[idx] = entry

    def finalize(self):
        entries: list[dict]
        if self._manifest_order is not None:
            if not self._manifest_selected:
                return
            entries = [
                self._manifest_selected[doc_id]
                for doc_id in self.manifest_doc_ids
                if doc_id in self._manifest_selected
            ]
        else:
            if not self._reservoir:
                return
            entries = self._reservoir
        flat_chunks: list[dict] = []
        assets_by_doc: dict[str, dict] = {}
        doc_ids: list[str] = []
        for entry in entries:
            doc_ids.append(entry["doc_id"])
            flat_chunks.extend(entry["chunks"])
            if entry.get("assets"):
                assets_by_doc[entry["doc_id"]] = entry["assets"]
        if not flat_chunks:
            return
        write_patent_sample_by_ids(flat_chunks, doc_ids=doc_ids, out_dir=self.out_dir, assets_by_doc=assets_by_doc)


def write_patent_sample_by_ids(chunks: list[dict], doc_ids: list[str], out_dir: Path, *, assets_by_doc: dict | None = None) -> list[str]:
    """Write per‑patent Markdown and CSV manifest for the given doc_ids.

    - Groups chunks by doc_id
    - Uses the provided list order for consistent indexing
    - For each doc, creates a folder under `<out_dir>/sampled/` named
      `<doc_id>_<title-slug>` and writes the original long filename inside it
    - Writes sampled chunks JSONL to backend/app/db/sample_chunks.jsonl
    Returns list of written Markdown file paths (as strings).
    """
    # Group by doc_id
    by_doc: dict[str, list[dict]] = {}
    for ch in chunks:
        did = ch.get("doc_id")
        if not did:
            continue
        by_doc.setdefault(did, []).append(ch)

    # Filter doc_ids to those actually present
    sample_ids = [did for did in doc_ids if did in by_doc]
    if not sample_ids:
        print("[warn] no matching doc_ids found in provided list")
        return []

    # Ensure base output directory exists and create a subfolder for samples
    out_dir.mkdir(parents=True, exist_ok=True)
    sample_dir = out_dir / "sampled"
    sample_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    manifest_rows: list[dict] = []

    print(f"[samples] Preparing to write {len(sample_ids)} sample(s) to {(out_dir / 'sampled').resolve()}")
    for idx, did in enumerate(sample_ids, start=1):
        doc_chunks = by_doc[did]
        # Derive metadata from the first representative chunk
        meta = next((c for c in doc_chunks if c.get("section") in ("abstract","description","claim","sequence-summary","sequence-metadata")), doc_chunks[0])
        title = meta.get("title") or ""
        filing_date = meta.get("filing_date") or ""
        classification = meta.get("classification") or ""
        authors = meta.get("authors") or ""

        # Build Markdown content
        heading = f"# {title or 'Untitled'} (Doc {did})\n\n"
        meta_md = (
            f"- Doc ID: {did}\n"
            f"- Title: {title}\n"
            f"- Filing Date: {filing_date}\n"
            f"- Classification: {classification}\n"
            f"- Authors: {authors}\n\n"
        )

        def section_md(name: str, items: list[str]) -> str:
            if not items:
                return ""
            body = "\n\n".join(items)
            return f"## {name}\n\n{body}\n\n"

        abs_items = [c.get("chunk","") for c in doc_chunks if c.get("section") == "abstract"]
        desc_chunks = [c for c in doc_chunks if c.get("section") == "description"]
        claim_chunks = [c for c in doc_chunks if c.get("section") == "claim"]
        seq_chunks = [c for c in doc_chunks if c.get("section") == "sequence-metadata"]
        seq_sum = [c.get("chunk","") for c in doc_chunks if c.get("section") == "sequence-summary"]
        supp_items = [c.get("chunk","") for c in doc_chunks if c.get("section") == "supplemental"]

        # If no chunks carry fig_images but assets exist, add a dedicated figures chunk
        if assets_by_doc and did in assets_by_doc:
            has_figs = any(c.get("fig_images") for c in doc_chunks)
            if not has_figs:
                fig_payloads = _images_to_payloads(
                    assets_by_doc[did].get("images"),
                    limit=6,
                    convert_to_png=True,
                )
                if fig_payloads:
                    doc_chunks.append({
                        "section": "figures",
                        "chunk": "",
                        "filing_date": filing_date,
                        "doc_id": did,
                        "kind": None,
                        "authors": authors,
                        "classification": classification,
                        "title": title,
                        "fig_images": fig_payloads,
                    })

        # Structured table for sequences
        seq_table_md = ""
        if seq_chunks:
            has_struct = any(isinstance(c.get("sequence"), dict) for c in seq_chunks)
            if has_struct:
                headers = ["SEQ ID NO", "Title", "Molecule", "Organism", "Feature", "Product", "Comment"]
                seq_table_md += "## Sequence Listing - Metadata\n\n"
                seq_table_md += "| " + " | ".join(headers) + " |\n"
                seq_table_md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                for sc in seq_chunks:
                    sd = sc.get("sequence") or {}
                    row = [
                        sd.get("seq_id") or "",
                        sd.get("title") or "",
                        sd.get("molecule") or "",
                        sd.get("organism") or "",
                        sd.get("feature") or "",
                        sd.get("product") or "",
                        sd.get("comment") or "",
                    ]
                    row = [str(x).replace("|", "\\|") for x in row]
                    seq_table_md += "| " + " | ".join(row) + " |\n"
                seq_table_md += "\n"
            else:
                raw_lines = [c.get("chunk", "") for c in seq_chunks]
                seq_table_md += section_md("Sequence Listing - Metadata", raw_lines)

        # Save any images for this doc_id (if provided)
        img_map = {}
        if assets_by_doc and did in assets_by_doc:
            patent_dir_name = f"{_slugify(did)}_{_slugify(title, 40)}" if title else f"{_slugify(did)}"
            patent_dir = sample_dir / patent_dir_name
            images_dir = patent_dir / "images"
            images_dir.mkdir(parents=True, exist_ok=True)
            conv_assets, file_map = _convert_doc_assets_to_png(assets_by_doc[did])
            _remap_chunk_fig_images(doc_chunks, file_map)
            for img in conv_assets.get("images", []):
                fname = img.get("file")
                data = img.get("data")
                if not fname or data is None:
                    continue
                outp = images_dir / fname
                try:
                    if not outp.exists():
                        outp.write_bytes(data)
                    for fig_id in img.get("fig_ids", []) or []:
                        img_map.setdefault(fig_id, str(Path("images") / fname))
                    if img.get("num"):
                        img_map.setdefault(str(img.get("num")), str(Path("images") / fname))
                except Exception:
                    pass

        def render_chunks_with_images(name: str, items: list[dict]) -> str:
            if not items:
                return ""
            parts = []
            for it in items:
                parts.append(it.get("chunk", ""))
                refs = it.get("fig_refs") or []
                imgs_for_para = []
                for r in refs:
                    fp = img_map.get(r)
                    if fp and fp not in imgs_for_para:
                        imgs_for_para.append(fp)
                if imgs_for_para:
                    for fp in imgs_for_para:
                        parts.append(f"\n![Figure]({fp})\n")
            body = "\n\n".join(parts)
            return f"## {name}\n\n{body}\n\n"

        content = (
            heading + meta_md +
            section_md("Abstract", abs_items) +
            render_chunks_with_images("Description", desc_chunks) +
            render_chunks_with_images("Claims", claim_chunks) +
            section_md("Supplemental", supp_items) +
            seq_table_md +
            section_md("Sequence Listing - Summary", seq_sum)
        )

        # Build a per‑patent directory to avoid overwriting across runs/documents
        patent_dir_name = f"{_slugify(did)}_{_slugify(title, 40)}" if title else f"{_slugify(did)}"
        patent_dir = sample_dir / patent_dir_name
        patent_dir.mkdir(parents=True, exist_ok=True)

        # Keep the original long filename, but place it inside the patent folder
        fname = f"sample_{idx:02d}_{_slugify(did)}_{_slugify(title, 40)}.md"
        fpath = patent_dir / fname
        fpath.write_text(content, encoding="utf-8")
        written.append(str(fpath))
        _print_progress("[samples]", idx, len(sample_ids))

        manifest_rows.append({
            "index": idx,
            "doc_id": did,
            "title": title,
            "filing_date": filing_date,
            "classification": classification,
            "authors": authors,
            "abstract_chunks": len(abs_items),
            "description_chunks": len(desc_chunks),
            "claim_chunks": len(claim_chunks),
            "sequence_metadata_chunks": len(seq_chunks),
            "sequence_summary_chunks": len(seq_sum),
        })

    # Write manifest CSV
    manifest_path = sample_dir / "sample_manifest.csv"
    fieldnames = list(manifest_rows[0].keys()) if manifest_rows else ["index","doc_id","title","filing_date","classification","authors"]
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(manifest_rows)

    # Write sampled chunks JSONL for backend demo
    try:
        db_dir = Path(__file__).resolve().parent.parent / "db"
        db_dir.mkdir(parents=True, exist_ok=True)
        chunks_path = db_dir / "sample_chunks.jsonl"
        import json as _json
        with chunks_path.open("w", encoding="utf-8") as f:
            for did in sample_ids:
                for ch in by_doc.get(did, []):
                    f.write(_json.dumps(ch, ensure_ascii=False) + "\n")
        print(f"Wrote sampled chunks JSONL: {chunks_path}")
    except Exception as e:
        print(f"[warn] failed to write sampled chunks jsonl: {e}")

    print(f"Wrote {len(written)} markdown samples and manifest at {sample_dir}")
    return written


def clamp_patent_doc(blob: bytes) -> bytes:
    """Clamp a raw blob to a single, self-contained XML document.

    - Realign to the first plausible XML start (XML decl or first tag)
    - If another XML declaration exists later, cut before it
    - Otherwise, trim after the first root's closing tag if found
    """
    if not blob:
        return b""
    # Strip control bytes and whitespace, then align to XML decl or first tag
    data = blob.lstrip(bytes(range(0, 33)))
    m = re.search(rb'<\?xml[^>]*\?>', data)
    if m:
        data = data[m.start():]
    else:
        m2 = re.search(rb'<[A-Za-z_][A-Za-z0-9._:-]*\b', data)
        if m2:
            data = data[m2.start():]
    if data.startswith(b'\xef\xbb\xbf'):
        data = data[3:]
    if not data:
        return b""

    # If there's another XML declaration later, keep only the first document
    j = data.find(b'<?xml', 5)
    if j != -1:
        data = data[:j]
        return data

    # Try to trim after the first root closing tag
    mroot = re.match(rb'(?:<\?xml[^>]*\?>\s*)?<([A-Za-z_][A-Za-z0-9._:-]*)\b', data)
    if mroot:
        root_name = mroot.group(1)
        close_pat = b'</' + root_name + b'>'
        k = data.rfind(close_pat)
        if k != -1:
            end = k + len(close_pat)
            data = data[:end]
    return data



def iter_uspto_subdocs(stream, chunk_size=1_048_576):
    buf = bytearray()
    START = b'<?xml'
    END   = b'</us-patent-grant>'
    keep  = max(len(START), len(END))  # tail we keep between chunks

    while True:
        chunk = stream.read(chunk_size)
        if chunk:
            buf += chunk
        else:
            # flush any final complete doc in buffer
            break

        # ensure we start at an XML decl
        s = buf.find(START)
        if s != -1 and s > 0:
            del buf[:s]

        while True:
            s = buf.find(START)
            if s == -1:
                # keep only tail to catch split boundaries
                if len(buf) > keep:
                    tail = buf[-keep:]
                    del buf[:-keep]
                    buf[:keep] = tail
                break
            e = buf.find(END, s)
            if e == -1:
                # need more bytes for a full doc
                if len(buf) > keep:
                    tail = buf[-keep:]
                    del buf[:-keep]
                    buf[:keep] = tail
                break
            e += len(END)
            # slice the complete doc
            xml_bytes = bytes(buf[s:e])
            yield xml_bytes
            del buf[:e]

    # At EOF, try to emit a last complete doc if present
    s = buf.find(START)
    e = buf.find(END, s) if s != -1 else -1
    if s != -1 and e != -1:
        e += len(END)
        yield bytes(buf[s:e])



def _collect_figure_assets(root: etree._Element, names: list[str], open_bytes_by_name) -> dict:
    """Collect figure image metadata and bytes for a single patent document.

    Returns a dict with key "images" -> list of {file, data, fig_ids, num}.
    If the weekly ZIP does not contain image files, the list will be empty.
    """
    images: list[dict] = []
    try:
        # Extract file names referenced in <drawings>/<figure>/<img file="..."> elements
        img_nodes = root.xpath(".//*[local-name()='drawings']//*[local-name()='figure']//*[local-name()='img']")
        if not img_nodes:
            return {"images": images}
        import os
        names_set = set(names)
        for img in img_nodes:
            file_attr = img.get("file") or img.get("href") or img.get("src")
            if not file_attr:
                continue
            # Normalize match by basename first
            base = os.path.basename(file_attr)
            # Find matching entry by basename
            match = next((n for n in names_set if os.path.basename(n) == base), None)
            data = None
            if match is not None:
                try:
                    data = open_bytes_by_name(match)
                except Exception:
                    data = None
            # Find related figure ids and number
            fig = img.getparent()
            while fig is not None and (etree.QName(fig).localname.lower() != 'figure'):
                fig = fig.getparent()
            fig_id = fig.get("id") if fig is not None else None
            fig_num = fig.get("num") if fig is not None else None
            rec = {"file": base, "data": data, "fig_ids": [fig_id] if fig_id else [], "num": fig_num}
            images.append(rec)
    except Exception:
        pass
    return {"images": images}


def _guess_media_type(filename: str | None) -> str:
    if not filename:
        return "application/octet-stream"
    media_type, _ = mimetypes.guess_type(filename)
    return media_type or "application/octet-stream"


def _b64encode_data(data: bytes | None) -> str | None:
    if not data:
        return None
    return base64.b64encode(data).decode("ascii")


_BROWSER_SAFE_MEDIA_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "image/svg+xml",
}
_TIFF_MEDIA_TYPES = {"image/tiff", "image/x-tiff"}
_TIFF_EXTS = (".tif", ".tiff")

def _http_get_with_retry(url: str, *, headers: dict | None = None, max_retries: int = 3, log_404: bool = True, log_error: bool = True):
    """HTTP GET with exponential backoff on 429/5xx. Returns response or None on final failure/404."""
    headers = headers or {}
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            status = resp.status_code
            if status == 404:
                if log_404:
                    print(f"[http] 404 for {url}")
                return None
            if status == 429 or 500 <= status < 600:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    if log_error:
                        print(f"[http] {status} for {url}; retrying in {wait}s")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            if log_error:
                print(f"[http] error for {url}: {e}")
            return None
    return None


def _ensure_browser_safe_image(
    *,
    filename: str | None,
    media_type: str,
    data: bytes | None,
) -> tuple[str, bytes | None]:
    """Convert non-web-native figure assets into PNG thumbnails."""
    if not data:
        return media_type, data
    if media_type in _BROWSER_SAFE_MEDIA_TYPES:
        return media_type, data
    lower_name = (filename or "").lower()
    needs_conversion = media_type in _TIFF_MEDIA_TYPES or lower_name.endswith(_TIFF_EXTS)
    if not needs_conversion:
        return media_type, data
    try:
        from PIL import Image  # type: ignore
    except Exception:
        if not getattr(_ensure_browser_safe_image, "_warned_pillow", False):
            print("[warn] Pillow not installed; cannot convert TIFF to PNG. Install 'Pillow' to enable figure previews.")
            _ensure_browser_safe_image._warned_pillow = True
        return media_type, data
    try:
        with Image.open(io.BytesIO(data)) as img_obj:
            frame = img_obj.convert("RGBA") if img_obj.mode not in ("RGB", "RGBA") else img_obj
            buf = io.BytesIO()
            frame.save(buf, format="PNG")
            return "image/png", buf.getvalue()
    except Exception:
        return media_type, data


def _fig_images_for_refs(refs: list[str], doc_assets: dict, cache: dict[str, dict]) -> list[dict]:
    """Resolve figure references to image payloads with base64 data."""
    images = (doc_assets or {}).get("images") or []
    if not refs or not images:
        return []
    def _normalize_ref(r: str) -> set[str]:
        vals: set[str] = set()
        if not r:
            return vals
        vals.add(r)
        rl = r.lower()
        vals.add(rl)
        stripped = r.lstrip("0")
        if stripped:
            vals.add(stripped)
            vals.add(stripped.lower())
        alnum = re.sub(r"[^0-9a-z]+", "", rl)
        if alnum:
            vals.add(alnum)
        dashed = re.sub(r"[^0-9a-z]+", "-", rl).strip("-")
        if dashed:
            vals.add(dashed)
        tokens = [t for t in re.split(r"[^0-9a-z]+", rl) if t]
        if tokens:
            vals.update(tokens)
        return vals

    ref_set: set[str] = set()
    for r in refs:
        ref_set.update(_normalize_ref(r))
    if not ref_set:
        return []
    resolved: list[dict] = []
    for idx, img in enumerate(images):
        fig_ids = [fid for fid in (img.get("fig_ids") or []) if fid]
        fig_id_vals = set()
        for fid in fig_ids:
            if not fid:
                continue
            fig_id_vals.update(_normalize_ref(fid))
        fig_num = img.get("num")
        num_candidates = set()
        if fig_num:
            num_candidates.update(_normalize_ref(fig_num))
        match = bool(ref_set.intersection(fig_id_vals))
        if not match and num_candidates:
            match = bool(ref_set.intersection(num_candidates))
        if not match:
            continue
        cache_key = img.get("file") or f"idx-{idx}"
        if cache_key not in cache:
            payload = {
                "file": img.get("file"),
                "fig_ids": fig_ids,
                "num": fig_num,
                "media_type": _guess_media_type(img.get("file")),
            }
            data_b64 = _b64encode_data(img.get("data"))
            if data_b64:
                payload["data_b64"] = data_b64
            cache[cache_key] = payload
        resolved.append(cache[cache_key].copy())
    return resolved


def _attach_fig_images_to_chunks(doc_chunks: list[dict], doc_assets: dict | None):
    """Attach resolved figure images to any chunk containing figure references."""
    if not doc_chunks or not doc_assets:
        return
    payload_cache: dict[str, dict] = {}
    for chunk in doc_chunks:
        refs = chunk.get("fig_refs") or []
        if not refs:
            continue
        imgs = _fig_images_for_refs(refs, doc_assets, payload_cache)
        if imgs:
            chunk["fig_images"] = imgs


def _images_to_payloads(images: list[dict] | None, limit: int = 6) -> list[dict]:
    """Convert raw image assets to base64 payloads (no format conversion)."""
    if not images:
        return []
    payloads: list[dict] = []
    for img in images:
        media_type = _guess_media_type(img.get("file"))
        data_b64 = _b64encode_data(img.get("data"))
        if not data_b64:
            continue
        payloads.append({
            "file": img.get("file"),
            "fig_ids": img.get("fig_ids"),
            "num": img.get("num"),
            "media_type": media_type,
            "data_b64": data_b64,
        })
        if len(payloads) >= limit:
            break
    return payloads


def _append_figures_chunk(chunks: list, doc_chunks: list[dict] | None, doc_assets: dict | None, meta: dict):
    """If images exist but no chunk has fig_images, add a dedicated figures chunk."""
    if not doc_assets:
        return
    images = doc_assets.get("images") or []
    if not images:
        return
    if any(c.get("fig_images") for c in (doc_chunks or [])):
        return
    payloads = _images_to_payloads(images)
    if not payloads:
        return
    record = {
        "section": "figures",
        "chunk": "",
        "filing_date": meta.get("filing_date"),
        "doc_id": meta.get("doc_id"),
        "kind": meta.get("kind"),
        "authors": meta.get("authors"),
        "classification": meta.get("classification"),
        "title": meta.get("title"),
        "fig_images": payloads,
    }
    _append_chunk(chunks, doc_chunks, record)


def _convert_doc_assets_to_png(doc_assets: dict) -> tuple[dict, dict]:
    """
    Convert TIFF images in doc_assets to PNG for browser display.
    Returns (converted_assets, file_map) where file_map maps original filenames to new filenames and media types.
    """
    images = (doc_assets or {}).get("images") or []
    try:
        from PIL import Image  # type: ignore
    except Exception:
        return doc_assets, {}

    converted: list[dict] = []
    file_map: dict[str, dict] = {}
    for img in images:
        fname = img.get("file")
        data = img.get("data")
        if not fname or data is None:
            converted.append(img)
            continue
        media_type = _guess_media_type(fname)
        needs_conv = media_type in _TIFF_MEDIA_TYPES or fname.lower().endswith(_TIFF_EXTS)
        if not needs_conv:
            converted.append(img)
            continue
        try:
            with Image.open(io.BytesIO(data)) as im:
                frame = im.convert("RGBA") if im.mode not in ("RGB", "RGBA") else im
                buf = io.BytesIO()
                frame.save(buf, format="PNG")
                new_bytes = buf.getvalue()
                new_name = Path(fname).with_suffix(".png").name
                rec = {
                    "file": new_name,
                    "data": new_bytes,
                    "fig_ids": img.get("fig_ids"),
                    "num": img.get("num"),
                }
                converted.append(rec)
                file_map[fname] = {
                    "file": new_name,
                    "media_type": "image/png",
                    "data_b64": _b64encode_data(new_bytes),
                }
        except Exception:
            converted.append(img)
    return {"images": converted}, file_map


def _remap_chunk_fig_images(doc_chunks: list[dict], file_map: dict[str, dict]):
    """Update fig_images entries to use converted filenames/data if present."""
    if not doc_chunks or not file_map:
        return
    for ch in doc_chunks:
        figs = ch.get("fig_images") or []
        changed = False
        new_figs = []
        for f in figs:
            fname = f.get("file")
            if fname and fname in file_map:
                mapped = file_map[fname]
                nf = dict(f)
                nf["file"] = mapped.get("file", fname)
                nf["media_type"] = mapped.get("media_type", nf.get("media_type"))
                if mapped.get("data_b64"):
                    nf["data_b64"] = mapped["data_b64"]
                new_figs.append(nf)
                changed = True
            else:
                new_figs.append(f)
        if changed:
            ch["fig_images"] = new_figs


def _fig_refs_in_elem(elem: etree._Element) -> list[str]:
    """Return list of figure references (ids or numbers) used in this element."""
    refs: list[str] = []
    seen: set[str] = set()
    try:
        for fr in elem.xpath(".//*[local-name()='figref']"):
            rid = fr.get("idref") or fr.get("id")
            txt = (" ".join(fr.itertext())).strip()
            if rid:
                if rid not in seen:
                    refs.append(rid)
                    seen.add(rid)
            if txt:
                # Heuristic: capture numeric ref text (e.g., "FIG. 1")
                m = re.search(r"\b(\d{1,3})\b", txt)
                if m:
                    num = m.group(1)
                    if num not in seen:
                        refs.append(num)
                        seen.add(num)
    except Exception:
        pass
    return refs


def outline(elem, depth=0, max_depth=3, max_children=8):
    if depth > max_depth:
        return
    name = etree.QName(elem).localname if isinstance(elem.tag, str) else str(elem.tag)
    attrs = " ".join(f'{k}="{v}"' for k, v in list(elem.attrib.items())[:3])
    line = f"- {name}" + (f" [{attrs}]" if attrs else "")
    print(" " * depth + line)
    kids = list(elem)
    for child in kids[:max_children]:
        outline(child, depth+1, max_depth=max_depth, max_children=max_children)
    if len(kids) > max_children:
        print(" " * (depth+1) + f"... ({len(kids)-max_children} more)")
            

def jpaths(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from jpaths(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from jpaths(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj


def xp_text_any(elem, paths):
    for xp in paths:
        vals = elem.xpath(xp)
        if vals:
            v = vals[0]
            if isinstance(v, etree._Element):
                t = " ".join(" ".join(v.itertext()).split())
            else:
                t = " ".join(str(v).split())
            if t:
                return t
    return None


def is_sequence_listing(root) -> bool:
    name = etree.QName(root).localname.lower() if isinstance(root.tag, str) else str(root.tag).lower()
    # Broaden match: any root containing "sequence" (e.g., sequence-cwu, SequenceListing)
    if 'sequence' in name:
        return True
    # Heuristic: some roots carry ST.26-like namespaces
    try:
        ns_uri = etree.QName(root).namespace or ''
    except Exception:
        ns_uri = ''
    return 'st.26' in ns_uri.lower() or 'sequence' in ns_uri.lower()


def extract_primary_classification(root) -> str | None:
    """Namespace-agnostic extraction of a primary classification symbol.
    Preference order:
    1) CPC symbol (classification-cpc/symbol or inline text)
    2) Construct CPC symbol from parts: section+class+subclass + main-group/subgroup
    3) IPC main-classification
    4) Locarno main-classification (designs)
    Returns a short string like "H01M 10/052" or similar.
    """
    # 1) CPC explicit symbol, if present
    sym = xp_text_any(root, [
        "//*[local-name()='classifications-cpc']//*[local-name()='classification-cpc']//*[local-name()='symbol']/text()",
        "//*[local-name()='classifications-cpc']//*[local-name()='main-cpc']//*[local-name()='symbol']/text()",
        "//*[local-name()='classifications-cpc']//*[local-name()='classification-cpc']/text()",
        "//*[local-name()='classifications-cpc']//*[local-name()='main-cpc']/text()",
    ])
    if sym:
        return sym
    # 2) Build from CPC parts
    nodes = root.xpath("//*[local-name()='classifications-cpc']//*[local-name()='main-cpc']//*[local-name()='classification-cpc']")
    if not nodes:
        nodes = root.xpath("//*[local-name()='classifications-cpc']//*[local-name()='classification-cpc']")
    if nodes:
        node = nodes[0]
        section = first_text_local(node, ".//*[local-name()='section']/text()")
        cl      = first_text_local(node, ".//*[local-name()='class']/text()")
        subcl   = first_text_local(node, ".//*[local-name()='subclass']/text()")
        mgrp    = first_text_local(node, ".//*[local-name()='main-group']/text()")
        sgrp    = first_text_local(node, ".//*[local-name()='subgroup']/text()")
        left = "".join([x or "" for x in (section, cl, subcl)])
        right = "/".join([x for x in (mgrp, sgrp) if x]) if (mgrp or sgrp) else None
        if left and right:
            return f"{left} {right}"
        if left:
            return left
        # If parts missing, fall back to any text under classification-cpc (helps some design filings)
        raw_txt = " ".join(" ".join(node.itertext()).split())
        if raw_txt:
            return raw_txt
    # 3) IPC main-classification
    ipc = xp_text_any(root, [
        "//*[local-name()='classification-ipc']//*[local-name()='main-classification']/text()",
    ])
    if ipc:
        return ipc
    # 4) Locarno (design)
    loc = xp_text_any(root, [
        "//*[local-name()='classification-locarno']//*[local-name()='main-classification']/text()",
    ])
    if loc:
        return loc
    return None


def extract_title(root) -> str | None:
    """Extract title, concatenating text across child nodes (handles subscripts, italics)."""
    paths = [
        "//*[local-name()='invention-title']",
        "//*[local-name()='us-bibliographic-data']//*[local-name()='invention-title']",
        "//*[local-name()='title']",
        "//title",
    ]
    for xp in paths:
        nodes = root.xpath(xp)
        if not nodes:
            continue
        n0 = nodes[0]
        if isinstance(n0, etree._Element):
            text = " ".join(" ".join(n0.itertext()).split())
            if text:
                return text
        else:
            # Nodes may be text strings; join them
            joined = " ".join(" ".join(str(x).split()) for x in nodes if str(x).strip())
            if joined:
                return joined
    return None


def extract_all_cpc_symbols(root) -> list[str]:
    """Return all CPC symbols present (deduped, order-preserving)."""
    vals: list[str] = []
    def _add(val: str | None):
        if val:
            v = " ".join(val.split())
            if v and v not in vals:
                vals.append(v)

    # Direct symbols
    sym_nodes = root.xpath("//*[local-name()='classifications-cpc']//*[local-name()='classification-cpc']//*[local-name()='symbol']/text()")
    for s in sym_nodes:
        _add(s)
    # Inline text under classification-cpc/main-cpc
    inline_nodes = root.xpath("//*[local-name()='classifications-cpc']//*[local-name()='classification-cpc']/text() | //*[local-name()='classifications-cpc']//*[local-name()='main-cpc']/text()")
    for s in inline_nodes:
        _add(s)
    # Build from parts for each classification-cpc
    nodes = root.xpath("//*[local-name()='classifications-cpc']//*[local-name()='classification-cpc']")
    for node in nodes:
        section = first_text_local(node, ".//*[local-name()='section']/text()")
        cl      = first_text_local(node, ".//*[local-name()='class']/text()")
        subcl   = first_text_local(node, ".//*[local-name()='subclass']/text()")
        mgrp    = first_text_local(node, ".//*[local-name()='main-group']/text()")
        sgrp    = first_text_local(node, ".//*[local-name()='subgroup']/text()")
        left = "".join([x or "" for x in (section, cl, subcl)])
        right = "/".join([x for x in (mgrp, sgrp) if x]) if (mgrp or sgrp) else None
        if left and right:
            _add(f"{left} {right}")
        elif left:
            _add(left)
        else:
            raw_txt = " ".join(" ".join(node.itertext()).split())
            _add(raw_txt)
    return vals


def extract_application_number(root, *, doc_id: str | None = None) -> str | None:
    """Return the best application number from application-reference/document-id."""
    doc_elems = root.xpath("//application-reference//document-id")
    best: str | None = None
    for de in doc_elems:
        nums = de.xpath(".//*[local-name()='doc-number']/text()")
        if not nums:
            continue
        val = nums[0].strip()
        if not val:
            continue
        # Prefer a number containing '/' or ',' (formatted app number)
        if "/" in val or "," in val:
            return val
        # Avoid picking the publication/grant number when doc_id is known
        if doc_id and val == doc_id:
            continue
        if best is None:
            best = val
    return best or (doc_id if doc_id else None)


def parse_sequence_listing(root, prev_meta=None):
    chunks = []
    doc_id = xp_text_any(root, [
        "//*[local-name()='publication-reference']//*[local-name()='doc-number']/text()",
        "//*[local-name()='document-id']//*[local-name()='doc-number']/text()",
    ])
    filing_date = xp_text_any(root, [
        "//*[local-name()='application-reference']//*[local-name()='document-id']//*[local-name()='date']/text()",
        "//*[local-name()='filing-date']/text()",
    ])
    authors = xp_text_any(root, [
        "//*[local-name()='applicants']//*[local-name()='applicant']//*[local-name()='name']/text()",
        "//*[local-name()='applicants']//*[local-name()='applicant']//*[local-name()='orgname']/text()",
    ])
    classification = extract_primary_classification(root)

    # If associated to the previous patent, carry over its metadata
    if prev_meta:
        authors = prev_meta.get("authors") or authors
        classification = prev_meta.get("classification") or classification
        filing_date = prev_meta.get("filing_date") or filing_date

    sequences = root.xpath("//*[local-name()='Sequence'] | //*[local-name()='INSDSeq']")
    seq_limit = 100
    count = 0
    for seq in sequences:
        if count >= seq_limit:
            break
        seq_id = xp_text_any(seq, [
            ".//*[local-name()='INSDSeq_sequence-identifier']/text()",
            ".//*[local-name()='SequenceID']/text()",
            ".//*[local-name()='SeqID']/text()",
            ".//*[local-name()='SEQUENCE-ID']/text()",
            ".//*[local-name()='INSDSeq_locus']/text()",
        ])
        mol_type = xp_text_any(seq, [
            ".//*[local-name()='MoleculeType']/text()",
            ".//*[local-name()='INSDSeq_moltype']/text()",
        ])
        organism = xp_text_any(seq, [
            ".//*[local-name()='Organism']/text()",
            ".//*[local-name()='INSDSeq_organism']/text()",
        ])
        title = xp_text_any(seq, [
            ".//*[local-name()='Title']/text()",
            ".//*[local-name()='Definition']/text()",
            ".//*[local-name()='INSDSeq_definition']/text()",
        ])
        feature = xp_text_any(seq, [
            ".//*[local-name()='FeatureKey']/text()",
            ".//*[local-name()='INSDFeature_key']/text()",
        ])
        product = xp_text_any(seq, [
            ".//*[local-name()='Product']/text()",
            ".//*[local-name()='INSDQualifier_value']/text()",
        ])
        comment = xp_text_any(seq, [
            ".//*[local-name()='Comment']/text()",
            ".//*[local-name()='INSDSeq_comment']/text()",
        ])

        parts = []
        if seq_id:
            parts.append(f"SEQ ID NO: {seq_id}")
        if title:
            parts.append(f"Title: {title}")
        if mol_type:
            parts.append(f"Molecule: {mol_type}")
        if organism:
            parts.append(f"Organism: {organism}")
        if feature:
            parts.append(f"Feature: {feature}")
        if product:
            parts.append(f"Product: {product}")
        if comment:
            parts.append(f"Comment: {comment}")
        text = ". ".join(p for p in parts if p)[:4000]
        if text:
            chunks.append({
                "section": "sequence-metadata",
                "chunk": text,
                "filing_date": filing_date,
                "doc_id": doc_id,
                "authors": authors,
                "classification": classification,
                "doc_type": "sequence-listing",
                "title": (prev_meta.get("title") if prev_meta else None),
                "kind": (prev_meta.get("kind") if prev_meta else None),
                "sequence": {
                    "seq_id": seq_id,
                    "title": title,
                    "molecule": mol_type,
                    "organism": organism,
                    "feature": feature,
                    "product": product,
                    "comment": comment,
                },
            })
            count += 1

    if count:
        chunks.append({
            "section": "sequence-summary",
            "chunk": f"Sequence listing with {len(sequences)} sequences; indexed {count} summaries.",
            "filing_date": filing_date,
            "doc_id": doc_id,
            "authors": authors,
            "classification": classification,
            "doc_type": "sequence-listing",
            "title": (prev_meta.get("title") if prev_meta else None),
            "kind": (prev_meta.get("kind") if prev_meta else None),
        })
    return chunks


def first_text_local(elem, xp):
    nodes = elem.xpath(xp)
    if not nodes:
        return None
    n0 = nodes[0]
    if isinstance(n0, etree._Element):
        return " ".join(" ".join(n0.itertext()).split())
    return " ".join(str(n0).split())


def fetch_metadata(app_no: str, *, log_404: bool = True, log_error: bool = True) -> dict | None:
    encoded = urllib.parse.quote(str(app_no), safe="")
    url = f"https://api.uspto.gov/api/v1/patent/applications/{encoded}/meta-data"
    headers_meta = {"x-api-key": api_key}
    resp = _http_get_with_retry(url, headers=headers_meta, max_retries=3, log_404=log_404, log_error=log_error)
    if resp is None:
        return None
    try:
        return resp.json()
    except Exception as e:
        if log_error:
            print(f"metadata json error for {app_no}: {e}")
        return None


def fetch_publication_metadata(pub_no: str, *, log_404: bool = True, log_error: bool = True) -> dict | None:
    """Fallback lookup by publication number."""
    url = f"https://api.uspto.gov/api/v1/patent/publications/{pub_no}/meta-data"
    headers_meta = {"x-api-key": api_key}
    resp = _http_get_with_retry(url, headers=headers_meta, max_retries=3, log_404=log_404, log_error=log_error)
    if resp is None:
        return None
    try:
        return resp.json()
    except Exception as e:
        if log_error:
            print(f"metadata pub json error for {pub_no}: {e}")
        return None


def _pub_number_variants(doc_id: str | None, kind: str | None) -> list[str]:
    if not doc_id:
        return []
    doc_id = str(doc_id)
    kind = (kind or "").strip()
    variants = [doc_id]
    if kind:
        variants.append(f"{doc_id}{kind}")
    variants.append(f"US{doc_id}")
    if kind:
        variants.append(f"US{doc_id}{kind}")
    seen = set()
    uniq = []
    for v in variants:
        if v and v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq


def _normalize_text(val: str | None) -> str:
    if val is None:
        return ""
    return " ".join(str(val).lower().split())


def _normalize_date(val: str | None) -> str:
    if val is None:
        return ""
    return re.sub(r"[^0-9]", "", str(val))


def _normalize_number_candidates(val: str | None) -> list[str]:
    if val is None:
        return []
    digits = re.sub(r"[^0-9]", "", str(val))
    if not digits:
        return []
    return [digits]


def _titles_equivalent(parsed: str, api: str) -> bool:
    """Return True if titles match after normalization and aggressive stripping."""
    if parsed == api:
        return True
    if not parsed or not api:
        return False
    # Remove all whitespace for a looser comparison
    strip_ws = lambda s: re.sub(r"\s+", "", s)
    if strip_ws(parsed) == strip_ws(api):
        return True
    # Remove non-alphanumerics for an even looser comparison
    strip_non = lambda s: re.sub(r"[^0-9a-z]+", "", s)
    return strip_non(parsed) == strip_non(api)


def _normalize_cpc_list(val) -> set[str]:
    """Normalize CPC codes to uppercase strings without spaces."""
    codes: set[str] = set()
    if val is None:
        return codes
    try:
        items = val if isinstance(val, (list, builtins.tuple)) else [val]
    except TypeError:
        items = [val]
    for item in items:
        if item is None:
            continue
        for tok in re.split(r"[,\s]+", str(item)):
            t = tok.strip().replace(" ", "").upper()
            if t:
                codes.add(t)
    return codes


def _cpc_sets_match(parsed: set[str], api: set[str]) -> bool:
    """Return True if every parsed CPC code is represented in API codes, allowing prefix/suffix differences.

    We consider codes equivalent if, after uppercasing and stripping spaces,
    either code is a substring of the other, or one endswith the other (e.g.,
    parsed '2300/125' matches API 'B60W2300/125').
    """
    if not parsed:
        return True
    if not api:
        return False

    def norm(c: str) -> str:
        return re.sub(r"\s+", "", c.upper())

    api_norm = [norm(a) for a in api if a]
    for p in parsed:
        np = norm(p)
        matched = False
        for a in api_norm:
            if a == np or a.endswith(np) or np.endswith(a) or np in a or a in np:
                matched = True
                break
        if not matched:
            return False
    return True


def _extract_api_title(api_meta: dict, amd: dict, entry: dict | None) -> str:
    """Get invention title from API response (search bag entries first, then top-level)."""
    candidates: list[str | None] = []
    bag = api_meta.get("patentFileWrapperDataBag") or api_meta.get("patentFileWrapperData") or []
    if isinstance(bag, dict):
        bag = [bag]
    for ent in bag if isinstance(bag, list) else []:
        ent_meta = ent.get("applicationMetaData") or ent.get("applicationMetadata") or {}
        candidates.extend([
            ent.get("inventionTitleText"),
            ent.get("inventionTitle"),
            ent.get("titleText"),
            ent.get("title"),
            ent_meta.get("inventionTitleText"),
            ent_meta.get("inventionTitle"),
            ent_meta.get("titleText"),
            ent_meta.get("title"),
        ])
    candidates.extend([
        (entry or {}).get("inventionTitleText"),
        (entry or {}).get("inventionTitle"),
        (entry or {}).get("titleText"),
        (entry or {}).get("title"),
        amd.get("inventionTitleText"),
        amd.get("inventionTitle"),
        amd.get("titleText"),
        amd.get("title"),
    ])
    for cand in candidates:
        cleaned = _normalize_text(cand)
        if cleaned and cleaned != "none":
            return cleaned
    return ""


def _maybe_validate_metadata(meta: dict | None, *, enable: bool, verbose: bool, collector: Optional["MetadataMismatchCollector"] = None):
    if not enable or not meta:
        return None
    try:
        res = _validate_metadata_with_api(meta, verbose=verbose)
        if res and res.get("mismatches"):
            app_no = meta.get("application_number") or meta.get("doc_id")
            print(f"[metadata] mismatch for app {app_no}: {', '.join(m['field'] for m in res['mismatches'])}")
            if collector:
                collector.record(meta.get("doc_id"), res["mismatches"])
        elif collector and res is None:
            collector.record_skip(meta.get("doc_id"), "api_not_found_or_missing_meta")
        return res
    except Exception as e:
        print(f"[metadata] validation error for {meta.get('doc_id')}: {e}")
        return None


class MetadataMismatchCollector:
    """Collect metadata mismatches and write them to CSV."""
    def __init__(self, csv_path: Path):
        self.csv_path = Path(csv_path)
        self._rows: list[dict] = []
        self._skips: list[dict] = []

    def record(self, doc_id: str | None, mismatches: list[dict]):
        for m in mismatches:
            self._rows.append({
                "doc_id": doc_id or "",
                "field": m.get("field") or "",
                "parsed": m.get("parsed") or "",
                "api": m.get("api") or "",
            })

    def record_skip(self, doc_id: str | None, reason: str):
        self._skips.append({
            "doc_id": doc_id or "",
            "reason": reason,
        })

    def flush(self) -> int:
        written = 0
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        if self._rows:
            fieldnames = ["doc_id", "field", "parsed", "api"]
            header_needed = not self.csv_path.exists() or self.csv_path.stat().st_size == 0
            with self.csv_path.open("a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                if header_needed:
                    w.writeheader()
                w.writerows(self._rows)
            written += len(self._rows)
            self._rows = []

        # Write skips to a companion CSV
        if self._skips:
            skips_path = self.csv_path.with_name(self.csv_path.stem + "_skips.csv")
            fieldnames = ["doc_id", "reason"]
            header_needed = not skips_path.exists() or skips_path.stat().st_size == 0
            with skips_path.open("a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                if header_needed:
                    w.writeheader()
                w.writerows(self._skips)
            written += len(self._skips)
            self._skips = []
        return written


def _validate_metadata_with_api(doc_meta: dict, *, verbose: bool = False) -> dict | None:
    """Compare parsed metadata to USPTO API metadata; return result dict."""
    doc_id = doc_meta.get("doc_id")
    app_no = doc_meta.get("application_number")
    kind = doc_meta.get("kind")
    api_meta = None
    # Use application number as the primary (unique) key for API lookups.
    if app_no:
        api_meta = fetch_metadata(str(app_no), log_404=verbose, log_error=verbose)
    # Only if no application number is available do we try publication lookups.
    if not api_meta and not app_no and doc_id:
        for pub in _pub_number_variants(doc_id, kind):
            api_meta = fetch_publication_metadata(pub, log_404=verbose, log_error=verbose)
            if api_meta:
                break
    if not api_meta:
        if verbose and (doc_id or app_no):
            print(f"[metadata] no metadata found for {doc_id or app_no}")
        return None
    # Extract application metadata; USPTO schema often nests in patentFileWrapperDataBag[0]
    bag = api_meta.get("patentFileWrapperDataBag") or api_meta.get("patentFileWrapperData") or []
    if isinstance(bag, dict):
        bag = [bag]
    amd = api_meta.get("applicationMetaData") or api_meta.get("applicationMetadata") or {}
    entry = None
    if not amd and isinstance(bag, list) and bag:
        entry = bag[0] or {}
        amd = entry.get("applicationMetaData") or entry.get("applicationMetadata") or {}
    if not entry and isinstance(bag, list) and bag:
        entry = bag[0] or {}
    if not amd:
        if verbose and (doc_id or app_no):
            print(f"[metadata] missing applicationMetaData in response for {doc_id or app_no}")
        return None
    app_no_api = (entry or {}).get("applicationNumberText") or amd.get("applicationNumberText") or amd.get("applicationNumber")
    # Prefer patentNumber for grant publication comparison; fall back to earliestPublicationNumber
    pub_api = amd.get("patentNumber") or amd.get("publicationNumber") or amd.get("earliestPublicationNumber")
    title_api_clean = _extract_api_title(api_meta, amd, entry)
    cpc_api = _normalize_cpc_list(amd.get("cpcClassificationBag"))
    cpc_parsed = _normalize_cpc_list(doc_meta.get("classification_cpc") or doc_meta.get("classification"))
    # Always print parsed vs API application identifiers for manual verification
    print(f"[metadata] parsed_app={app_no} api_app={app_no_api} pub_api={pub_api}")
    api_filing_dates = set()
    api_filing_dates = {d for d in api_filing_dates if d}
    parsed = {
        "doc_id": _normalize_text(doc_meta.get("doc_id")),
        "application_number": _normalize_text(app_no),
        "filing_date": _normalize_date(doc_meta.get("filing_date")),
        "title": _normalize_text(doc_meta.get("title")),
        "kind": _normalize_text(doc_meta.get("kind")),
    }
    api_vals = {
        "doc_id": _normalize_text(pub_api),
        "application_number": _normalize_text(app_no_api),
        "filing_date": _normalize_date(amd.get("filingDate")),
        "title": title_api_clean,
        # Kind code often absent in this schema; compare only if API provides one
        "kind": _normalize_text(amd.get("publicationKindCode") or amd.get("kind")),
    }
    comparisons: list[dict] = []
    for key in ["doc_id", "application_number", "title", "kind"]:
        if key == "title" and (not api_vals["title"] or api_vals["title"] == "none"):
            # Skip title mismatch when API title is missing or literal "None"
            continue
        if key == "doc_id":
            # Allow doc_id mismatch if application numbers align (some doc_ids map to multiple grants)
            match = (
                parsed[key] == api_vals[key]
                or (
                    parsed.get("application_number")
                    and api_vals.get("application_number")
                    and parsed.get("application_number") == api_vals.get("application_number")
                )
            )
        elif key == "title":
            match = _titles_equivalent(parsed[key], api_vals[key])
        else:
            match = parsed[key] == api_vals[key] if (parsed[key] or api_vals[key]) else True
        api_display = None
        if key == "title":
            api_display = title_api_clean or title_api_raw
        else:
            api_display = amd.get({
                "doc_id": "publicationNumber",
                "application_number": "applicationNumberText",
                "kind": "publicationKindCode",
            }.get(key, key))
        if key == "kind" and not api_vals["kind"]:
            # skip kind comparison if API did not provide it
            continue
        comparisons.append({"field": key, "match": match, "parsed": doc_meta.get(key), "api": api_display})
    # CPC classification comparison (subset match)
    if cpc_parsed or cpc_api:
        # Only evaluate when API returned CPC; if API is empty, skip mismatch logging
        if cpc_api:
            cpc_match = _cpc_sets_match(cpc_parsed, cpc_api)
            comparisons.append({
                "field": "cpc",
                "match": cpc_match,
                "parsed": sorted(cpc_parsed) if cpc_parsed else [],
                "api": sorted(cpc_api) if cpc_api else [],
            })
    mismatches = [c for c in comparisons if not c["match"] and (c["api"] or c["parsed"])]
    result = {
        "ok": not mismatches,
        "mismatches": mismatches,
    }
    if verbose and mismatches:
        print(f"[metadata] {doc_id} mismatches: " + "; ".join(f"{m['field']}: parsed='{m['parsed']}' api='{m['api']}'" for m in mismatches))
    return result
    

#meta = fetch_metadata(app_no)
#amd = meta.get("applicationMetaData", {})
#print(f"{app_no} status={amd.get('applicationStatusDescriptionText')}, "
#    f"filingDate={amd.get('filingDate')}, pubDate={amd.get('publicationDate')}")
'''
try:
    # Attempt to retrieve metadata for a single application
    response = requests.get(meta_template, headers=headers)
    response.raise_for_status()  # Raises an exception for 4xx/5xx errors
    data = response.json()       # Parse JSON response
    print(json.dumps(data, indent=4))  # Pretty-print metadata
except requests.exceptions.RequestException as e:
    print(f"Error connecting to USPTO API: {e}")
except json.JSONDecodeError as e:
    print(f"Error decoding JSON response: {e}")
'''

# --- Setup for USPTO Patent Applications Search API ---
import requests
import time

# Constants to manage rate limiting and retries
SLEEP_AFTER_429 = 0.1      # Wait 0.1 seconds after receiving a "Too Many Requests" response
SLEEP_BETWEEN_HTTP = 0     # Wait time between successive HTTP requests
HTTP_RETRY = 10            # Retry up to 10 times if 429 status code persists
MAX_RANGE = 10000          # Maximum offset range for pagination
LIMIT = 100                # Number of results per page (pagination size)

# The main USPTO patent applications search endpoint
url = 'https://api.uspto.gov/api/v1/patent/applications/search'

# Simplified headers for POST (requests will set Content-Type automatically)
headers = {
    'x-api-key': api_key
}

# --- JSON query template for searching patent applications ---
query_template = {
  "q": None,   # No free-text query (filters only)
  "filters": [  # Filtering conditions for returned applications
    {
      "name": "applicationMetaData.applicationTypeLabelName",
      "value": ["Utility"]  # Limit to utility patent applications
    },
    {
      "name": "applicationMetaData.publicationCategoryBag",
      "value": ["Pre-Grant Publications - PGPub"]  # Only pre-grant publications
    },
    {
      "name": "applicationMetaData.applicationStatusDescriptionText",
      "value": ["Non Final Action Mailed"]  # Only applications with this status
    }
  ],
  "rangeFilters": [  # Numeric/date range filter
    {
      "field": "applicationMetaData.filingDate",
      "valueFrom": "2010-10-01",
      "valueTo": "2023-10-30"  # Filter by filing date
    }
  ],
  "pagination": {  # Pagination settings
    "offset": 0,   # Start from record 0 (updated dynamically per loop)
    "limit": LIMIT # Return LIMIT records per request
  },
  "sort": [  # Sort results in descending order by filing date
    {
      "field": "applicationMetaData.filingDate",
      "order": "Desc"
    }
  ],
  "fields": ["applicationNumberText", "applicationMetaData"]  # Only request these fields
}

# Initialize an empty list to store all retrieved application numbers
application_numbers_api = []

# --- Function to make a paginated search request ---
def make_search_request(offset, retry=0):
    # Create a shallow copy of the query template and update the offset
    query = query_template.copy()
    query['pagination']['offset'] = offset

    # Send the POST request with the query payload
    response = requests.post(url, headers=headers, json=query)

    # --- Handle successful request ---
    if response.status_code == 200:
        data = response.json()  # Parse the JSON response body
        # Extract application numbers from the response if the key exists
        return [item['applicationNumberText'] for item in data.get('patentFileWrapperDataBag', [])], None

    # --- Handle rate limiting (HTTP 429) ---
    elif response.status_code == 429:
        if retry < HTTP_RETRY:
            time.sleep(SLEEP_AFTER_429)         # Wait briefly before retrying
            retry += 1                          # Increment retry count
            return make_search_request(offset, retry)  # Recursive retry

    # --- Handle all other errors ---
    return None, response  # Return the response for error handling outside



def bulk_dataset_download(
    input_date: str | datetime,
    path: Path = Path('.'),
    *,
    sample_k: int = 50,
    sample_out_dir: Path | None = None,
    sample_seed: int | None = None,
    use_manifest: bool = False,
    dataset_product: str = "PTGRDT",
    verbose: bool = False,
    return_chunks: bool = True,
    batch_size: int | None = None,
    on_batch: Callable[[list[dict]], None] | None = None,
    validate_metadata: bool = False,
    metadata_mismatch_csv: Path | None = None,
    max_patents: int | None = 1000,
) -> list[dict] | None:
    '''This function takes in a start date and creates an end date 7 days later.
    It then queries the USPTO bulk data API for available datasets in that date range.
    This is currently working off of the application data and not grant data. Need to
    switch it over.

    Sampling/export controls (for manual inspection):
    - sample_k: number of patents to export as Markdown (0 to skip)
    - sample_out_dir: directory for Markdown and CSV (defaults to `path`)
    - sample_seed: set to make sampling deterministic
    - dataset_product: USPTO dataset product slug (default PTGRDT which
      includes images). You can override if needed.
    - return_chunks: set False to stream processing without storing every chunk
      (useful for large weekly dumps when sampling is disabled).
    - batch_size/on_batch: provide both to process chunks incrementally.
      Each time `batch_size` chunks are parsed (or at the end) `on_batch`
      receives a list you can embed/store before the next batch arrives.
    '''
    global VERBOSE
    VERBOSE = bool(verbose)
    path = Path(path)
    meta_validate = bool(validate_metadata)
    meta_mismatch_collector = MetadataMismatchCollector(metadata_mismatch_csv) if (meta_validate and metadata_mismatch_csv) else None
    sample_enabled = bool(sample_k and sample_k > 0)
    assets_by_doc: dict[str, dict] | None = {} if sample_enabled else None
    return_chunks = bool(return_chunks)
    # Always collect chunk data when sampling so doc_ids are available
    collect_chunks = return_chunks or sample_enabled
    max_patents = max_patents if (max_patents is None or max_patents > 0) else None
    seen_doc_ids: set[str] = set()
    stop_processing = False

    def _register_doc_id(doc_id: str | None) -> bool:
        nonlocal stop_processing
        if not doc_id:
            return False
        if doc_id in seen_doc_ids:
            return True
        if max_patents is not None and len(seen_doc_ids) >= max_patents:
            stop_processing = True
            return False
        seen_doc_ids.add(doc_id)
        return True
    sampler: StreamingSampler | None = None
    sample_target_dir = sample_out_dir or path
    if sample_enabled:
        manifest_ids = None
        if use_manifest:
            manifest_path = sample_target_dir / "sampled" / "sample_manifest.csv"
            manifest_ids = _load_manifest_doc_ids(manifest_path)
            if not manifest_ids:
                manifest_ids = None
        sampler = StreamingSampler(k=sample_k, out_dir=sample_target_dir, seed=sample_seed, manifest_doc_ids=manifest_ids)

    base, ext_hint, last_tuesday, product_upper = _dataset_file_base(input_date, path, dataset_product)
    file_stem = base.name
    path.mkdir(parents=True, exist_ok=True)
    existing_path = _find_existing_archive(base)
    file_path = existing_path or base.with_suffix(ext_hint)
    file_url = f"https://api.uspto.gov/api/v1/datasets/products/files/{dataset_product}/{last_tuesday:%Y}/{file_stem}{ext_hint}"
    tmp_path = Path(str(file_path) + ".part")
    
    #Below is only for testing purposes: should be removed later since file IO allows for deletion
    if file_path.exists() and file_path.stat().st_size > 0:
        print(f"Using existing archive: {file_path} ({file_path.stat().st_size:,} bytes)")
    else:
        tmp_path = file_path.with_suffix(file_path.suffix + ".part")
        print(file_stem)
        print(file_url)
        # Download to a temporary file to avoid corrupt partials on failure
        _download_with_retry(file_url, file_path, tmp_path)
    def clean_text(path):
        # Given an input path, finds the root associated with that path,
        # then clean all text by removing whitespace
        parts = root.xpath(path)
        return " ".join(t.strip() for t in parts if t.strip())

    def _flush_meta_mismatches():
        if not meta_mismatch_collector:
            return
        n = meta_mismatch_collector.flush()
        if n:
            print(f"[metadata] wrote {n} mismatch row(s) to {meta_mismatch_collector.csv_path}")

    #tmp_path.replace(file_path)  # rename .part -> .zip after success
    print(f"Saved/using: {file_path} ({file_path.stat().st_size:,} bytes)")
    if product_upper == "APPXML":
        with ZipFile(file_path, mode="r") as zf:
            members = [n for n in zf.namelist() if not n.endswith("/")]
            xml_members = [n for n in members if n.lower().endswith(".xml")]
            if not xml_members:
                raise FileNotFoundError("No .xml file found inside APPXML zip")
            inner_xml = xml_members[0]
            print(f"[archive] ZIP (APPXML) inner XML: {inner_xml}")
            def _names():
                return members
            def _open_bytes(name: str) -> bytes:
                with zf.open(name) as f:
                    return f.read()
            parser = make_parser()
            chunks = _ChunkCollector(collect=collect_chunks, batch_size=batch_size, on_batch=on_batch)
            last_doc_meta = None
            with zf.open(inner_xml, "r") as xml_stream:
                for i, blob in enumerate(iter_uspto_subdocs(xml_stream), start=1):
                    xml_blob = clamp_patent_doc(blob)
                    parser_strict = make_parser()
                    parser_recover = etree.XMLParser(
                        resolve_entities=False,
                        load_dtd=False,
                        no_network=True,
                        huge_tree=True,
                        recover=True,
                        remove_comments=True,
                    )
                    try:
                        root = etree.fromstring(xml_blob, parser=parser_strict)
                    except etree.XMLSyntaxError as e:
                        try:
                            root = etree.fromstring(xml_blob, parser=parser_recover)
                            print(f"[warn] subdoc {i} strict-parse failed but recovered: {e}")
                        except Exception:
                            save_failed(i, xml_blob, "xml_syntax_error", None)
                            print(f"[warn] subdoc {i} unrecoverable parse error: {e}")
                            continue
                    if is_sequence_listing(root):
                        continue
                    counter = 0
                    authors = ""
                    doc_id = root.xpath("//publication-reference//document-id//doc-number//text()")
                    doc_id = doc_id[0] if doc_id else None
                    if doc_id and doc_id[:2] == "RE":
                        print(f"Skipping reissue patent {doc_id}")
                        continue
                    if not _register_doc_id(doc_id):
                        if stop_processing:
                            break
                        continue
                    app_number = extract_application_number(root, doc_id=doc_id)
                    kind_list = root.xpath("//publication-reference//document-id//kind//text()")
                    kind = kind_list[0].strip() if kind_list else None
                    doc_chunks: list[dict] | None = [] if sampler else None
                    if i % 25 == 0:
                        latest = doc_id or "unknown"
                        print(f"[progress][APPXML] Parsed {i} documents (last doc_id={latest})")
                    try:
                        filing_date = root.xpath("//application-reference//document-id//date//text()")[0]
                    except IndexError:
                        outline(root, max_depth=4, max_children=20)
                        print(root.xpath("//publication-reference//document-id//date//text()"))
                        print(f"Doc ID that failed is {doc_id}")
                        input("Fake breakpoint")
                        continue
                    classification = extract_primary_classification(root)
                    classification_cpc = extract_all_cpc_symbols(root)
                    title = extract_title(root)
                    first_names = root.xpath("//inventors//inventor//addressbook//first-name//text()")
                    last_names = root.xpath("//inventors//inventor//addressbook//last-name//text()")
                    for name in zip(first_names, last_names):
                        authors += " ".join(name) + "; "
                    authors = authors[:-2]
                    last_doc_meta = {
                        "authors": authors,
                        "classification": classification,
                        "classification_cpc": classification_cpc,
                        "filing_date": filing_date,
                        "doc_id": doc_id,
                        "application_number": app_number,
                        "kind": kind,
                        "title": title,
                    }
                    _maybe_validate_metadata(last_doc_meta, enable=meta_validate, verbose=verbose, collector=meta_mismatch_collector)
                    doc_buffer: list[dict] = []
                    def _record_chunk(payload: dict):
                        doc_buffer.append(payload)
                    for ordinal, claim in enumerate(root.xpath("//claims//claim"), start=1):
                        claim_text = elem_to_rich_text(claim).strip()
                        if not claim_text:
                            continue
                        claim_number = _extract_claim_number(claim, ordinal)
                        claim_type = _extract_claim_type(claim, claim_text)
                        claim_id = f"{doc_id}-CLM-{claim_number}"
                        _record_chunk(
                            {
                                "section": "claim",
                                "text": claim_text,
                                "claim_id": claim_id,
                                "claim_number": claim_number,
                                "claim_type": claim_type,
                                "filing_date": filing_date,
                                "doc_id": doc_id,
                                "kind": kind,
                                "authors": authors,
                                "classification": classification,
                                "title": title,
                            }
                        )
                        counter += 1
                    doc_chunks, counter = _finalize_doc_chunks(chunks, doc_buffer, sample_enabled=bool(sampler))
                    _log(f"[parse] doc {i}: {doc_id} (chunks: {counter})")
                    if sampler and doc_chunks and doc_id:
                        try:
                            doc_assets = _collect_figure_assets(root, _names(), _open_bytes)
                        except Exception:
                            doc_assets = {"images": []}
                        _attach_fig_images_to_chunks(doc_chunks, doc_assets)
                        _append_figures_chunk(
                            chunks,
                            doc_chunks,
                            doc_assets,
                            {
                                "filing_date": filing_date,
                                "doc_id": doc_id,
                                "kind": kind,
                                "authors": authors,
                                "classification": classification,
                                "title": title,
                            },
                        )
                        sampler.consider(doc_id, doc_chunks, doc_assets)
            if sampler:
                sampler.finalize()
            _flush_collector(chunks)
            print("[done] Completed processing all subdocuments (APPXML zip).")
            _flush_meta_mismatches()
            if return_chunks:
                return chunks
            return None
    is_tar = file_path.name.lower().endswith((".tar", ".tar.gz", ".tgz"))
    if is_tar:
        with tarfile.open(file_path, mode='r:*') as tf:
            members = [m for m in tf.getmembers() if m.isfile() and _is_util_member(m.name)]
            try:
                total_files = len(members)
            except Exception:
                total_files = 0
            print(f"[archive] TAR opened: {file_path} (files: {total_files})")
            # Determine layout: either single XML or many per‑patent ZIPs
            xml_members = [m for m in members if m.name.lower().endswith('.xml')]
            # Per‑patent ZIPs (exclude supplemental and reissue categories)
            zip_members = [
                m for m in members
                if m.name.upper().endswith('.ZIP')
                and '-SUPP/' not in m.name.upper()
                and '/REISSUE/' not in m.name.upper()
            ]
            parser = make_parser()
            chunks = _ChunkCollector(collect=collect_chunks, batch_size=batch_size, on_batch=on_batch)
            last_doc_meta = None

            if xml_members and not zip_members:
                inner_xml = xml_members[0]
                print(f"[archive] inner XML: {inner_xml.name}")
                def _names():
                    return [m.name for m in members]
                def _open_bytes(name: str) -> bytes:
                    fobj = tf.extractfile(name)
                    if not fobj:
                        raise FileNotFoundError(name)
                    return fobj.read()
                with tf.extractfile(inner_xml) as xml_stream:
                    for i, blob in enumerate(iter_uspto_subdocs(xml_stream), start=1):
                        xml_blob = clamp_patent_doc(blob)
                        parser_strict  = make_parser()  # your existing (recover=False)
                        parser_recover = etree.XMLParser(resolve_entities=False, load_dtd=False,
                                         no_network=True, huge_tree=True, recover=True,
                                         remove_comments=True)
                        try:
                            root = etree.fromstring(xml_blob, parser=parser_strict)
                        except etree.XMLSyntaxError as e:
                            # Try again with recover=True to at least get structure
                            try:
                                root = etree.fromstring(xml_blob, parser=parser_recover)
                                print(f"[warn] subdoc {i} strict-parse failed but recovered: {e}")
                            except Exception:
                                # unrecoverable, skip this doc
                                save_failed(i, xml_blob, "xml_syntax_error", None)
                                print(f"[warn] subdoc {i} unrecoverable parse error: {e}")
                                continue
                        # Handle ST.26 sequence listings separately
                        if is_sequence_listing(root):
                            continue
                        counter = 0
                        authors = ""
                        doc_id = root.xpath("//publication-reference//document-id//doc-number//text()")
                        doc_id = doc_id[0] if doc_id else None
                        if doc_id and doc_id[:2] == "RE":
                            print(f'Skipping reissue patent {doc_id}')
                            continue
                        if not _register_doc_id(doc_id):
                            if stop_processing:
                                break
                            continue
                        app_number = extract_application_number(root, doc_id=doc_id)
                        kind_list = root.xpath("//publication-reference//document-id//kind//text()")
                        kind = kind_list[0].strip() if kind_list else None
                        doc_chunks: list[dict] | None = [] if sampler else None
                        try:
                            filing_date = root.xpath("//application-reference//document-id//date//text()")[0]
                        except IndexError:
                            outline(root, max_depth=4, max_children=20)
                            print(root.xpath("//publication-reference//document-id//date//text()"))
                            print(f'Doc ID that failed is {doc_id}')
                            input("Fake breakpoint")

                        classification = extract_primary_classification(root)
                        classification_cpc = extract_all_cpc_symbols(root)
                        title = extract_title(root)
                        first_names = root.xpath("//inventors//inventor//addressbook//first-name//text()")
                        last_names = root.xpath("//inventors//inventor//addressbook//last-name//text()")
                        for name in zip(first_names, last_names):
                            authors += " ".join(name) + "; "
                        authors = authors[:-2]
                        last_doc_meta = {
                            "authors": authors,
                            "classification": classification,
                            "classification_cpc": classification_cpc,
                            "filing_date": filing_date,
                            "doc_id": doc_id,
                            "application_number": app_number,
                            "kind": kind,
                            "title": title,
                        }
                        _maybe_validate_metadata(last_doc_meta, enable=meta_validate, verbose=verbose, collector=meta_mismatch_collector)
                        doc_buffer: list[dict] = []
                        def _record_chunk(payload: dict):
                            doc_buffer.append(payload)
                        for ordinal, claim in enumerate(root.xpath("//claims//claim"), start=1):
                            claim_text = elem_to_rich_text(claim).strip()
                            if not claim_text:
                                continue
                            claim_number = _extract_claim_number(claim, ordinal)
                            claim_type = _extract_claim_type(claim, claim_text)
                            claim_id = f"{doc_id}-CLM-{claim_number}"
                            _record_chunk({
                                           "section": "claim",
                                           "text": claim_text,
                                           "claim_id": claim_id,
                                           "claim_number": claim_number,
                                           "claim_type": claim_type,
                                           "filing_date": filing_date,
                                           "doc_id": doc_id,
                                           "kind": kind,
                                           "authors":authors,
                                           "classification": classification,
                                           "title": title,
                                           })
                            counter += 1
                        _, counter = _finalize_doc_chunks(chunks, doc_buffer, sample_enabled=False)
                        _log(f"[parse] doc {i}: {doc_id} (chunks: {counter})")
                # Emit per-patent Markdown files + CSV manifest (no text)
                try:
                    if sample_k and sample_k > 0:
                        target_dir = sample_out_dir or path
                        if use_manifest:
                            # Read existing manifest doc_ids and regenerate sample exactly
                            manifest_path = (target_dir / "sampled" / "sample_manifest.csv")
                            doc_ids: list[str] = []
                            if manifest_path.exists():
                                with manifest_path.open("r", encoding="utf-8") as f:
                                    reader = csv.DictReader(f)
                                    for row in reader:
                                        did = (row.get("doc_id") or "").strip()
                                        if did:
                                            doc_ids.append(did)
                            else:
                                print(f"[warn] manifest not found at {manifest_path}; falling back to random sampling")
                            if doc_ids:
                                write_patent_sample_by_ids(chunks, doc_ids=doc_ids, out_dir=target_dir, assets_by_doc=assets_by_doc)
                            else:
                                write_random_patent_sample(chunks, k=sample_k, out_dir=target_dir, seed=sample_seed, assets_by_doc=assets_by_doc)
                        else:
                            write_random_patent_sample(chunks, k=sample_k, out_dir=target_dir, seed=sample_seed, assets_by_doc=assets_by_doc)
                except Exception as e:
                    print(f"[warn] failed to write sample set: {e}")
                _flush_collector(chunks)
                print("[done] Completed processing all subdocuments (tar/xml).")
                _flush_meta_mismatches()
                if return_chunks:
                    return chunks
                return None

            if zip_members:
                print(f"[archive] Found {len(zip_members)} per‑patent ZIPs; beginning parse…")
                total_zips = len(zip_members)
                for j, m in enumerate(zip_members, start=1):
                    if stop_processing:
                        break
                    _print_progress("[parse] patents", j-1, total_zips)
                    try:
                        fobj = tf.extractfile(m)
                        if not fobj:
                            continue
                        data = fobj.read()
                        with ZipFile(io.BytesIO(data), 'r') as zf:
                            # Try to locate matching supplemental ZIP (same basename under IYYYYMMDD-SUPP)
                            base = m.name.split('/')[-1]
                            supp_member = next(
                                (sm for sm in members
                                 if sm.isfile()
                                 and sm.name.upper().endswith('/' + base.upper())
                                 and '-SUPP/' in sm.name.upper()),
                                None
                            )
                            zf_supp = None
                            supp_names = []
                            if supp_member is not None:
                                try:
                                    sdata = tf.extractfile(supp_member).read()
                                    zf_supp = ZipFile(io.BytesIO(sdata), 'r')
                                    supp_names = zf_supp.namelist()
                                    _log(f"[supp] Found supplemental ZIP for {base}: {supp_member.name}")
                                except Exception as e:
                                    _log(f"[supp] Failed to open supplemental ZIP for {base}: {e}")
                                    zf_supp = None
                                    supp_names = []

                            names = zf.namelist() + supp_names
                            xml_names = [n for n in names if n.lower().endswith('.xml')]
                            if not xml_names:
                                continue
                            inner_xml_name = xml_names[0]
                            with zf.open(inner_xml_name, 'r') as xml_stream:
                                for i, blob in enumerate(iter_uspto_subdocs(xml_stream), start=1):
                                    xml_blob = clamp_patent_doc(blob)
                                    parser_strict  = make_parser()
                                    parser_recover = etree.XMLParser(resolve_entities=False, load_dtd=False,
                                                     no_network=True, huge_tree=True, recover=True,
                                                     remove_comments=True)
                                    try:
                                        root = etree.fromstring(xml_blob, parser=parser_strict)
                                    except etree.XMLSyntaxError as e:
                                        try:
                                            root = etree.fromstring(xml_blob, parser=parser_recover)
                                            print(f"[warn] {m.name}: subdoc {i} recovered: {e}")
                                        except Exception:
                                            save_failed(i, xml_blob, "xml_syntax_error", None)
                                            print(f"[warn] {m.name}: subdoc {i} unrecoverable parse error: {e}")
                                            continue
                                    if is_sequence_listing(root):
                                        continue
                                    counter = 0
                                    authors = ""
                                    doc_id = root.xpath("//publication-reference//document-id//doc-number//text()")
                                    doc_id = doc_id[0] if doc_id else None
                                    if doc_id and doc_id[:2] == "RE":
                                        print(f'[skip] reissue patent {doc_id}')
                                        continue
                                    if not _register_doc_id(doc_id):
                                        if stop_processing:
                                            break
                                        continue
                                    app_number = extract_application_number(root, doc_id=doc_id)
                                    kind_list = root.xpath("//publication-reference//document-id//kind//text()")
                                    kind = kind_list[0].strip() if kind_list else None
                                    doc_chunks: list[dict] | None = [] if sample_enabled else None
                                    doc_buffer: list[dict] = []
                                    def _record_chunk(payload: dict):
                                        doc_buffer.append(payload)
                                    try:
                                        filing_date = root.xpath("//application-reference//document-id//date//text()")[0]
                                    except IndexError:
                                        outline(root, max_depth=4, max_children=20)
                                        continue
                                    classification = extract_primary_classification(root)
                                    classification_cpc = extract_all_cpc_symbols(root)
                                    title = extract_title(root)
                                    first_names = root.xpath("//inventors//inventor//addressbook//first-name//text()")
                                    last_names = root.xpath("//inventors//inventor//addressbook//last-name//text()")
                                    for name in zip(first_names, last_names):
                                        authors += " ".join(name) + "; "
                                    authors = authors[:-2]
                                    last_doc_meta = {
                                        "authors": authors,
                                        "classification": classification,
                                        "classification_cpc": classification_cpc,
                                        "filing_date": filing_date,
                                        "doc_id": doc_id,
                                        "application_number": app_number,
                                        "kind": kind,
                                        "title": title,
                                    }
                                    _maybe_validate_metadata(last_doc_meta, enable=meta_validate, verbose=verbose, collector=meta_mismatch_collector)
                                    if doc_chunks is None:
                                        doc_chunks = [] if sample_enabled else None
                                    for ordinal, claim in enumerate(root.xpath("//claims//claim"), start=1):
                                        claim_text = elem_to_rich_text(claim).strip()
                                        if not claim_text:
                                            continue
                                        claim_number = _extract_claim_number(claim, ordinal)
                                        claim_type = _extract_claim_type(claim, claim_text)
                                        claim_id = f"{doc_id}-CLM-{claim_number}"
                                        _record_chunk({"section": "claim",
                                                       "text": claim_text,
                                                       "claim_id": claim_id,
                                                       "claim_number": claim_number,
                                                       "claim_type": claim_type,
                                                       "filing_date": filing_date,
                                                       "doc_id": doc_id,
                                                       "kind": kind,
                                                       "authors":authors,
                                                       "classification": classification,
                                                       "title": title,
                                                       })
                                        counter += 1

                                    doc_chunks, counter = _finalize_doc_chunks(chunks, doc_buffer, sample_enabled=sample_enabled)
                                    _log(f"[parse] {m.name}: {doc_id} (chunks: {counter})")
                                    if sample_enabled and doc_id and assets_by_doc is not None:
                                        try:
                                            def _z_open_bytes(name: str) -> bytes:
                                                try:
                                                    with zf.open(name, 'r') as ff:
                                                        return ff.read()
                                                except Exception:
                                                    if zf_supp is not None:
                                                        with zf_supp.open(name, 'r') as ff:
                                                            return ff.read()
                                                    raise
                                            doc_assets = _collect_figure_assets(root, names, _z_open_bytes)
                                        except Exception:
                                            doc_assets = {"images": []}
                                        assets_by_doc[doc_id] = doc_assets
                                        if doc_chunks:
                                            _attach_fig_images_to_chunks(doc_chunks, doc_assets)
                                            _append_figures_chunk(
                                                chunks,
                                                doc_chunks,
                                                doc_assets,
                                                {
                                                    "filing_date": filing_date,
                                                    "doc_id": doc_id,
                                                    "kind": kind,
                                                    "authors": authors,
                                                    "classification": classification,
                                                    "title": title,
                                                },
                                            )
                                        try:
                                            img_n = len(doc_assets.get("images", []))
                                            if img_n:
                                                _log(f"[assets] doc {doc_id}: {img_n} image(s) found")
                                        except Exception:
                                            pass
                        if stop_processing:
                            break
                    except Exception as e:
                        print(f"[warn] failed reading inner zip {m.name}: {e}")
                        continue
                _print_progress("[parse] patents", total_zips, total_zips)

                # Emit per‑patent samples
                try:
                    if sample_k and sample_k > 0:
                        target_dir = sample_out_dir or path
                        if use_manifest:
                            manifest_path = (target_dir / "sampled" / "sample_manifest.csv")
                            doc_ids: list[str] = []
                            if manifest_path.exists():
                                with manifest_path.open("r", encoding="utf-8") as f:
                                    reader = csv.DictReader(f)
                                    for row in reader:
                                        did = (row.get("doc_id") or "").strip()
                                        if did:
                                            doc_ids.append(did)
                            else:
                                print(f"[warn] manifest not found at {manifest_path}; falling back to random sampling")
                            if doc_ids:
                                write_patent_sample_by_ids(chunks, doc_ids=doc_ids, out_dir=target_dir, assets_by_doc=assets_by_doc)
                            else:
                                write_random_patent_sample(chunks, k=sample_k, out_dir=target_dir, seed=sample_seed, assets_by_doc=assets_by_doc)
                        else:
                            write_random_patent_sample(chunks, k=sample_k, out_dir=target_dir, seed=sample_seed, assets_by_doc=assets_by_doc)
                except Exception as e:
                    print(f"[warn] failed to write sample set: {e}")
                _flush_collector(chunks)
                print("[done] Completed processing all subdocuments (tar/zips).")
                _flush_meta_mismatches()
                if return_chunks:
                    return chunks
                return None

            # Neither layout was detected
            raise FileNotFoundError("No XML or inner ZIP files found inside TAR")
    else:
        with ZipFile(file_path, mode='r') as Myzip:
            members = [n for n in Myzip.namelist() if n.lower().endswith(".xml")]
            if not members:
                raise FileNotFoundError("No .xml found inside ZIP")
            inner_xml_name = members[0]  # often there’s exactly one
            parser = make_parser()
            print(f"[archive] ZIP opened: {file_path}; inner XML: {inner_xml_name}")
            chunks = _ChunkCollector(collect=collect_chunks, batch_size=batch_size, on_batch=on_batch)
            last_doc_meta = None
            # Best-effort doc count for progress (may be expensive); skip for very large files
            total_docs: int | None = None
            try:
                size = file_path.stat().st_size
                if size <= 200_000_000:  # only count when zip is small enough
                    total_docs = count_docs_in_zip(file_path)
            except Exception:
                total_docs = None
            def _names():
                return Myzip.namelist()
            def _open_bytes(name: str) -> bytes:
                with Myzip.open(name, 'r') as f:
                    return f.read()
            with Myzip.open(inner_xml_name, "r") as xml_stream:
                for i, blob in enumerate(iter_uspto_subdocs(xml_stream), start=1):
                    xml_blob = clamp_patent_doc(blob)
                    # Progress update
                    if i == 1 or (i % 25 == 0):
                        _print_progress("[parse] docs", i-1, total_docs)
                    parser_strict  = make_parser()  # your existing (recover=False)
                    parser_recover = etree.XMLParser(resolve_entities=False, load_dtd=False,
                                     no_network=True, huge_tree=True, recover=True,
                                     remove_comments=True)
                    try:
                        root = etree.fromstring(xml_blob, parser=parser_strict)

                    except etree.XMLSyntaxError as e:
                        # Try again with recover=True to at least get structure
                        try:
                            root = etree.fromstring(xml_blob, parser=parser_recover)
                            _log(f"[warn] subdoc {i} strict-parse failed but recovered: {e}")
                        except Exception:
                            # unrecoverable, skip this doc
                            save_failed(i, xml_blob, "xml_syntax_error", None)
                            print(f"[warn] subdoc {i} unrecoverable parse error: {e}")
                            continue
                    # Handle ST.26 sequence listings separately
                    if is_sequence_listing(root):
                        continue
                    counter = 0
                    authors = ""
                    doc_id = root.xpath("//publication-reference//document-id//doc-number//text()")
                    doc_id = doc_id[0] if doc_id else None
                    if doc_id and doc_id[:2] == "RE":
                        print(f'Skipping reissue patent {doc_id}')
                        continue
                    if not _register_doc_id(doc_id):
                        if stop_processing:
                            break
                        continue
                    app_number = extract_application_number(root, doc_id=doc_id)
                    kind_list = root.xpath("//publication-reference//document-id//kind//text()")
                    kind = kind_list[0].strip() if kind_list else None
                    try:
                        filing_date = root.xpath("//application-reference//document-id//date//text()")[0]
                    except IndexError:
                        #outline(root, max_depth=4, max_children=20)
                        outline(root, max_depth=4, max_children=20)
                        print(root.xpath("//publication-reference//document-id//date//text()"))
                        print(f'Doc ID that failed is {doc_id}')
                        input("Fake breakpoint")
                        continue
                    
                    classification = extract_primary_classification(root)
                    classification_cpc = extract_all_cpc_symbols(root)
                    # Patent title (robust to namespaces)
                    title = extract_title(root)
                    first_names = root.xpath("//inventors//inventor//addressbook//first-name//text()")
                    last_names = root.xpath("//inventors//inventor//addressbook//last-name//text()")
                    for name in zip(first_names, last_names):
                        authors += " ".join(name) + "; "
                    authors = authors[:-2]
                    # Remember metadata for sequence listings that follow
                    last_doc_meta = {
                        "authors": authors,
                        "classification": classification,
                        "classification_cpc": classification_cpc,
                        "filing_date": filing_date,
                        "doc_id": doc_id,
                        "application_number": app_number,
                        "kind": kind,
                        "title": title,
                    }
                    _maybe_validate_metadata(last_doc_meta, enable=meta_validate, verbose=verbose, collector=meta_mismatch_collector)
                    doc_buffer: list[dict] = []
                    def _record_chunk(payload: dict):
                        doc_buffer.append(payload)
                    for ordinal, claim in enumerate(root.xpath("//claims//claim"), start=1):
                        claim_text = elem_to_rich_text(claim).strip()
                        if not claim_text:
                            continue
                        claim_number = _extract_claim_number(claim, ordinal)
                        claim_type = _extract_claim_type(claim, claim_text)
                        claim_id = f"{doc_id}-CLM-{claim_number}"
                        _record_chunk({"section": "claim",
                                       "text": claim_text,
                                       "claim_id": claim_id,
                                       "claim_number": claim_number,
                                       "claim_type": claim_type,
                                       "filing_date": filing_date,
                                       "doc_id": doc_id,
                                       "kind": kind,
                                       "authors":authors,
                                       "classification": classification,
                                       "title": title,
                                       })
                        counter += 1
                    doc_chunks, counter = _finalize_doc_chunks(chunks, doc_buffer, sample_enabled=sample_enabled)
                    #temp_dict = {"doc_id": "", "section": "claim", "authors": "bleb bleb bleb"}
                    #temp_list=[doc_id, section, authors, text, ] 
                    #big_list.append(temp_list)
                    print(f"[parse] doc {i}: {doc_id} (chunks: {counter})")
                    # Collect figure assets for this document (if images present)
                    if sample_enabled and doc_id and assets_by_doc is not None:
                        try:
                            doc_assets = _collect_figure_assets(root, _names(), _open_bytes)
                        except Exception:
                            doc_assets = {"images": []}
                        assets_by_doc[doc_id] = doc_assets
                        if doc_chunks:
                            _attach_fig_images_to_chunks(doc_chunks, doc_assets)
                            _append_figures_chunk(
                                chunks,
                                doc_chunks,
                                doc_assets,
                                {
                                    "filing_date": filing_date,
                                    "doc_id": doc_id,
                                    "kind": kind,
                                    "authors": authors,
                                    "classification": classification,
                                    "title": title,
                                },
                            )
                        try:
                            img_n = len(doc_assets.get("images", []))
                            if img_n:
                                print(f"[assets] doc {doc_id}: {img_n} image(s) found")
                        except Exception:
                            pass
            # Emit per-patent Markdown files + CSV manifest (no text)
            try:
                if sample_k and sample_k > 0:
                    target_dir = sample_out_dir or path
                    if use_manifest:
                        # Read existing manifest doc_ids and regenerate sample exactly
                        manifest_path = (target_dir / "sampled" / "sample_manifest.csv")
                        doc_ids: list[str] = []
                        if manifest_path.exists():
                            with manifest_path.open("r", encoding="utf-8") as f:
                                reader = csv.DictReader(f)
                                for row in reader:
                                    did = (row.get("doc_id") or "").strip()
                                    if did:
                                        doc_ids.append(did)
                        else:
                            print(f"[warn] manifest not found at {manifest_path}; falling back to random sampling")
                        if doc_ids:
                            write_patent_sample_by_ids(chunks, doc_ids=doc_ids, out_dir=target_dir, assets_by_doc=assets_by_doc)
                        else:
                            write_random_patent_sample(chunks, k=sample_k, out_dir=target_dir, seed=sample_seed, assets_by_doc=assets_by_doc)
                    else:
                        write_random_patent_sample(chunks, k=sample_k, out_dir=target_dir, seed=sample_seed, assets_by_doc=assets_by_doc)
            except Exception as e:
                print(f"[warn] failed to write sample set: {e}")
            # Finalize progress line
            if total_docs:
                _print_progress("[parse] docs", total_docs, total_docs)
            else:
                sys.stdout.write("\n")
            _flush_collector(chunks)
            print("[done] Completed processing all subdocuments (zip).")
            _flush_meta_mismatches()
            if return_chunks:
                return chunks
            return None
                    
                # Inspect structure of the first subdoc, then stop
                #print(chunks)
                # Stop after first while exploring; remove when ready to process all

if __name__ == "__main__":
    #dict = fetch_metadata(app_no = '18770008')
    #print(dict)
    #sys.exit('early stop')
    path_stub = Path("C:\\Patent_Wizard\\validation")
    report_hash_consistency(csv_path=path_stub / Path("determinism_hashes.csv"))
    report_hash_consistency(csv_path=path_stub / Path("determinism_hashes2.csv"))
    report_hash_consistency(csv_path=path_stub / Path("determinism_hashes3.csv"))
    report_hash_consistency(csv_path=path_stub / Path("determinism_hashes4.csv"))
    report_hash_consistency(csv_path=path_stub / Path("determinism_hashes5.csv"))

#validate_batch_determinism("2025-04-01", runs=5, batch_size=500, csv_path=Path("determinism_hashes6.csv"), delete_between_runs=True)
#report_hash_consistency(csv_path=Path("determinism_hashes6.csv"))
#for chunk in these_chunks:
#    plain = rich_to_plain(chunk.get("chunk", ""))
#    print(f"{chunk.get('doc_id')} | {chunk.get('section')} | {chunk.get('filing_date')} | {chunk.get('classification')} | {chunk.get('authors')}\n{plain}\n")
#TODO: weave in SQlite database to store metadata as well as application numbers and text for lexical search
            

#Helpers: Move to helper file later


UNUSED_HELPERS_DOC = '''
Unused helper definitions kept for reference only. Re-enable them if needed.

def count_docs_for_date(input_date: str | datetime, path: Path = Path('.')) -> int:
    """Convenience: build the expected weekly file path and count docs.

    Does not download the file; use bulk_dataset_download first to fetch.
    """
    start_date = datetime.strptime(input_date, "%Y-%m-%d") if isinstance(input_date, str) else input_date
    days_since_tuesday = (start_date.weekday() - 1)
    last_tuesday = start_date - timedelta(days=days_since_tuesday)
    file_name = f"ipg{last_tuesday:%y}{last_tuesday:%m}{last_tuesday:%d}"
    file_path = path / f"{file_name}.zip"
    return count_docs_in_zip(file_path)


def sanitize_app_no(s: str | None) -> str | None:
    if not s:
        return None
    return re.sub(r"[^0-9A-Za-z]", "", s)


def find_keys(obj, keywords):
    kws = [k.lower() for k in keywords]
    for p, v in jpaths(obj):
        last = p.split(".")[-1].lower()
        if any(kw in last for kw in kws):
            print(f"{p}: {v}")
'''



'''
# --- Main loop to page through API results ---
for offset in range(0, MAX_RANGE, LIMIT):  # Iterate through offsets 0, 100, 200, ... up to 9900
    application_numbers, error_response = make_search_request(offset, 0)  # Fetch one page
    time.sleep(SLEEP_BETWEEN_HTTP)  # Optional pause between requests

    if application_numbers is not None:  # If data retrieved successfully
        application_numbers_api.extend(application_numbers)  # Add to master list
        print(f'Application Number {application_numbers}')   # Print each batch
    else:
        # Print error details if request failed
        print(f"request failed with status code {error_response.status_code} for offset: {offset}")
        print(f"response content: {error_response.content}")
        print(f"url causing the error: {url}")
'''
