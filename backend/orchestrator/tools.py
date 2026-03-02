from patent_miner_classes import retrievalstate

def routing_function(state: retrievalstate):
    return "retrieve" if state["retrieval_required"] else "answer"