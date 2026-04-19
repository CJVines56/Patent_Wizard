from typing import List, Dict, Any

def make_fake_answer(query: str, contexts: List[Dict[str, Any]], k: int) -> str:
    """
    Produce a deterministic answer string with bracket citations [1], [2], ...
    This is a stand-in for a real RAG pipeline (cleaning, retrieval, rerank, LLM).
    """
    if not contexts:
        return f"(FAKE RAG) No supporting contexts found for: '{query}'."

    # Use at least 5 contexts when available (ensure richer answers)
    eff_k = max(k, 5)
    top_k = contexts[:eff_k]
    # Assemble a compact inline reference list like: [1], [2]
    cites = ", ".join(f"[{i}]" for i in range(1, len(top_k) + 1))

    # Build a readable bullet list enumerating each cited document
    bullet_lines = []
    for i, c in enumerate(top_k, start=1):
        title = c.get("title", "")
        snippet = c.get("snippet", "")
        bullet_lines.append(f"[{i}] {title}: {snippet}")

    bullets = "\n".join(bullet_lines)
    # Return a multi-paragraph answer that mentions the citations and lists them
    return (
        f"(FAKE RAG) Proposed answer for: '{query}'. See {cites} for sources.\n\n"
        f"Based on the following {len(top_k)} contexts:\n{bullets}\n\n"
    )
