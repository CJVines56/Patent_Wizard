import os
import warnings

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r"Importing (faithfulness|answer_relevancy) from 'ragas\.metrics' is deprecated.*",
)

import time
import pdb
from typing import Any, Dict, List

import pandas as pd
import random
from datasets import Dataset
from dotenv import load_dotenv

from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from custom_metric import MetadataAccuracy, CleanAccuracy

from langchain_openai import ChatOpenAI
from langchain_core.callbacks.base import BaseCallbackHandler

from graph import compile_graph
from langchain_huggingface import HuggingFaceEmbeddings
from langsmith.run_helpers import trace

load_dotenv()


class RPMLimiterCallback(BaseCallbackHandler):
    """
    RPM limiter for LangChain LLM/chat model calls.
    Works for sync runs and remains compatible even if a caller switches to batch/async later.
    """
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
    # Graph-level throttle (graph triggers multiple Gemini calls internally) [1][2][3]
    time.sleep(60.0 / max(app_rpm_budget, 1))

    try:

        with trace(
        name="langgraph_app_invoke",
        inputs={"question": question},
        project_name=os.getenv("LANGSMITH_PROJECT", "default"),
    ):
            
            final_state = app.invoke({"messages": [{"role": "user", "content": question}]})
            answer = final_state["answer"]
            if isinstance(answer, list):
                answer = "\n".join(str(x) for x in answer)
            elif not isinstance(answer, str):
                answer = str(answer)
            cleaned_q = final_state["cleaned_query"]
            metadata = final_state["metadata"]
            raw_contexts: List[Dict[str, Any]] = final_state.get("contexts") or []
            contexts: List[str] = [
                c.get("text", "") for c in raw_contexts if isinstance(c, dict) and c.get("text")
            ]
        return {
        "response": answer
    }

    except Exception as e:
        print(f"Error running graph for question '{question}': {e}")
        return {"question": question, "answer": "", "contexts": [], "metadata": ""}


def load_questions(csv_path: str, question_col: str) -> list[str]:
    try:
        df = pd.read_csv(csv_path)
        if question_col not in df.columns:
            raise ValueError(f"Column '{question_col}' not found. Available: {list(df.columns)}")
        return df[question_col].dropna().astype(str).tolist()
    except Exception as e:
        print(f"Error loading questions from '{csv_path}': {e}")
        return []


def main():
    ragas_limiter = RPMLimiterCallback(rpm=90)

    try:
        llm = ChatOpenAI(
            model="protected.gemini-2.5-flash",
            temperature=0.2,
            callbacks=[ragas_limiter],
        )
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        return

    app = compile_graph(print_mermaid=False)

    quit_commands = {"q", "quit", "exit"}

    while True:
        try:
            question = input("\nEnter your question (q/quit/exit to stop): ").strip()
            if not question:
                continue
            if question.lower() in quit_commands:
                break

            answer = run_one_with_graph(app, question, app_rpm_budget=60)
            print("\nAnswer:\n", answer)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()