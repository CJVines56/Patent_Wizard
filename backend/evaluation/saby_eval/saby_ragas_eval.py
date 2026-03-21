import os
import warnings
import time
import random
from typing import Any, Dict, List

import pandas as pd
from datasets import Dataset
from dotenv import load_dotenv

from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

from langchain_openai import ChatOpenAI
from langchain_core.callbacks.base import BaseCallbackHandler

from saby_graph import compile_graph
from langchain_huggingface import HuggingFaceEmbeddings
from langsmith.run_helpers import trace

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
    # Graph-level throttle (graph may trigger multiple provider calls internally)
    time.sleep(60.0 / max(app_rpm_budget, 1))

    try:
        with trace(
            name="langgraph_app_invoke",
            inputs={"question": question},
            project_name=os.getenv("LANGSMITH_PROJECT", "default"),
        ):
            final_state = app.invoke({"messages": [{"role": "user", "content": question}]})

            answer = final_state.get("answer", "")
            if isinstance(answer, list):
                answer = "\n".join(str(x) for x in answer)
            elif not isinstance(answer, str):
                answer = str(answer)

            cleaned_q = final_state.get("cleaned_query", question)

            raw_contexts: List[Dict[str, Any]] = final_state.get("contexts") or []
            contexts: List[str] = [
                c.get("text", "")
                for c in raw_contexts
                if isinstance(c, dict) and c.get("text")
            ]

        return {
            "user_input": cleaned_q,
            "response": answer,
            "retrieved_contexts": contexts,
        }

    except Exception as e:
        print(f"Error running graph for question '{question}': {e}")
        # keep the same schema as success
        return {
            "user_input": question,
            "response": "",
            "retrieved_contexts": [],
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

    results = None

    ragas_limiter = RPMLimiterCallback(rpm=90)
    try:
        ragas_llm = ChatOpenAI(
            model="protected.gemini-2.5-flash",
            temperature=0.2,
            callbacks=[ragas_limiter],
            n=3,
        )
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        ragas_llm = None

    ragas_embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    metrics = [faithfulness, answer_relevancy]
    app = compile_graph(print_mermaid=False)

    questions = load_questions(CSV_PATH, QUESTION_COL)
    rows = [run_one_with_graph(app, q, app_rpm_budget=60) for q in questions]

    if ragas_llm is None:
        print("LLM is not initialized, evaluation skipped.")
    elif len(rows) == 0:
        print("No rows to evaluate, check your question file.")
    else:
        ds = Dataset.from_list(rows)
        try:
            results = evaluate(
                dataset=ds,
                metrics=metrics,
                llm=ragas_llm,
                embeddings=ragas_embeddings,
            )
        except Exception as e:
            print(f"Error during evaluation: {e}")

    if results is not None:
        print(results)