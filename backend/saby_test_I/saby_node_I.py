import sys
import os
import json
from typing import Any, Dict, Optional, List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from saby_classes import retrievalstate, Patent_Miner_State

from saby_vector_store import vector_storage


load_dotenv()

# N_MEMORY = 10

nodes_model = ChatOpenAI(
    model="protected.gpt-5",
    temperature=0.2,
)

clean_prompt = (
    "You are a patent search and retrieval assistant.\n"
    "Given a user question, detect and correct grammatical errors and misspellings.\n"
    "If the question contains ambiguous or vague words/phrases, rewrite it concisely while preserving meaning.\n"
    "If the question contains no errors or ambiguity, do not rewrite it.\n"
    "Return ONLY the cleaned question text.\n"
    "Here is the user question: {question}"
)


def query_clean(state: Patent_Miner_State):
    """
    Clean the latest user question.
    IMPORTANT: Do not overwrite `messages` (we keep it as chat history).
    """
    messages = list(state.get("messages") or [])
    if not messages:
        return {}

    last = messages[-1]
    question = getattr(last, "content", None) or last.get("content", "")

    prompt = clean_prompt.format(question=question)
    cleaned_query = nodes_model.invoke([{"role": "user", "content": prompt}]).content.strip()

    # Replace only the last message content (keep history)
    state["messages"][-1].content = cleaned_query

    return {"question": cleaned_query}


def query_route(state: Patent_Miner_State) -> retrievalstate:
    user_text = state["messages"][-1].content

    prompt = (
        "You are a router for a Patent search and retrieval RAG system.\n"
        f"Given the question:\n{user_text}\n\n"
        "Decide if answering the user requires retrieving context from the RAG patent database.\n\n"
        "Return ONLY valid JSON with exactly this schema:\n"
        '{"needs_retrieval": true|false}\n'
        "Rules:\n"
        "- needs_retrieval=true if the question depends on patent information.\n"
        "- needs_retrieval=false if it is purely conversational, generic, or can be answered without the patent corpus.\n"
    )

    resp = nodes_model.invoke([{"role": "user", "content": prompt}])
    text = (resp.content or "").strip()

    needs_retrieval = True
    try:
        needs_retrieval = bool(json.loads(text).get("needs_retrieval"))
    except Exception:
        needs_retrieval = True

    return {"retrieval_required": needs_retrieval, "routing_decision_raw": text}


def retrieve_context(state: Patent_Miner_State, where_filter: Optional[Dict[str, Any]] = None):
    """
    Uniqueness-enforced retrieval:
    - Select at most one chunk per patent (by 'doc_id' or fallback to 'index').
    - Iteratively exclude already-seen patents and fetch more until target_k is reached.
    - Optionally merge with an external metadata filter (where_filter).
    """
    # Latest cleaned question
    messages = state.get("messages") or []
    question = messages[-1].content if messages else ""

    # Config
    target_k = 5 # final number of unique patents to return (matches prior behavior)
    unique_key = "doc_id" # patent-level uniqueness key (present in vector store metadata)
    burst_k = 10 # how many candidates to fetch per round
    max_rounds = 6 # max number of bursts

    seen = set()
    selected_docs = []
    rounds = 0

    while len(selected_docs) < target_k and rounds < max_rounds:
        rounds += 1

        # Exclude already-seen patents
        exclusion_filter = {unique_key: {"$nin": list(seen)}} if seen else None

        # Merge external where_filter with exclusion_filter
        if where_filter and exclusion_filter:
            combined_filter = {"$and": [where_filter, exclusion_filter]}
        elif where_filter:
            combined_filter = where_filter
        else:
            combined_filter = exclusion_filter

        # Fetch a burst of candidates, excluding already selected patents
        try:
            docs = vector_storage.similarity_search(
            question,
            k=burst_k,
            filter=combined_filter, # Chroma's metadata filter
        )
        except TypeError:
        # Fallback for vector stores that expect "where" instead of "filter"
            docs = vector_storage.similarity_search(
            question,
            k=burst_k,
            where=combined_filter, # type: ignore
        )

        if not docs:
            break

        # Keep the first (most similar) chunk per unseen patent
        for d in docs:
            meta = dict(d.metadata) if d.metadata else {}
            uid = meta.get(unique_key) or meta.get("index")
            if not uid or uid in seen:
                continue
            seen.add(uid)
            selected_docs.append(d)
            if len(selected_docs) >= target_k:
                break


    chunks: List[Dict[str, Any]] = [
    {"text": d.page_content, "metadata": dict(d.metadata) if d.metadata else {}}
    for d in selected_docs
    ]
    #joined_context = "\n\n".join([c["text"] for c in chunks])

    return {"retrieved_context": chunks}


rusty_prompt = (
    "You are a patent search and retrieval assistant.\n"
    "Given the question, and retrieved patents below:\n\n"
    "Question: {question}\n\n"
    "Retrieved patents:\nPatent 1\n\n{patents}\n\n"
    "Use three sentences maximum to respond to the user. If the context is not relevant, say so.\n"
)

def rusty_answer(state: Patent_Miner_State):
    question = state["messages"][-1].content
    patents = state.get("joined_patents") or ""

    ## Refine context to full patent ##

    prompt = rusty_prompt.format(question=question, patents=patents)

    ## Rewrite invoke method -- 3/17
    response_text = nodes_model.invoke([{"role": "user", "content": prompt}]).content

    return {"messages": [{"role": "assistant", "content": response_text}], "answer": response_text}


general_prompt = (
    "You are a helpful assistant. Given the question below:\n\n"
    "Question: {question}\n\n"
    "Answer concisely in <= 3 sentences. If you don't know, say you don't know.\n"
)

def general_answer(state: Patent_Miner_State):
    question = state["messages"][-1].content
    prompt = general_prompt.format(question=question)

    response_text = nodes_model.invoke([{"role": "user", "content": prompt}]).content

    return {"messages": [{"role": "assistant", "content": response_text}], "answer": response_text}