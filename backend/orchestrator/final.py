# import os
# import warnings

# warnings.filterwarnings(
#     "ignore",
#     category=DeprecationWarning,
#     message=r"Importing (faithfulness|answer_relevancy) from 'ragas\.metrics' is deprecated.*",
# )

# import time
# from typing import Any, Dict, List
# import random

# import pandas as pd
# from datasets import Dataset
# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
# from langchain_core.callbacks.base import BaseCallbackHandler

# from graph import compile_graph
# from langsmith.run_helpers import trace

# load_dotenv()


# class RPMLimiterCallback(BaseCallbackHandler):
#     """
#     RPM limiter for LangChain LLM/chat model calls.
#     Works for sync runs and remains compatible even if a caller switches to batch/async later.
#     """
#     def __init__(self, rpm: int, jitter_s: float = 0.2):
#         self.min_interval = 60.0 / max(rpm, 1)
#         self.jitter_s = jitter_s
#         self._next_time = 0.0

#     def _sleep_if_needed(self):
#         now = time.time()
#         if now < self._next_time:
#             time.sleep(self._next_time - now)
#         self._next_time = time.time() + self.min_interval + random.uniform(0, self.jitter_s)

#     def on_chat_model_start(self, serialized, messages, **kwargs):
#         self._sleep_if_needed()

#     def on_llm_start(self, serialized, prompts, **kwargs):
#         self._sleep_if_needed()


# def run_one_with_graph(app, question: str, thread_id: str, app_rpm_budget: int = 60) -> dict:
#     # Graph-level throttle (graph triggers multiple calls internally)
#     time.sleep(60.0 / max(app_rpm_budget, 1))

#     try:
#         with trace(
#             name="langgraph_app_invoke",
#             inputs={"question": question, "thread_id": thread_id},
#             project_name=os.getenv("LANGSMITH_PROJECT", "default"),
#         ):
#             config = {"configurable": {"thread_id": thread_id}}

#             final_state = app.invoke(
#                 {"messages": [{"role": "user", "content": question}]},
#                 config=config,
#             )

#             answer = final_state["messages"][-1].content
#             if isinstance(answer, list):
#                 answer = "\n".join(str(x) for x in answer)
#             elif not isinstance(answer, str):
#                 answer = str(answer)

#             return {"response": answer}

#     except Exception as e:
#         print(f"Error running graph for question '{question}': {e}")
#         return {"response": ""}


# def main():

#     app = compile_graph(print_mermaid=False)

#     quit_commands = {"q", "quit", "exit"}

#     # For dev CLI: a single fixed session (thread) for the whole run
#     thread_id = "dev-session-1"

#     while True:
#         try:
#             question = input("\nEnter your question (q/quit/exit to stop): ").strip()
#             if not question:
#                 continue
#             if question.lower() in quit_commands:
#                 break

#             result = run_one_with_graph(app, question, thread_id=thread_id, app_rpm_budget=60)
#             print("\nAnswer:\n", result["response"])

#         except KeyboardInterrupt:
#             print("\nExiting...")
#             break
#         except Exception as e:
#             print(f"Error: {e}")


# if __name__ == "__main__":
#     main()