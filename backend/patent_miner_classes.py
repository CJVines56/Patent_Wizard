from typing import Optional, TypedDict, Any, Dict, List
from pydantic import BaseModel, Field


## Query Classes ##

# Query Cleaning Schema #
class CleanedQuery(BaseModel):
    cleaned_query: str = Field(..., description="A single concise rewritten search query.")

## Metadata Classes ##

# Metadata schema #
class QueryMetadata(BaseModel):
    author_name: Optional[str] = Field(
        default=None,
        description="Name of the author or inventor if mentioned or implied."
    )
    filing_date: Optional[str] = Field(
        default=None,
        description=(
            "Either an exact date in YYYY-MM-DD or a natural-language constraint "
            "like 'after 2020', 'before 2021-05-01', "
            "'between 2019-01-01 and 2020-12-31'."
        )
    )
    title: Optional[str] = Field(
        default=None,
        description="The title or main topic/subject of the requested document(s)."
    )
    document_id: Optional[str] = Field(
        default=None,
        description="The unique document or patent identifier, if mentioned or implied."
    )


# Metadata state # 
class metadatastate(TypedDict):
        metadata: Optional[QueryMetadata] = None
        chroma_filter: Optional[Dict[str, Any]] = None

        cleaned_query: Optional[str] = None
        contexts: Optional[List[Dict[str, Any]]] = None
        joined_context: Optional[str] = None
        answer: Optional[str] = None