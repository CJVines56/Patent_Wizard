from __future__ import annotations

import argparse
import os
import random
import time
import warnings
from contextlib import nullcontext
from pathlib import Path
from typing import Any

try:
    from backend.app.env_bootstrap import load_project_env
except ModuleNotFoundError:
    def load_project_env():
        return None

try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None

try:
    from langchain_core.callbacks.base import BaseCallbackHandler
except ModuleNotFoundError:
    class BaseCallbackHandler:  # type: ignore[no-redef]
        """Fallback base class so utility tests can import this module without LangChain."""

        pass

try:
    from langsmith.run_helpers import trace
except ModuleNotFoundError:
    trace = None

load_project_env()

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r"Importing (faithfulness|answer_relevancy) from 'ragas\.metrics' is deprecated.*",
)

DEFAULT_QUESTION_FILES = (
    "validation/regular_validation_I.txt",
    "backend/orchestrator/regular_validation_I.txt",
    "validation/regular_validation.txt",
    "validation/regular_validation_II.txt",
)


class RPMLimiterCallback(BaseCallbackHandler):
    """RPM limiter for LangChain LLM/chat model calls."""

    def __init__(self, rpm: int, jitter_s: float = 0.2):
        self.min_interval = 60.0 / max(rpm, 1)
        self.jitter_s = jitter_s
        self._next_time = 0.0

    def _sleep_if_needed(self):
        now = time.time()
        if now < self._next_time:
            time.sleep(self._next_time - now)
        self._next_time = time.time() + self.min_interval + random.uniform(0, self.jitter_s)

    def on_chat_model_start(self, serialized, messages, **kwargs):
        self._sleep_if_needed()

    def on_llm_start(self, serialized, prompts, **kwargs):
        self._sleep_if_needed()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_questions_path(csv_path: str | None = None) -> Path:
    if csv_path:
        candidate = Path(csv_path)
        if not candidate.is_absolute():
            candidate = _repo_root() / candidate
        return candidate

    for relative_path in DEFAULT_QUESTION_FILES:
        candidate = _repo_root() / relative_path
        if candidate.exists():
            return candidate

    return _repo_root() / DEFAULT_QUESTION_FILES[0]


def extract_cleaned_question(final_state: dict[str, Any], fallback_question: str) -> str:
    cleaned_query = final_state.get("cleaned_query")
    if isinstance(cleaned_query, str) and cleaned_query.strip():
        return cleaned_query.strip()

    messages = final_state.get("messages") or []
    for message in reversed(messages):
        role = getattr(message, "type", None)
        content = getattr(message, "content", None)
        if isinstance(message, dict):
            role = message.get("role", role)
            content = message.get("content", content)
        if role in {"human", "user"} and isinstance(content, str) and content.strip():
            return content.strip()

    return fallback_question


def extract_context_texts(final_state: dict[str, Any]) -> list[str]:
    raw_contexts = final_state.get("retrieved_context") or []
    return [
        item.get("text", "")
        for item in raw_contexts
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    ]


def _trace_context(question: str, thread_id: str):
    if trace is None:
        return nullcontext()

    return trace(
        name="langgraph_app_invoke",
        inputs={"question": question, "thread_id": thread_id},
        project_name=os.getenv("LANGSMITH_PROJECT", "default"),
    )


def run_one_with_graph(app, question: str, thread_id: str, app_rpm_budget: int = 60) -> dict[str, Any]:
    # Graph-level throttle because one graph invocation may trigger multiple model/tool calls.
    time.sleep(60.0 / max(app_rpm_budget, 1))

    try:
        with _trace_context(question, thread_id):
            final_state = app.invoke(
                {"messages": [{"role": "user", "content": question}]},
                config={"configurable": {"thread_id": thread_id}},
            )

        answer = final_state.get("answer", "")
        if isinstance(answer, list):
            answer = "\n".join(str(x) for x in answer)
        elif not isinstance(answer, str):
            answer = str(answer)

        return {
            "user_input": extract_cleaned_question(final_state, question),
            "response": answer,
            "retrieved_contexts": extract_context_texts(final_state),
        }
    except Exception as exc:
        print(f"Error running graph for question '{question}': {exc}")
        return {
            "user_input": question,
            "response": "",
            "retrieved_contexts": [],
            "error": str(exc),
        }


