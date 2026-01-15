"""
Quick script to build realistic fake patent data, embed it, print vector previews,
and store to local Weaviate. Also includes an optional reset helper.
"""

from embed import embed_chunks, tokenizer, model
from store import store_embeddings


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

    run_fake_ingest()
