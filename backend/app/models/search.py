from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SearchItem(BaseModel):
    id: int
    title: str
    snippet: str
    search_text: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    search_scope: str = "claim"
    total: int
    page: int
    page_size: int
    items: List[Dict[str, Any]]
    cited_items: List[Dict[str, Any]]
    other_items: List[Dict[str, Any]]
    mode: str
    answer: Optional[str] = None
