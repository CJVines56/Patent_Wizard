from typing import List, Dict, Any, Optional, TypedDict
from langgraph.graph import MessagesState


class Patent_Miner_State(MessagesState):
    joined_context: Optional[str] = None
    contexts: Optional[List[Dict[str, Any]]] = None


class retrievalstate(TypedDict):
    retrieval_required: Optional[bool]
    routing_decision_raw: Optional[str]