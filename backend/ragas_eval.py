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
            print(metadata)
            raw_contexts: List[Dict[str, Any]] = final_state.get("contexts") or []
            contexts: List[str] = [
                c.get("text", "") for c in raw_contexts if isinstance(c, dict) and c.get("text")
            ]
        return {"question": cleaned_q, "answer": answer, "contexts": contexts, "metadata": metadata}
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


if __name__ == "__main__":
    CSV_PATH = "eval_questions_3.txt"
    QUESTION_COL = "unclean_question"

    # ---- RAGAS LLM (metrics) ----
    # Tune this to your provider limits.
    # Faithfulness + answer_relevancy can trigger multiple calls per row,
    # so keep it conservative first (e.g., 60-120 rpm).
    ragas_limiter = RPMLimiterCallback(rpm=90)

    try:
        # If your LLM supports 'n' generations, set n=3, otherwise leave as default
        ragas_llm = ChatOpenAI(
            model="protected.gemini-2.5-flash",
            temperature=0.2,
            callbacks=[ragas_limiter],
            n=3            # n=3,  # Uncomment if supported by your LLM API
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

    ## Clean_accuracy test ##
    rows = [run_one_with_graph(app, q, app_rpm_budget=60) for q in questions]
    with open('output_clean_query.txt', 'w', encoding='utf-8') as f:
        for row in rows:
            question = row.get('question')
            f.write(f"{question}\n")
    
    ## Metadata_accuracy test ##
    # rows = [run_one_with_graph(app, q, app_rpm_budget=60) for q in questions]
    # with open('output_metadata.txt', 'w', encoding='utf-8') as f:
    #     for row in rows:
    #         metadata = row.get('metadata')
    #         f.write(f"{metadata}\n")


    # rows = [run_one_with_graph(app, q, app_rpm_budget=60) for q in questions]

    # ds = Dataset.from_list(rows)
    # if ragas_llm is None:
    #     print("LLM is not initialized, evaluation skipped.")
    # elif len(rows) == 0:
    #     print("No rows to evaluate, check your question file.")
    # else:
    #     try:
    #         results = evaluate(
    #             dataset=ds,
    #             metrics=metrics,
    #             llm=ragas_llm,
    #             embeddings=ragas_embeddings,
    #         )
    #         print(results)
    #         print(results.to_pandas())
    #     except Exception as e:
    #         print(f"Error during evaluation: {e}")

    # print(results)
    # print(results.to_pandas())