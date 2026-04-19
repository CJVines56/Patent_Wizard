from typing import List
from ..db.dataset import CATALOG
from ..models.search import SearchItem

def _token_in(text: str, q: str) -> bool:
    return q.lower() in text.lower()

def naive_filter(q: str) -> List[SearchItem]:
    """
    Very simple filter that preserves catalog order.
    No scoring/reranking here.
    """
    if not q:
        hits = CATALOG
    else:
        hits = []
        ql = q.lower()
        for row in CATALOG:
            title = row.get("title", "")
            snippet = row.get("snippet", "")
            search_text = row.get("search_text", "")  # aggregated plain text if available
            if (
                ql in title.lower()
                or ql in snippet.lower()
                or (search_text and ql in search_text.lower())
            ):
                hits.append(row)
    return [SearchItem(**row) for row in hits]

def first_k(items: List[SearchItem], k: int) -> List[SearchItem]:
    """Top-k by original order only."""
    return items[:k]
