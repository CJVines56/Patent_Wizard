import json
from ragas.metrics.base import Metric
from dataclasses import dataclass
from typing import Dict, Any



## Metadata extraction metric ##

def _normalize_metadata(x: Any) -> Any:
    if x is None:
        return None
    if isinstance(x, (dict, list)):
        return x
    if isinstance(x, str):
        s = x.strip()
        # try JSON, else treat as plain string
        try:
            return json.loads(s)
        except Exception:
            return " ".join(s.split()).lower()
    return str(x)

@dataclass
class MetadataAccuracy(Metric):
    name: str = "metadata_accuracy"

    # Ragas uses these to validate required fields in each row
    required_columns = {"metadata", "expected_metadata"}

    def score(self, row: Dict[str, Any], callbacks=None) -> float:
        pred = _normalize_metadata(row.get("metadata"))
        ref = _normalize_metadata(row.get("expected_metadata"))

        if ref is None:
            return float("nan")  # or 0.0 if you prefer
        return 1.0 if pred == ref else 0.0
    

## Query Cleaning Metric ##

_PROMPT = """You are grading a query-cleaning system.

Original user question:
{unclean_question}

Cleaned query:
{cleaned_query}

Does the cleaned query preserve the original intent and all critical constraints?
Return only one character:
1 = yes (meaning preserved)
0 = no (meaning changed / important detail lost)
"""

@dataclass
class CleanAccuracy(Metric):
    name: str = "clean_accuracy"
    required_columns = {"unclean_question", "cleaned_query"}

    def __init__(self, llm):
        self.llm = llm

    def score(self, row: Dict[str, Any], callbacks=None) -> float:
        prompt = _PROMPT.format(
            unclean_question=row.get("unclean_question", ""),
            cleaned_query=row.get("cleaned_query", ""),
        )
        # ChatOpenAI is already set up in your script [1]
        resp = self.llm.invoke(prompt)
        text = getattr(resp, "content", str(resp)).strip()
        return 1.0 if text.startswith("1") else 0.0