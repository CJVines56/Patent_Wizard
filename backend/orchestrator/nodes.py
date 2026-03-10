import json
from typing import Any, Dict, Optional, List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from patent_miner_classes import retrievalstate, Patent_Miner_State
from vector_store import vector_storage

load_dotenv()

# N_MEMORY = 10

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
    messages[-1] = {"role": "user", "content": cleaned_query}
    state["messages"][-1].content = messages[-1]["content"]
    return None


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
    Retrieval uses ONLY the latest cleaned question (not full chat history).
    """
    search_kwargs = {"k": 5}
    retriever = vector_storage.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs,
    )

    question = state["messages"][-1].content
    docs = retriever.invoke(question)

    chunks: List[Dict[str, Any]] = [
        {"text": d.page_content, "metadata": dict(d.metadata) if d.metadata else {}}
        for d in docs
    ]
    joined_context = "\n\n".join([c["text"] for c in chunks])

    return {"joined_context": joined_context, "contexts": chunks}


rusty_prompt = (
    "You are a patent search and retrieval assistant.\n"
    "Given the question and retrieved context below:\n"
    "Question: {question}\n\n"
    "Retrieved context:\n{context}\n\n"
    "Use three sentences maximum to respond to the user. If the context is not relevant, say so.\n"
)

def rusty_answer(state: Patent_Miner_State):
    question = state["messages"][-1].content
    context = state.get("joined_context") or ""
    prompt = rusty_prompt.format(question=question, context=context)

    # Conversational memory: include last N messages as context
    history = _history_with_summary(state)
    response_text = nodes_model.invoke(history + [{"role": "user", "content": prompt}]).content

    return {"messages": [{"role": "assistant", "content": response_text}]}


general_prompt = (
    "You are a helpful assistant.\n"
    "Answer concisely in <= 3 sentences. If you don't know, say you don't know.\n"
    "Question: {question}"
)

def general_answer(state: Patent_Miner_State):
    question = state["messages"][-1].content
    prompt = general_prompt.format(question=question)

    history = _history_with_summary(state)
    response_text = nodes_model.invoke(history + [{"role": "user", "content": prompt}]).content

    return {"messages": [{"role": "assistant", "content": response_text}]}

## Message summarization ##

N_MEMORY = 4          # keep last 4 verbatim
SUMMARIZE_KEEP = 2     # summarize everything except last 2 (tune as you like)

summary_model = ChatOpenAI(
    model="protected.gpt-4.1",
    temperature=0.2,
)

summary_prompt = ("You maintain a rolling conversation summary for a patent assistant. \n"
                  "Existing summary (may be empty): \n{existing_summary}\n\n"
                  "New dialogue to incorporate: \n{dialogue}\n\n"
                  "Update the summary. Preserve:\n"
                  "- user goals, constraints, preferences\n"
                  "- decisions and plans\n"
                  "- important entities (names, dates, patent/publication numbers if present)\n"
                  "- open questions / next steps\n"
                  "Be concise. Do not invent details.\n"
                  "Return ONLY the updated summary."
)

def _format_dialogue(msgs):
    lines = []
    for m in msgs:
        role = m.type
        content = m.content
        lines.append(f"{role.upper()}: {content}")
    return "\n".join(lines)

def maybe_summarize_messages(state: Patent_Miner_State):
    """
    If messages exceed N_MEMORY, summarize the oldest part into conversation_summary,
    then keep only the last SUMMARIZE_KEEP messages verbatim.
    """
    messages = list(state.get("messages") or [])
    if len(messages) <= N_MEMORY:
        return {}

    existing_summary = state.get("conversation_summary") or ""

    # summarize everything except the last SUMMARIZE_KEEP messages
    to_summarize = messages[:-SUMMARIZE_KEEP]
    to_keep = messages[-SUMMARIZE_KEEP:]

    dialogue = _format_dialogue(to_summarize)
    print(dialogue)
    prompt = summary_prompt.format(existing_summary=existing_summary, dialogue=dialogue)

    updated_summary = summary_model.invoke([{"role": "user", "content": prompt}]).content.strip()
    print(updated_summary)

    return {
        "conversation_summary": updated_summary,
        "messages": to_keep,
    }


def _history_with_summary(state: Patent_Miner_State):
    msgs = list(state.get("messages") or [])
    summary = (state.get("conversation_summary") or "").strip()
    if summary:
        return [{"role": "system", "content": f"Conversation summary so far:\n{summary}"}] + msgs
    return msgs

def summarize_memory(state: Patent_Miner_State):

    return maybe_summarize_messages(state)