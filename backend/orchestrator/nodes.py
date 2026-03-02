import json
from typing import Any, Dict, Optional, List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState

from patent_miner_classes import retrievalstate
from vector_store import vector_storage

load_dotenv()

N_MEMORY = 10

nodes_model = ChatOpenAI(
    model="protected.gpt-4.1",
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


def _trim_messages(messages, n=N_MEMORY):
    return messages[-n:] if messages else messages


def query_clean(state: MessagesState) -> dict:
    """
    Clean the latest user question.
    IMPORTANT: Do not overwrite `messages` (we keep it as chat history).
    """
    question = state["messages"][-1].content
    prompt = clean_prompt.format(question=question)

    cleaned_text = nodes_model.invoke([{"role": "user", "content": prompt}]).content.strip()
    return {"cleaned_query": cleaned_text}


def query_route(state: MessagesState) -> retrievalstate:
    user_text = state.get("cleaned_query") or state["messages"][-1].content

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


def retrieve_context(state: MessagesState, where_filter: Optional[Dict[str, Any]] = None) -> dict:
    """
    Retrieval uses ONLY the latest cleaned question (not full chat history).
    """
    search_kwargs = {"k": 5}
    retriever = vector_storage.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs,
    )

    question = state.get("cleaned_query") or state["messages"][-1].content
    docs = retriever.invoke(question)

    chunks: List[Dict[str, Any]] = [
        {"text": d.page_content, "metadata": dict(d.metadata) if d.metadata else {}}
        for d in docs
    ]
    joined_context = "\n\n".join([c["text"] for c in chunks])

    return {"joined_context": joined_context, "contexts": chunks}


rusty_prompt = (
    "You are a patent search and retrieval assistant.\n"
    "Question: {question}\n\n"
    "Retrieved context:\n{context}\n\n"
    "Use three sentences maximum. If the context is not relevant, say so.\n"
)

def rusty_answer(state: MessagesState) -> dict:
    question = state.get("cleaned_query") or state["messages"][-1].content
    context = state.get("joined_context") or ""
    prompt = rusty_prompt.format(question=question, context=context)

    # Conversational memory: include last N messages as context
    history = _trim_messages(state["messages"], N_MEMORY)
    response_text = nodes_model.invoke(history + [{"role": "user", "content": prompt}]).content

    return {"answer": response_text}


general_prompt = (
    "You are a helpful assistant.\n"
    "Answer concisely in <= 3 sentences. If you don't know, say you don't know.\n"
    "Question: {question}"
)

def general_answer(state: MessagesState) -> dict:
    question = state.get("cleaned_query") or state["messages"][-1].content
    prompt = general_prompt.format(question=question)

    history = _trim_messages(state["messages"], N_MEMORY)
    response_text = nodes_model.invoke(history + [{"role": "user", "content": prompt}]).content

    return {"answer": response_text}


def append_answer_to_messages(state: MessagesState) -> dict:
    """
    Append final answer into chat history and trim to last N messages.
    This is what makes assistant replies available for future turns via the checkpointer.
    """
    answer_text = state.get("answer", "")
    if not isinstance(answer_text, str):
        answer_text = str(answer_text)

    new_messages = list(state["messages"]) + [AIMessage(content=answer_text)]
    return {"messages": new_messages[-N_MEMORY:]}