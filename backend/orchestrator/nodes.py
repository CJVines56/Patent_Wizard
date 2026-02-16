import os
import json
from typing import Any, Dict, Optional
from nodes2 import metadatastate
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from patent_miner_classes import CleanedQuery, retrievalstate
from tools import retriever_tool
from dotenv import load_dotenv

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
    user_text = state["messages"][-1]["content"]

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

# def retrieval_node(state: metadatastate) -> MessagesState:
#     """Call the model to generate a response based on the current state. 
#     Given the question, it will retrieve using the retriever tool.
#     If the model invokes the retriever tool, it also receives the respective metadata filter for the query."
#     """

#     where_filter = state["chroma_filter"]  # set by metadata_filter_node

#     sys = (
#         "If you call the retrieval tool, you MUST pass:\n"
#         f'- query: the user question\n- where_filter: {where_filter}\n'
#         "If where_filter is null/empty, omit it."
#     )

#     response = (
#         nodes_model
#         .bind_tools([retriever_tool]).invoke([{"role": "system", "content": sys}] + state["cleaned_query"])
#     )

#     return {"messages": [response]}

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
        "contexts": state.get("chunks", []) or [],
        "joined_context": state.get("joined_text", "") or "",
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
