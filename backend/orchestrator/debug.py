import os
import warnings

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r"Importing (faithfulness|answer_relevancy) from 'ragas\.metrics' is deprecated.*",
)

import time
from dotenv import load_dotenv
from graph import compile_graph
from langsmith.run_helpers import trace

load_dotenv()

def run_one_with_graph(app, question: str, thread_id: str, app_rpm_budget: int = 60) -> dict:
    # Graph-level throttle (graph triggers multiple calls internally)
    time.sleep(60.0 / max(app_rpm_budget, 1))

    try:
        with trace(
            name="langgraph_app_invoke",
            inputs={"question": question, "thread_id": thread_id},
            project_name=os.getenv("LANGSMITH_PROJECT", "default"),
        ):
            config = {"configurable": {"thread_id": thread_id}}
            
            final_state = app.invoke(
                {"messages": [{"role": "user", "content": question}]},
                config=config,
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

    # # Test 3
    # question = "Is there any patent on Biopsy articles?"
    # result = run_one_with_graph(app, question, thread_id=thread_id, app_rpm_budget=60)
    # print("\nAnswer:\n", result["response"])

    # Test 4
    question =  '''An assembly for processing meat moving along a path of travel, said assembly comprising:
    at least one blade roller extending transverse to a length of the path of travel and including a plurality of spaced apart blades,
    said plurality of blades transversely connected to a length of said blade roller and rotatable therewith in substantially aligned relation to the length of the path of travel and in cutting relation to the meat,
    a marking roller disposed transverse to the length of the path of travel adjacent to said blade roller and including a plurality of marking sections connected to said marking roller and rotatable therewith relative to the length of the path of travel,
    said plurality of marking sections collectively oriented in transverse relation to the length of said marking roller, and a plurality of spaces each disposed between different adjacent ones of said plurality of marking sections,
    each of said plurality of blades disposed to pass through different ones of said plurality spaces between adjacent ones of said plurality of marking sections, concurrent to rotation of said blade roller and said marking roller,
    each of said plurality of marking sections including at least one marking member extending outwardly from a periphery of said marking roller into a penetrating orientation with the meat passing along the path of travel during rotation of the marking roller,
    a support assembly including at least one support roller disposed in supporting relation to the meat concurrently to disposition of said plurality of marking members into said penetrating orientation with the meat,
    a stripper structure including a plurality of fingers each having a free end, each of said free ends disposed within said plurality of spaces between adjacent ones of said plurality of marking sections, in removable relation to meat retained on said marking roller, and
    a plurality of slots extending between adjacent ones of said plurality of fingers, each of said plurality of slots structured to receive and allow passage therethrough of a different one of said plurality of marking sections, concurrent to rotation of said marking roller.
    '''
    
    result = run_one_with_graph(app, question, thread_id=thread_id, app_rpm_budget=60)
    print("\nAnswer:\n", result["response"])

    #Test 5
    question = '''A golf club head, comprising:
    a body including a topline, a sole, and a front face, wherein the front face defines a rear surface that extends along a plane and the body defines a center of gravity plane, wherein the center of gravity plane extends parallel to a ground plane at a center of gravity of the body when the golf club head is at address; and
    a lattice structure formed on a portion of the body, layer by layer, via an additive manufacturing process, wherein the portion of the body is bounded by the plane, the center of gravity plane, the topline, and an intersection between the plane and the center of gravity plane, wherein the entire lattice structure is disposed above the center of gravity plane and behind the rear surface, 
    wherein the lattice structure extends along the topline toward a toe end of the body, and wherein a thickness is measured normal to the front face between the front face and a back of the lattice structure, the thickness being smaller in a region proximate the topline and larger in a region proximate the center of gravity plane.'''
    
    result = run_one_with_graph(app, question, thread_id=thread_id, app_rpm_budget=60)
    print("\nAnswer:\n", result["response"])

    #Test 6
    question = "Did he or she have any political relations with Nigeria during the time?"
    result = run_one_with_graph(app, question, thread_id=thread_id, app_rpm_budget=60)
    print("\nAnswer:\n", result["response"])

if __name__ == "__main__":
    main()