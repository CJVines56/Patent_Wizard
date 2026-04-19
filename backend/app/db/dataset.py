from typing import List, Dict, Any
from pathlib import Path
import json

# Optional: plain-text conversion mirroring services.download.rich_to_plain
import re
def _rich_to_plain(rich: str) -> str:
    if not rich:
        return ""
    s = re.sub(r"<br\s*/?>", "\n", rich, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    return s.strip()


SAMPLED_CHUNKS_PATH = Path(__file__).resolve().parent / "sample_chunks.jsonl"

# Loaded chunk objects grouped by doc_id for potential future use
CHUNKS_BY_DOC: Dict[str, List[Dict[str, Any]]] = {}

# In-memory demo "documents" built from sampled chunks (fallback to static if missing).
CATALOG: List[Dict[str, Any]] = []


def _load_sampled_chunks() -> Dict[str, List[Dict[str, Any]]]:
    by_doc: Dict[str, List[Dict[str, Any]]] = {}
    if not SAMPLED_CHUNKS_PATH.exists():
        return by_doc
    with SAMPLED_CHUNKS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            did = obj.get("doc_id")
            if not did:
                continue
            by_doc.setdefault(did, []).append(obj)
    return by_doc


def _build_catalog_from_chunks(by_doc: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if not by_doc:
        return items
    for idx, (did, chunks) in enumerate(by_doc.items(), start=1):
        # Prefer abstract as snippet, else description, else claim
        title = None
        snippet = ""
        filing_date = None
        classification = None
        authors = None
        kind = None
        # Pull title from any chunk that has it
        for ch in chunks:
            if ch.get("title"):
                title = ch["title"]
                break
        if not title:
            title = f"Doc {did}"
        # Slurp common metadata from any chunk
        fig_images: List[Dict[str, Any]] = []
        seen_fig_keys: set[str] = set()
        for ch in chunks:
            if not filing_date and ch.get("filing_date"):
                filing_date = ch.get("filing_date")
            if not classification and ch.get("classification"):
                classification = ch.get("classification")
            if not authors and ch.get("authors"):
                authors = ch.get("authors")
            if not kind and ch.get("kind"):
                kind = ch.get("kind")
            imgs = ch.get("fig_images") or []
            if imgs:
                for img in imgs:
                    data_b64 = img.get("data_b64")
                    if not data_b64:
                        continue
                    cache_key = f"{img.get('file') or ''}:{data_b64[:16]}"
                    if cache_key in seen_fig_keys:
                        continue
                    seen_fig_keys.add(cache_key)
                    fig_images.append({
                        "file": img.get("file"),
                        "media_type": img.get("media_type"),
                        "fig_ids": img.get("fig_ids"),
                        "num": img.get("num"),
                        "data_b64": data_b64,
                    })
                    if len(fig_images) >= 6:
                        break
        # no early break; we scan all chunks to gather figure previews

        # Snippet from the first abstract chunk (plain text)
        abs_chunk = next((c for c in chunks if c.get("section") == "abstract"), None)
        if abs_chunk:
            snippet = _rich_to_plain(abs_chunk.get("chunk", ""))
        else:
            desc_chunk = next((c for c in chunks if c.get("section") == "description"), None)
            if desc_chunk:
                snippet = _rich_to_plain(desc_chunk.get("chunk", ""))
            else:
                claim_chunk = next((c for c in chunks if c.get("section") == "claim"), None)
                if claim_chunk:
                    snippet = _rich_to_plain(claim_chunk.get("chunk", ""))
        # Trim snippet for UI
        if len(snippet) > 240:
            snippet = snippet[:237] + "..."
        # Aggregate full plain-text for simple substring search
        search_text = " ".join(
            _rich_to_plain(c.get("chunk", "")) for c in chunks if c.get("chunk")
        )
        items.append({
            "id": idx,
            "title": title,
            "snippet": snippet,
            "doc_id": did,
            "search_text": search_text,
            "filing_date": filing_date,
            "classification": classification,
            "authors": authors,
            "kind": kind,
            "fig_images": fig_images,
        })
    return items


# Initialize data
CHUNKS_BY_DOC = _load_sampled_chunks()
if CHUNKS_BY_DOC:
    CATALOG = _build_catalog_from_chunks(CHUNKS_BY_DOC)
else:
    # Fallback static demo set if no sampled chunks available yet
    CATALOG = [
        {"id": 1, "title": "Electric Power Systems", "snippet": "Power flow, stability, protection."},
        {"id": 2, "title": "Signals and Systems", "snippet": "Fourier, Laplace, and sampling theory."},
        {"id": 3, "title": "Digital Control", "snippet": "Discrete-time control and DSP."},
        {"id": 4, "title": "Embedded C Programming", "snippet": "Peripherals, interrupts, and memory-mapped I/O."},
        {"id": 5, "title": "High Voltage Engineering", "snippet": "Insulation, breakdown, and testing."},
        {"id": 6, "title": "Power Electronics", "snippet": "Converters, PWM, and switching devices."},
        {"id": 7, "title": "Numerical Methods in Engineering", "snippet": "Error analysis, interpolation, integration."},
        {"id": 8, "title": "Electromagnetics", "snippet": "Fields, waves, transmission lines."},
        {"id": 9, "title": "Machine Learning Basics", "snippet": "Supervised and unsupervised methods."},
        {"id": 10, "title": "Data Structures in Python", "snippet": "Lists, dicts, sets, and algorithms."},
    ]
