from typing import Any, Dict, Optional, List
import os
import glob
import saby_vector_store as vector_store
from saby_classes import Patent_Miner_State

def build_docid_to_path_map(base_dir: str) -> Dict[str, str]:
    """
    Map doc_id -> file path by scanning the directory.
    Matches how ingestion derives doc_id from filenames: split on '' and take the 3rd part if present,
    otherwise use the filename stem 
    vector_store.py
    .
    """
    mapping: Dict[str, str] = {}
    for fname in os.listdir(base_dir):
        if not fname.lower().endswith((".md", ".txt", ".html", ".pdf")):
            continue
        stem = os.path.splitext(fname)[0]
        parts = stem.split("_")
        # Follow vector_store.load_markdown_files logic 

        doc_id = parts[2] if len(parts) >= 3 else stem
        # First match wins; adjust if you expect duplicates
        mapping.setdefault(doc_id, os.path.join(base_dir, fname))
    return mapping

def patent_fetch(state: Patent_Miner_State, base_dir: Optional[str] = None):
    """
    For each retrieved unique chunk, load the corresponding full patent file from disk by doc_id 

    Returns:
    - full_patent_texts: {doc_id -> full_text}
    - patent_paths: {doc_id -> absolute_path}
    """
    retrieved = state.get("retrieved_context") or []
    if not retrieved:
        return {}

    base_dir = base_dir or getattr(vector_store, "MD_DIR", "patents/markdown")
    docid_to_path = build_docid_to_path_map(base_dir)

    full_texts: Dict[str, str] = {}

    for item in retrieved:
        meta = item.get("metadata", {}) or {}
        doc_id = str(meta.get("doc_id") or meta.get("index") or "").strip()
        if not doc_id:
            continue

        # Resolve path
        path = docid_to_path.get(doc_id)
        if not path:
        # Fallback: any filename containing the doc_id as a substring
            candidates = sorted(glob.glob(os.path.join(base_dir, f"*{doc_id}*.*")))
            path = candidates[0] if candidates else None
        if not path or not os.path.exists(path):
            continue
        
        ext = os.path.splitext(path)[-1]
        #try:
        if ext in (".md", ".txt", ".html"):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

        if content:
            full_texts[doc_id] = content

    retrieved_patents: List[Dict[str, Any]] = [{"text": full_texts[c]} for c in full_texts]

    joined_patents = "\n\nNext Patent\n\n".join([full_texts[c] for c in full_texts])
    del full_texts
    
    # Attach to state; you can decide how rusty_answer uses these (e.g., include links or run a secondary selector)
    return {"joined_patents": joined_patents, "retrieved_patents": retrieved_patents}