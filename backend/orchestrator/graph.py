from langgraph.graph import MessagesState, StateGraph, START, END
from nodes import retrieve_context
from nodes import query_clean, query_route, general_answer, rusty_answer
from nodes2 import metadata_filter_node
from patent_miner_classes import metadatastate
from tools import routing_function


def build_graph():
    """
    Build and return the uncompiled graph (builder).
    Call draw_mermaid() on this builder if you want to visualize without warnings.
    """

    workflow = StateGraph(MessagesState, output_schema=metadatastate)

    workflow.add_node("query_clean", query_clean)
    workflow.add_node("query_route", query_route)
    workflow.add_node("metadata_filter", metadata_filter_node)
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("general_answer", general_answer)
    workflow.add_node("rusty_answer", rusty_answer)

    workflow.add_edge(START, "query_clean")
    workflow.add_edge("query_clean", "query_route")  #NEW

    workflow.add_conditional_edges(
    "query_route",
    routing_function,
    {"metadatafilter": "metadata_filter", "answer": "general_answer"},
    )

    workflow.add_edge("metadata_filter", "retrieve")
    workflow.add_edge("retrieve", "rusty_answer")   # changed
    workflow.add_edge("rusty_answer", END)
    workflow.add_edge("general_answer", END)

    return workflow

def compile_graph(print_mermaid: bool = False):
    builder = build_graph()
    compiled_graph = builder.compile()

    if print_mermaid:
        print(compiled_graph.get_graph().draw_mermaid())

    return compiled_graph