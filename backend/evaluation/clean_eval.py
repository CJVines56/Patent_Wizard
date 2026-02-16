import os
import warnings
import time
import random
from typing import Any, Dict, List

import pandas as pd
from datasets import Dataset
from dotenv import load_dotenv

from ragas import evaluate
from langchain_openai import ChatOpenAI
from langchain_core.callbacks.base import BaseCallbackHandler
from langsmith.run_helpers import trace

from orchestrator.graph import compile_graph
from orchestrator.custom_metric import CleanAccuracy  # <-- use custom metric [1]

load_dotenv()

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r"Importing (faithfulness|answer_relevancy) from 'ragas\.metrics' is deprecated.*",
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


def run_one_with_graph(app, question: str, app_rpm_budget: int = 60) -> dict:
    # Graph-level throttle (graph may trigger multiple provider calls) [2]
    time.sleep(60.0 / max(app_rpm_budget, 1))

    try:
        with trace(
            name="langgraph_app_invoke",
            inputs={"question": question},
            project_name=os.getenv("LANGSMITH_PROJECT", "default"),
        ):
            final_state = app.invoke({"messages": [{"role": "user", "content": question}]})

            cleaned_q = final_state.get("cleaned_query", "")

        # CleanAccuracy requires these columns [1]
        return {
            "unclean_question": question,
            "cleaned_query": cleaned_q,
        }

    except Exception as e:
        print(f"Error running graph for question '{question}': {e}")
        # keep same schema even on failure [2]
        return {
            "unclean_question": question,
            "cleaned_query": "",
        }


def load_questions(csv_path: str, question_col: str) -> list[str]:
    try:
        df = pd.read_csv(csv_path)
        if question_col not in df.columns:
            raise ValueError(f"Column '{question_col}' not found. Available: {list(df.columns)}")
        return df[question_col].dropna().astype(str).tolist()
    except Exception as e:
        print(f"Error loading questions from '{csv_path}': {e}")
        return []


if __name__ == "__main__":
    CSV_PATH = "./validation/test_validation.txt"
    QUESTION_COL = "Question"

    limiter = RPMLimiterCallback(rpm=90)

    # LLM used by CleanAccuracy.score() [1]
    try:
        judge_llm = ChatOpenAI(
            model="protected.gemini-2.5-flash",
            temperature=0.0,
            callbacks=[limiter],
        )
    except Exception as e:
        print(f"Error initializing judge LLM: {e}")
        judge_llm = None

    app = compile_graph(print_mermaid=False)

    questions = load_questions(CSV_PATH, QUESTION_COL)
    rows = [run_one_with_graph(app, q, app_rpm_budget=60) for q in questions]

    results = None
    if judge_llm is None:
        print("Judge LLM is not initialized, evaluation skipped.")
    elif len(rows) == 0:
        print("No rows to evaluate, check your question file.")
    else:
        ds = Dataset.from_list(rows)

        # Only evaluate CleanAccuracy [1]
        metrics = [CleanAccuracy(llm=judge_llm)]

        try:
            results = evaluate(
                dataset=ds,
                metrics=metrics,
                llm=judge_llm,  # not strictly necessary for this custom metric, but safe
            )
        except Exception as e:
            print(f"Error during evaluation: {e}")

    if results is not None:
        print(results)