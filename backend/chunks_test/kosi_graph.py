from langgraph.graph import StateGraph, START, END
from kosi_patent_miner_classes import Patent_Miner_State

from kosi_node import (
    query_clean,
    query_route,
    retrieve_context,
    general_answer,
    rusty_answer,
)

from kosi_tools import routing_function


def build_graph():
    workflow = StateGraph(Patent_Miner_State)

    workflow.add_node("query_clean", query_clean)
    workflow.add_node("query_route", query_route)
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("general_answer", general_answer)
    workflow.add_node("rusty_answer", rusty_answer)

    workflow.add_edge(START, "query_clean")
    workflow.add_edge("query_clean", "query_route")

    workflow.add_conditional_edges(
        "query_route",
        routing_function,
        {
            "retrieve": "retrieve",
            "answer": "general_answer",
        },
    )

    workflow.add_edge("retrieve", "rusty_answer")

    workflow.add_edge("rusty_answer", END)
    workflow.add_edge("general_answer", END)

    return workflow


def compile_graph(print_mermaid: bool = False):
    builder = build_graph()

    compiled_graph = builder.compile()

    if print_mermaid:
        print(compiled_graph.get_graph().draw_mermaid())

    return compiled_graph