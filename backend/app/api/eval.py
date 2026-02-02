from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile

from backend.app.scripts.retrieve_rerank import evaluate


router = APIRouter(prefix="/api", tags=["eval"])


def _require_api_key(api_key: Optional[str]) -> None:
    expected = os.environ.get("QRELS_API_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="QRELS_API_KEY is not configured on the server.")
    if not api_key or api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key.")


def _write_upload(upload: UploadFile, path: Path) -> None:
    content = upload.file.read()
    path.write_bytes(content)


def _write_queries_from_qrels(qrels_path: Path, queries_path: Path) -> int:
    seen = set()
    out = []
    for line in qrels_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        q = row.get("query")
        if not q or q in seen:
            continue
        seen.add(q)
        out.append({"query": q})
    with queries_path.open("w", encoding="utf-8") as f:
        for row in out:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(out)


@router.post("/qrels-eval")
async def qrels_eval(
    api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    qrels: UploadFile = File(...),
    queries: UploadFile | None = File(default=None),
    shard: str = Form(default="768_f16"),
    limit: int = Form(default=200),
    rerank_k: int = Form(default=100),
    filter_missing_qrels: bool = Form(default=True),
):
    _require_api_key(api_key)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        qrels_path = tmpdir_path / "qrels.jsonl"
        _write_upload(qrels, qrels_path)

        if queries is not None:
            queries_path = tmpdir_path / "queries.jsonl"
            _write_upload(queries, queries_path)
            derived_count = None
        else:
            queries_path = tmpdir_path / "queries.jsonl"
            derived_count = _write_queries_from_qrels(qrels_path, queries_path)

        metrics = evaluate(
            queries_path,
            qrels_path,
            shard=shard,
            limit=limit,
            rerank_k=rerank_k,
            filter_missing_qrels=filter_missing_qrels,
        )

        metrics_csv = (
            "precision@10,recall@10,ndcg@10,mrr@10\n"
            f"{metrics.get('precision@10', 0.0)},"
            f"{metrics.get('recall@10', 0.0)},"
            f"{metrics.get('ndcg@10', 0.0)},"
            f"{metrics.get('mrr@10', 0.0)}\n"
        )

        return {
            "metrics": metrics,
            "metrics_csv": metrics_csv,
            "shard": shard,
            "limit": limit,
            "rerank_k": rerank_k,
            "filter_missing_qrels": filter_missing_qrels,
            "queries_derived_from_qrels": derived_count,
        }