def load_questions(csv_path: str | Path, question_col: str) -> list[str]:
    path = Path(csv_path)
    if pd is None:
        print("Error loading questions: pandas is not installed.")
        return []
    try:
        df = pd.read_csv(path, sep=None, engine="python")
        if question_col not in df.columns:
            raise ValueError(f"Column '{question_col}' not found. Available: {list(df.columns)}")
        return df[question_col].dropna().astype(str).str.strip().tolist()
    except Exception as exc:
        print(f"Error loading questions from '{path}': {exc}")
        return []


def build_eval_rows(
    app,
    questions: list[str],
    thread_prefix: str = "regular-eval",
    app_rpm_budget: int = 60,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, question in enumerate(questions, start=1):
        thread_id = f"{thread_prefix}-{idx}"
        rows.append(run_one_with_graph(app, question, thread_id=thread_id, app_rpm_budget=app_rpm_budget))
    return rows


def build_graph_app():
    from backend.orchestrator.graph import compile_graph

    return compile_graph(print_mermaid=False)


def build_ragas_llm(model: str, ragas_rpm: int):
    try:
        from langchain_openai import ChatOpenAI
    except ModuleNotFoundError as exc:
        print(f"Error initializing LLM: {exc}")
        return None

    ragas_limiter = RPMLimiterCallback(rpm=ragas_rpm)
    try:
        return ChatOpenAI(
            model=model,
            temperature=0.2,
            callbacks=[ragas_limiter],
            n=3,
        )
    except Exception as exc:
        print(f"Error initializing LLM: {exc}")
        return None


def build_ragas_embeddings():
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ModuleNotFoundError as exc:
        print(f"Error initializing embeddings: {exc}")
        return None

    try:
        return HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    except Exception as exc:
        print(f"Error initializing embeddings: {exc}")
        return None


def run_ragas_evaluation(valid_rows: list[dict[str, Any]], ragas_llm, ragas_embeddings):
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, faithfulness
    except ModuleNotFoundError as exc:
        print(f"Error during evaluation: {exc}")
        return None

    try:
        return evaluate(
            dataset=Dataset.from_list(valid_rows),
            metrics=[faithfulness, answer_relevancy],
            llm=ragas_llm,
            embeddings=ragas_embeddings,
        )
    except Exception as exc:
        print(f"Error during evaluation: {exc}")
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RAGAS evaluation against the orchestrator graph.")
    parser.add_argument("--questions-path", default=None, help="Path to the question file.")
    parser.add_argument("--question-col", default="Question", help="Question column name.")
    parser.add_argument("--thread-prefix", default="regular-eval", help="Prefix for per-question thread IDs.")
    parser.add_argument("--app-rpm-budget", type=int, default=60, help="Throttle for graph invocations.")
    parser.add_argument("--ragas-rpm", type=int, default=90, help="Throttle for evaluator LLM calls.")
    parser.add_argument("--model", default="protected.gpt-5", help="Chat model used for RAGAS metrics.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    questions_path = resolve_questions_path(args.questions_path)

    ragas_llm = build_ragas_llm(args.model, args.ragas_rpm)
    ragas_embeddings = build_ragas_embeddings()

    questions = load_questions(questions_path, args.question_col)
    if not questions:
        print(f"No questions loaded from '{questions_path}'.")
        return 1

    app = build_graph_app()
    rows = build_eval_rows(
        app,
        questions,
        thread_prefix=args.thread_prefix,
        app_rpm_budget=args.app_rpm_budget,
    )

    valid_rows = [row for row in rows if row.get("response") and row.get("retrieved_contexts")]
    skipped_rows = len(rows) - len(valid_rows)

    if ragas_llm is None or ragas_embeddings is None:
        print("Evaluator initialization failed, evaluation skipped.")
        return 1
    if not valid_rows:
        print("No successful rows to evaluate after graph execution.")
        return 1
    if skipped_rows:
        print(f"Skipping {skipped_rows} rows that returned no response or no retrieved contexts.")

    results = run_ragas_evaluation(valid_rows, ragas_llm, ragas_embeddings)
    if results is None:
        return 1

    print(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
