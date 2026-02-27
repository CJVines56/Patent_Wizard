import os
import json
from typing import Any, Dict, Optional, List
from nodes2 import metadatastate
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from patent_miner_classes import CleanedQuery, retrievalstate
from vector_store import vector_storage
from dotenv import load_dotenv
import pdb

load_dotenv()


nodes_model = ChatOpenAI(
    model="protected.gpt-4.1",
    temperature=0.2,
)

#clean_structured_llm = nodes_model.with_structured_output(CleanedQuery)

## Query Cleaning Node ##


clean_prompt = (
    "You are a patent search and retrieval assistant. \n"
    "Given a user question, detect and correct grammatical errors and misspellings. \n"
    "If the question contains ambiguous or vague words/phrases - rewrite it concisely while preserving meaning. \n"
    "If the question contains no errors or ambiguity - do not rewite it. \n"
    "Here is the user question: {question}"
)


def query_clean(state: MessagesState):
    """Clean the original user question."""
    messages = state["messages"]
    question = messages[0].content
    prompt = clean_prompt.format(question=question)
    
    cleaned_q = nodes_model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [cleaned_q],"cleaned_query": cleaned_q}

## Query Routing Node ##

def query_route(state: MessagesState) -> retrievalstate:
    user_text = state["messages"][-1].content

    prompt = (
        "You are a router for a Patent search and retrieval RAG system.\n"
        f"Given the question: \n{user_text}\n"
        "Decide if answering the user requires retrieving context from the RAG patent database.\n\n"
        "Return ONLY valid JSON with exactly this schema:\n"
        '{"needs_retrieval": true|false}\n\n'
        "Rules:\n"
        "- needs_retrieval=true if the question depends on patent information.\n"
        "- needs_retrieval=false if it is purely conversational, generic, or can be answered without the patent corpus.\n\n"
    )

    resp = nodes_model.invoke(prompt)
    text = getattr(resp, "content", str(resp)).strip()

    needs_retrieval = True  # safe default
    try:
        needs_retrieval = bool(json.loads(text).get("needs_retrieval"))
    except Exception:
        # If the model outputs invalid JSON, default to retrieval to avoid false negatives.
        needs_retrieval = True

    return {
        "retrieval_required": needs_retrieval,
        "routing_decision_raw": text,
    }


## Retrieval Node ##

def retrieve_context(state: metadatastate, where_filter: Optional[Dict[str, Any]] = None) -> metadatastate:
    """Retrieve information to help answer a query, optionally using metadata filters.

    Args:
        query: Search terms to look for
        where_filter: Filter for database search
    """
    search_kwargs = {"k": 5}
    where_filter = state['chroma_filter']
    if where_filter:
        # Chroma / langchain-chroma supports `filter` in search_kwargs in many setups.
        # If your environment expects `where`, change the key accordingly.
        search_kwargs["filter"] = where_filter
    retriever = vector_storage.as_retriever(search_type="similarity", 
                                            search_kwargs=search_kwargs,)
    
    question=state['cleaned_query']
    context = retriever.invoke(question)
    
    chunks: List[Dict[str, Any]] = [
        {
            "text": d.page_content,
            "metadata": dict(d.metadata) if d.metadata else {},
        }
        for d in context
    ]

    joined_context = "\n\n".join([c["text"] for c in chunks])

    return {
        "joined_context": joined_context,
        "contexts": chunks,
    }

## Response Generation Node 1 ##

rusty_prompt = (
    "You are a patent search and retrieval assistant.\n"
    "Given the question: {question}"
    "Use the following retrieved context to answer it:\n"
    "{context}"
    "Use three sentences maximum to respond and keep the answer concise.\n"
    "If no context is provided. Respond that the provided context is not relevant to the question.\n"
)

def rusty_answer(state: metadatastate)-> metadatastate:
    """Generate an answer."""
    question = state["cleaned_query"]
    context = state["joined_context"]
    prompt = rusty_prompt.format(question=question, context=context)
    response = nodes_model.invoke([{"role": "user", "content": prompt}])
    return {"answer": [response.content]}


## Response Generation Node 2 ##

general_prompt = (
    "You are a patent search and retrieval assistant.\n"
    "Given the question: {question}"
    "Respond the user consicely. If you do not know - just say that you do not know. \n"
    "Use three sentences maximum to respond."
)

def general_answer(state: metadatastate)-> metadatastate:
    """Generate an answer."""
    question = state["cleaned_query"]
    prompt = general_prompt.format(question=question)
    response = nodes_model.invoke([{"role": "user", "content": prompt}])
    return {"answer": [response.content]}
