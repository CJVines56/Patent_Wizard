from typing import Any, Dict, List, Optional
from langchain.tools import tool
from vector_store import vector_storage
from langgraph.graph import MessagesState, END
from patent_miner_classes import retrievalstate


## Retrieval tool ##

@tool(response_format='content')
def retrieve_context(query: str, where_filter: Optional[Dict[str, Any]] = None):
    """Retrieve information to help answer a query, optionally using metadata filters.

    Args:
        query: Search terms to look for
        where_filter: Filter for database search
    """



    search_kwargs = {"k": 5}
    if where_filter:
        # Chroma / langchain-chroma supports `filter` in search_kwargs in many setups.
        # If your environment expects `where`, change the key accordingly.
        search_kwargs["filter"] = where_filter
    retriever = vector_storage.as_retriever(search_type="similarity", 
                                            search_kwargs=search_kwargs,)
    
    context = retriever.invoke(query)
    
    chunks: List[Dict[str, Any]] = [
        {
            "text": d.page_content,
            "metadata": dict(d.metadata) if d.metadata else {},
        }
        for d in context
    ]

    joined_text = "\n\n".join([c["text"] for c in chunks])

    return {
        "query": query,
        "joined_text": joined_text,
        "chunks": chunks,
    }

retriever_tool = retrieve_context


def route_from_query(state: retrievalstate):
    return "metadatafilter" if state[retrieval_required] else END