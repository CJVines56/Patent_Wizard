import os
import json
from typing import Any, Dict, Optional
from pathlib import Path
from backend.orchestrator.patent_miner_classes import metadatastate
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from backend.orchestrator.patent_miner_classes import CleanedQuery
from backend.orchestrator.tools import retriever_tool
from dotenv import load_dotenv

_ORCH_DIR = Path(__file__).resolve().parent
load_dotenv(_ORCH_DIR / ".env")
load_dotenv(_ORCH_DIR / "env")


nodes_model = ChatOpenAI(
    model="protected.gemini-2.5-flash",
    temperature=0.2,
)

clean_structured_llm = nodes_model.with_structured_output(CleanedQuery)

## Query Cleaning Node ##


clean_prompt = (
    "Rewrite the user's question into ONE concise search query. "
    "Return only the cleaned query."
)


def query_clean(state: MessagesState):
    """Clean the original user question."""
    messages = state["messages"]
    question = messages[0].content
    prompt = clean_prompt.format(question=question)
    
    obj: CleanedQuery = clean_structured_llm.invoke(
        [{"role": "system", "content": prompt},
         {"role": "user", "content": question}]
    )

    cleaned = obj.cleaned_query.strip()
    return {"messages": [{"role": "user", "content": cleaned}],
            "cleaned_query": cleaned}

## Query Routing Node ##

def query_route(state: MessagesState):   ## When finalized -> route this part to metadata extraction, then response generation
    
    """Call the model to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool, or simply respond to the user.
    If the model invokes the retriever tool, it also receives the respective metadata filter for the query."
    """

    where_filter = state.get("chroma_filter")  # set by metadata_filter_node

    sys = (
        "If you call the retrieval tool, you MUST pass:\n"
        f'- query: the user question\n- where_filter: {where_filter}\n'
        "If where_filter is null/empty, omit it."
    )

    response = (
        nodes_model
        .bind_tools([retriever_tool]).invoke([{"role": "system", "content": sys}] + state["messages"])
    )

    return {"messages": [response]}


## Context and cleaned query Storage Node ##

TOOL_NAME = "retrieve_context"  # matches tools.py

def store_contexts(state: MessagesState)-> metadatastate:
    for m in reversed(state["messages"]):
        if getattr(m, "type", None) == "tool" and getattr(m, "name", None) == TOOL_NAME:
            tool_msg = m
            break
    
    if tool_msg is None:
        return {
            "cleaned_query": state["messages"][1].content,
            "contexts": [],
            "joined_context": "",
        }
    tool_content = tool_msg.content

    
    if isinstance(tool_content, dict):
        payload = tool_content
    else:
        payload = json.loads(tool_content)  # your tool returns JSON string content

    return {
        "cleaned_query": state["messages"][1].content,
        "contexts": payload.get("chunks", []) or [],
        "joined_context": payload.get("joined_text", "") or "",
    }

## Response Generation Node ##

generate_prompt = (
    "You are a patent litigation assistant. \n"
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know the answer, just say that you don't know. "
    "If no context is provided. Use your own knowledge to answer the question."
    "Use three sentences maximum and keep the answer concise.\n"
    "Question: {question} \n"
    "Context: {context}"
)

def generate_answer(state: metadatastate)-> metadatastate:
    """Generate an answer."""
    def _message_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            parts = [_message_text(v) for v in value]
            return "\n".join(p for p in parts if p.strip())
        if isinstance(value, dict):
            for key in ("text", "content", "answer", "output_text"):
                text = value.get(key)
                if isinstance(text, str) and text.strip():
                    return text
            return str(value)
        return str(value)

    question = str(state.get("cleaned_query") or "").strip()
    context = str(state.get("joined_context") or "").strip()

    # If query_route already produced a direct assistant answer (no retrieval/tool),
    # prefer returning that message instead of re-invoking the model.
    if not context:
        messages = state.get("messages") or []
        for msg in reversed(messages):
            role = str(getattr(msg, "type", "") or getattr(msg, "role", "") or "").lower()
            if role in {"ai", "assistant"}:
                direct = _message_text(getattr(msg, "content", None)).strip()
                if direct:
                    return {"answer": [direct]}

    prompt = generate_prompt.format(question=question, context=context)
    response = nodes_model.invoke([{"role": "user", "content": prompt}])
    return {"answer": [response.content]}
