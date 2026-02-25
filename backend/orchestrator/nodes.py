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

def query_route(state: MessagesState) -> retrievalstate:
    user_text = state["messages"][-1].content

    prompt = (
        "You are a router for a RAG system.\n"
        "Decide if answering the user requires retrieving external context.\n\n"
        "Return ONLY valid JSON with exactly this schema:\n"
        '{"needs_retrieval": true|false}\n\n'
        "Rules:\n"
        "- needs_retrieval=true if the question depends on domain-specific, private, or unknown info.\n"
        "- needs_retrieval=false if it is purely conversational, generic, or can be answered without the corpus.\n\n"
        f"User question:\n{user_text}\n"
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
    question = state["cleaned_query"]
    context = state["joined_context"]
    prompt = generate_prompt.format(question=question, context=context)
    response = nodes_model.invoke([{"role": "user", "content": prompt}])
    return {"answer": [response.content]}
