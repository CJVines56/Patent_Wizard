from typing import List, Dict, Any, Optional, TypedDict
from langgraph.graph import MessagesState


class Patent_Miner_State(MessagesState):
    # in Patent_Miner_State definition
    question: Optional[str] = None
    retrieved_context: Optional[List[Dict[str, Any]]] = None
    retrieved_patents: Optional[List[Dict[str, Any]]] = None
    joined_patents: Optional[List[Dict[str, str]]] = None
    answer: Optional[str] = None

class retrievalstate(TypedDict):
    retrieval_required: Optional[bool]
    routing_decision_raw: Optional[str]