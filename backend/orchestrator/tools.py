from typing import Any, Dict, List, Optional
from langchain.tools import tool, ToolRuntime
from vector_store import vector_storage
from langgraph.graph import MessagesState, END
from patent_miner_classes import retrievalstate, metadatastate


## Route function ##
def routing_function(state: retrievalstate):
    return "metadatafilter" if state["retrieval_required"] else "answer"