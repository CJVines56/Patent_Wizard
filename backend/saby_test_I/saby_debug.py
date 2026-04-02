import os
import warnings

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r"Importing (faithfulness|answer_relevancy) from 'ragas\.metrics' is deprecated.*",
)

import time
from dotenv import load_dotenv
from saby_graph import compile_graph
from langsmith.run_helpers import trace

load_dotenv()

def run_one_with_graph(app, question: str, app_rpm_budget: int = 60) -> dict:
    # Graph-level throttle (graph triggers multiple calls internally)
    time.sleep(60.0 / max(app_rpm_budget, 1))

    try:
        with trace(
            name="langgraph_app_invoke",
            inputs={"question": question},
            project_name=os.getenv("LANGSMITH_PROJECT", "default"),
        ):
            
            final_state = app.invoke(
                {"messages": [{"role": "user", "content": question}]}
            )

            answer = final_state["answer"]
            if isinstance(answer, list):
                answer = "\n".join(str(x) for x in answer)
            elif not isinstance(answer, str):
                answer = str(answer)

            return {"response": answer}

    except Exception as e:
        print(f"Error running graph for question '{question}': {e}")
        return {"response": ""}


def main():
    app = compile_graph(print_mermaid=False)

    # For dev CLI: a single fixed session (thread) for the whole run
    thread_id = "dev-session-1"

    # #Test 1
    # question = "How are yo]iu doing timoay bugdy"
    # result = run_one_with_graph(app, question, thread_id=thread_id, app_rpm_budget=60)
    # print("\nAnswer:\n", result["response"])

    # Test 2
    # question = "Is there any patent on Biopsy articles?"
    # result = run_one_with_graph(app, question, thread_id=thread_id, app_rpm_budget=60)
    # print("\nAnswer:\n", result["response"])

    # Test 3
    question = "Is there any patent on chromatographic reader devices for biodetection?"
    result = run_one_with_graph(app, question, app_rpm_budget=60)
    print("\nAnswer:\n", result["response"])

    # # Test 4
    # question = "Is Barack Obama still the president of the USA?"
    # result = run_one_with_graph(app, question, thread_id=thread_id, app_rpm_budget=60)
    # print("\nAnswer:\n", result["response"])

    # #Test 5
    # question = "Who was President of the US when Vidal started running things?"
    # result = run_one_with_graph(app, question, thread_id=thread_id, app_rpm_budget=60)
    # print("\nAnswer:\n", result["response"])

    # #Test 6
    # question = "Did the President and Kathi have a good relationship?"
    # result = run_one_with_graph(app, question, thread_id=thread_id, app_rpm_budget=60)
    # print("\nAnswer:\n", result["response"])

if __name__ == "__main__":
    main()