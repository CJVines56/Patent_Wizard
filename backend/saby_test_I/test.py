from typing import List, Dict, Any

thisdict =	{
  "brand": "Ford",
  "model": "Mustang",
  "year": "Chichi"
}
retrieved_patents: List[Dict[str, Any]] = [{"text": thisdict[c]} for c in thisdict]

print(retrieved_patents)
