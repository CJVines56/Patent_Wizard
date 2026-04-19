import os
from dotenv import load_dotenv
from typing import Optional, Any, Dict, List
import re
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from langgraph.graph import MessagesState, StateGraph, END
from backend.orchestrator.patent_miner_classes import QueryMetadata, metadatastate

_ORCH_DIR = Path(__file__).resolve().parent
load_dotenv(_ORCH_DIR / ".env")
load_dotenv(_ORCH_DIR / "env")

nodes2_model = ChatOpenAI(
    model="protected.gemini-2.5-flash",
    temperature=0.2,
)


## Query Metadata Extraction Node ##

# LLM Setup #

structured_llm = nodes2_model.with_structured_output(QueryMetadata)

metadata_extract_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an assistant that extracts metadata constraints from user queries "
        "for a document retrieval system. "
        "Map natural language to the following fields where possible: "
        "author_name, filing_date, title, document_id. "
        "If a field is not mentioned, leave it null. "
        "You may infer reasonable values from context, but do not hallucinate "
        "specific IDs, names, or dates that are not implied by the query."
    ),
    ("user", "{query}")
])

def llm_extract_metadata_structured(user_query: str) -> QueryMetadata:
    messages = metadata_extract_prompt.format_messages(query=user_query)
    metadata_obj: QueryMetadata = structured_llm.invoke(messages)
    return metadata_obj

# Metadata Filtering setup #

def build_advanced_chroma_filter(metadata: QueryMetadata) -> Dict[str, Any]:
    """
    Build a ChromaDB filter dict using:
    - regex for partial/case-insensitive author and doc_id
    - $contains for title substring
    - range/exact handling for filing_date
    """
    filters = []

    # Author: regex, case-insensitive
    if metadata.author_name:
        filters.append({
            "authors": {
                "$regex": metadata.author_name,
                "$options": "i"
            }
        })

    # Title: substring / inclusion
    if metadata.title:
        filters.append({
            "title": {
                "$contains": metadata.title
            }
        })

    # Document ID: regex to allow flexible match
    if metadata.document_id:
        filters.append({
            "doc_id": {
                "$regex": metadata.document_id,
                "$options": "i"
            }
        })

    # Filing date: natural language → exact or range
    if metadata.filing_date:
        fd = metadata.filing_date.strip()

        after_match = re.match(r"after\s+(\d{4}(?:-\d{2}-\d{2})?)", fd, re.IGNORECASE)
        before_match = re.match(r"before\s+(\d{4}(?:-\d{2}-\d{2})?)", fd, re.IGNORECASE)
        between_match = re.match(
            r"between\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})",
            fd,
            re.IGNORECASE
        )
        exact_match = re.match(r"^\d{4}-\d{2}-\d{2}$", fd)

        if between_match:
            start_date, end_date = between_match.groups()
            filters.append({
                "filing_date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })
        elif after_match:
            date_str = after_match.group(1)
            if re.match(r"^\d{4}$", date_str):
                date_str = f"{date_str}-01-01"
            filters.append({
                "filing_date": {
                    "$gt": date_str
                }
            })
        elif before_match:
            date_str = before_match.group(1)
            if re.match(r"^\d{4}$", date_str):
                date_str = f"{date_str}-12-31"
            filters.append({
                "filing_date": {
                    "$lt": date_str
                }
            })
        elif exact_match:
            filters.append({
                "filing_date": fd
            })

    if not filters:
        return {}
    if len(filters) == 1:
        return filters[0]
    return {"$and": filters}


def metadata_filter_node(state: MessagesState) -> metadatastate:
    # 1. Extract metadata

    question = state["messages"][0].content
    metadata = llm_extract_metadata_structured(question)
    where_filter = build_advanced_chroma_filter(metadata)

    return {"metadata": metadata, "chroma_filter": where_filter}

