from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from patent_miner_classes import Patent_Miner_State

from nodes import (
    query_clean,
    query_route,
    retrieve_context,
    general_answer,
    rusty_answer,
    summarize_memory
)
from tools import routing_function


def build_graph():
    workflow = StateGraph(Patent_Miner_State)

    workflow.add_node("query_clean", query_clean)
    workflow.add_node("query_route", query_route)
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("general_answer", general_answer)
    workflow.add_node("rusty_answer", rusty_answer)
    workflow.add_node("summarize_memory", summarize_memory)

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

    # Both answer paths append to memory then END
    workflow.add_edge("rusty_answer", "summarize_memory")
    workflow.add_edge("general_answer", "summarize_memory")
    workflow.add_edge("summarize_memory", END)

    return workflow


def compile_graph(print_mermaid: bool = False):
    builder = build_graph()

    checkpointer = InMemorySaver()
    compiled_graph = builder.compile(checkpointer=checkpointer)

    if print_mermaid:
        print(compiled_graph.get_graph().draw_mermaid())

    return compiled_graph