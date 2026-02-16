from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from tools import retriever_tool
from nodes import query_clean, query_route, generate_answer, store_contexts
from nodes2 import metadata_filter_node
from patent_miner_classes import metadatastate
from tools import route_from_query


def build_graph():
    """
    Build and return the uncompiled graph (builder).
    Call draw_mermaid() on this builder if you want to visualize without warnings.
    """

    workflow = StateGraph(MessagesState, output_schema=metadatastate)

    workflow.add_node("query_clean", query_clean)
    workflow.add_node("query_route", query_route)
    workflow.add_node("metadata_filter", metadata_filter_node)
    workflow.add_node("retrieve", ToolNode([retriever_tool]))
    workflow.add_node("store_contexts", store_contexts)      # NEW
    workflow.add_node("generate_answer", generate_answer)

    workflow.add_edge(START, "query_clean")
    workflow.add_edge("query_clean", "query_route")  #NEW

    workflow.add_conditional_edges(
    "query_route",
    route_from_query,
    {"metadatafilter": "metadatafilter", END: END},
)

    workflow.add_edge("metadatafilter", "retrieve")
    workflow.add_edge("retrieve", "store_contexts")          # changed
    workflow.add_edge("store_contexts", "generate_answer")   # changed
    workflow.add_edge("generate_answer", END)

    return workflow

def compile_graph(print_mermaid: bool = False):
    builder = build_graph()
    compiled_graph = builder.compile()

    if print_mermaid:
        print(compiled_graph.get_graph().draw_mermaid())

    return compiled_graph