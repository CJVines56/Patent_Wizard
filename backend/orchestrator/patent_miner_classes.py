from typing import List, Dict, Any, Optional, TypedDict
from langgraph.graph import MessagesState
from langmem.short_term import RunningSummary


class Patent_Miner_State(MessagesState):
    # in Patent_Miner_State definition 
    context: dict[str, RunningSummary] = None
    joined_context: Optional[str] = None
    retrieved_context: Optional[List[Dict[str, Any]]] = None


class retrievalstate(TypedDict):
    retrieval_required: Optional[bool]
    routing_decision_raw: Optional[str]