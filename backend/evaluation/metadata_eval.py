import os
import warnings
import time
import random
from typing import Any, Dict, List, Optional

import pandas as pd
from datasets import Dataset
from dotenv import load_dotenv

from ragas import evaluate
from langchain_openai import ChatOpenAI
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_huggingface import HuggingFaceEmbeddings
from langsmith.run_helpers import trace

from orchestrator.graph import compile_graph
from orchestrator.custom_metric import MetadataAccuracy  # <-- use your custom metric [1]

load_dotenv()

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r"Importing (faithfulness|answer_relevancy) from 'ragas\.metrics' is deprecated.*",
)


class RPMLimiterCallback(BaseCallbackHandler):
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


def run_one_with_graph(app, question: str, expected_metadata: Any, app_rpm_budget: int = 60) -> dict:
    # Graph-level throttle (graph triggers multiple calls internally) [2]
    time.sleep(60.0 / max(app_rpm_budget, 1))

    try:
        with trace(
            name="langgraph_app_invoke",
            inputs={"question": question},
            project_name=os.getenv("LANGSMITH_PROJECT", "default"),
        ):
            final_state = app.invoke({"messages": [{"role": "user", "content": question}]})

            cleaned_q = final_state.get("cleaned_query", question)
            metadata = final_state.get("metadata")

        # Return the columns required by MetadataAccuracy [1]
        return {
            "user_input": cleaned_q,              # optional, but nice to keep
            "metadata": metadata,                 # required [1]
            "expected_metadata": expected_metadata,  # required [1]
        }

    except Exception as e:
        print(f"Error running graph for question '{question}': {e}")
        # Keep the SAME schema even on failure [2]
        return {
            "user_input": question,
            "metadata": None,
            "expected_metadata": expected_metadata,
        }


def load_eval_rows(csv_path: str, question_col: str, expected_metadata_col: str) -> list[dict]:
    try:
        df = pd.read_csv(csv_path)
        missing = [c for c in (question_col, expected_metadata_col) if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns {missing}. Available: {list(df.columns)}")

        rows = []
        for _, r in df.iterrows():
            q = r[question_col]
            if pd.isna(q):
                continue
            rows.append(
                {
                    "question": str(q),
                    "expected_metadata": r[expected_metadata_col],
                }
            )
        return rows

    except Exception as e:
        print(f"Error loading eval rows from '{csv_path}': {e}")
        return []


if __name__ == "__main__":
    CSV_PATH = "./validation/test_validation.txt"
    QUESTION_COL = "Question"
    EXPECTED_METADATA_COL = "expected_metadata"  # <-- change to your actual column name

    # LLM used by ragas (not strictly needed for MetadataAccuracy, but safe to keep)
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

    # Not needed for MetadataAccuracy, but evaluate() may accept it; harmless to omit or keep.
    ragas_embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    app = compile_graph(print_mermaid=False)

    eval_inputs = load_eval_rows(CSV_PATH, QUESTION_COL, EXPECTED_METADATA_COL)
    rows = [
        run_one_with_graph(app, x["question"], x["expected_metadata"], app_rpm_budget=60)
        for x in eval_inputs
    ]

    results = None
    if len(rows) == 0:
        print("No rows to evaluate. Check your CSV path/columns.")
    else:
        ds = Dataset.from_list(rows)

        # Only evaluate MetadataAccuracy [1]
        metrics = [MetadataAccuracy()]

        try:
            results = evaluate(
                dataset=ds,
                metrics=metrics,
                llm=ragas_llm,              # not used by MetadataAccuracy, but ok
                embeddings=ragas_embeddings # not used by MetadataAccuracy, but ok
            )
        except Exception as e:
            print(f"Error during evaluation: {e}")

    if results is not None:
        print(results)