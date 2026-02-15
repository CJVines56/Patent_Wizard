"""
Simple Tkinter GUI for retrieval + reranking and doc_id lookup.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from pathlib import Path

from backend.app.scripts.retrieve_rerank import (
    SHARD_TO_PATH,
    evaluate,
    evaluate_sweep,
    lookup_patent,
    rerank_with_lmdb,
    retrieve_claims,
)


def _format_hits(hits, k: int = 10) -> str:
    lines: list[str] = []
    for i, h in enumerate(hits[:k], start=1):
        score = f"{h.score:.3f}" if h.score is not None else "-"
        dist = f"{h.distance:.4f}" if h.distance is not None else "-"
        lines.append(
            f"{i:02d} score={score} dist={dist} claim_id={h.claim_id} doc_id={h.doc_id} type={h.claim_type}"
        )
        lines.append(f"    {h.text[:300]}")
        lines.append("")
    return "\n".join(lines)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Patent Retrieval + Rerank")
        self.geometry("980x700")

        self.query_var = tk.StringVar()
        self.doc_id_var = tk.StringVar()
        self.limit_var = tk.StringVar(value="200")
        self.rerank_var = tk.StringVar(value="100")
        self.retrieve_shard_var = tk.StringVar(value="768_f16")
        self.rerank_shard_var = tk.StringVar(value="768_f16")
        self.queries_path_var = tk.StringVar(value="backend/validation/queries.jsonl")
        self.qrels_path_var = tk.StringVar(value="backend/validation/qrels.jsonl")
        self.metrics_csv_var = tk.StringVar(value="backend/validation/metrics.csv")
        self.use_csv_var = tk.BooleanVar(value=False)

        self._build()

    def _build(self):
        pad = {"padx": 8, "pady": 6}

        top = ttk.Frame(self)
        top.pack(fill=tk.X, **pad)

        ttk.Label(top, text="Query").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.query_var, width=80).grid(
            row=0, column=1, columnspan=5, sticky="ew", **pad
        )

        ttk.Label(top, text="Retrieve Shard").grid(row=1, column=0, sticky="w")
        retrieve_box = ttk.Combobox(
            top,
            textvariable=self.retrieve_shard_var,
            values=sorted(SHARD_TO_PATH.keys()),
            state="readonly",
            width=12,
        )
        retrieve_box.grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(top, text="Rerank Shard").grid(row=1, column=2, sticky="e")
        rerank_box = ttk.Combobox(
            top,
            textvariable=self.rerank_shard_var,
            values=sorted(SHARD_TO_PATH.keys()),
            state="readonly",
            width=12,
        )
        rerank_box.grid(row=1, column=3, sticky="w", **pad)

        ttk.Label(top, text="Limit").grid(row=1, column=4, sticky="e")
        ttk.Entry(top, textvariable=self.limit_var, width=8).grid(
            row=1, column=5, sticky="w", **pad
        )

        ttk.Label(top, text="Rerank K").grid(row=1, column=6, sticky="e")
        ttk.Entry(top, textvariable=self.rerank_var, width=8).grid(
            row=1, column=7, sticky="w", **pad
        )

        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, **pad)
        ttk.Button(btns, text="Retrieve + Rerank", command=self.on_search).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(btns, text="Run Qrels Eval", command=self.on_eval).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(btns, text="Run Shard Sweep", command=self.on_sweep).pack(
            side=tk.LEFT, padx=6
        )

        doc = ttk.Frame(self)
        doc.pack(fill=tk.X, **pad)
        ttk.Label(doc, text="Patent doc_id").pack(side=tk.LEFT)
        ttk.Entry(doc, textvariable=self.doc_id_var, width=24).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(doc, text="Lookup Patent", command=self.on_lookup).pack(
            side=tk.LEFT, padx=6
        )

        eval_frame = ttk.Frame(self)
        eval_frame.pack(fill=tk.X, **pad)
        ttk.Label(eval_frame, text="Queries").grid(row=0, column=0, sticky="w")
        ttk.Entry(eval_frame, textvariable=self.queries_path_var, width=60).grid(
            row=0, column=1, sticky="ew", **pad
        )
        ttk.Button(eval_frame, text="Browse", command=self.on_browse_queries).grid(
            row=0, column=2, sticky="w", **pad
        )

        ttk.Label(eval_frame, text="Qrels").grid(row=1, column=0, sticky="w")
        ttk.Entry(eval_frame, textvariable=self.qrels_path_var, width=60).grid(
            row=1, column=1, sticky="ew", **pad
        )
        ttk.Button(eval_frame, text="Browse", command=self.on_browse_qrels).grid(
            row=1, column=2, sticky="w", **pad
        )

        ttk.Checkbutton(
            eval_frame,
            text="Save metrics CSV",
            variable=self.use_csv_var,
        ).grid(row=2, column=0, sticky="w")
        ttk.Entry(eval_frame, textvariable=self.metrics_csv_var, width=60).grid(
            row=2, column=1, sticky="ew", **pad
        )

        self.status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status, anchor="w").pack(
            fill=tk.X, padx=10, pady=(0, 4)
        )

        self.text = tk.Text(self, wrap=tk.WORD)
        self.text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.text.insert("1.0", "Run a query or lookup a patent by doc_id.")

    def _set_output(self, content: str):
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", content)

    def on_search(self):
        query = (self.query_var.get() or "").strip()
        if not query:
            messagebox.showwarning("Missing query", "Enter a query first.")
            return
        try:
            limit = max(1, int(self.limit_var.get()))
            rerank_k = max(1, int(self.rerank_var.get()))
        except ValueError:
            messagebox.showerror("Invalid numbers", "Limit and Rerank K must be integers.")
            return
        retrieve_shard = self.retrieve_shard_var.get()
        rerank_shard = self.rerank_shard_var.get()
        self.status.set("Retrieving from Weaviate...")
        self.update_idletasks()
        try:
            hits = retrieve_claims(query, limit=limit, shard=retrieve_shard)
            self.status.set(f"Retrieved {len(hits)}. Reranking with {rerank_shard}...")
            self.update_idletasks()
            reranked = rerank_with_lmdb(hits, query, shard=rerank_shard, rerank_k=rerank_k)
            self._set_output(_format_hits(reranked, k=10))
            self.status.set(
                f"Done. Retrieved={len(hits)} reranked_top={min(rerank_k, len(hits))} "
                f"retrieve={retrieve_shard} rerank={rerank_shard}"
            )
        except Exception as e:
            self.status.set("Error")
            messagebox.showerror("Search failed", str(e))

    def on_lookup(self):
        doc_id = (self.doc_id_var.get() or "").strip()
        if not doc_id:
            messagebox.showwarning("Missing doc_id", "Enter a patent doc_id first.")
            return
        self.status.set(f"Looking up doc_id={doc_id}...")
        self.update_idletasks()
        try:
            hits = lookup_patent(doc_id)
            self._set_output(_format_hits(hits, k=min(20, len(hits))))
            self.status.set(f"Found {len(hits)} claims for doc_id={doc_id}")
        except Exception as e:
            self.status.set("Error")
            messagebox.showerror("Lookup failed", str(e))

    def on_browse_queries(self):
        path = filedialog.askopenfilename(title="Select queries.jsonl", filetypes=[("JSONL", "*.jsonl"), ("All", "*.*")])
        if path:
            self.queries_path_var.set(path)

    def on_browse_qrels(self):
        path = filedialog.askopenfilename(title="Select qrels.jsonl", filetypes=[("JSONL", "*.jsonl"), ("All", "*.*")])
        if path:
            self.qrels_path_var.set(path)

    def on_eval(self):
        queries_path = (self.queries_path_var.get() or "").strip()
        qrels_path = (self.qrels_path_var.get() or "").strip()
        if not queries_path or not qrels_path:
            messagebox.showwarning("Missing files", "Select both queries and qrels JSONL files.")
            return
        try:
            limit = max(1, int(self.limit_var.get()))
            rerank_k = max(1, int(self.rerank_var.get()))
        except ValueError:
            messagebox.showerror("Invalid numbers", "Limit and Rerank K must be integers.")
            return
        retrieve_shard = self.retrieve_shard_var.get()
        rerank_shard = self.rerank_shard_var.get()
        self.status.set("Running qrels evaluation...")
        self.update_idletasks()
        try:
            scores = evaluate(
                Path(queries_path),
                Path(qrels_path),
                retrieve_shard=retrieve_shard,
                rerank_shard=rerank_shard,
                limit=limit,
                rerank_k=rerank_k,
            )
            lines = [
                "Qrels evaluation complete:",
                f"precision@10: {scores.get('precision@10', 0.0):.4f}",
                f"recall@10:    {scores.get('recall@10', 0.0):.4f}",
                f"ndcg@10:      {scores.get('ndcg@10', 0.0):.4f}",
                f"mrr@10:       {scores.get('mrr@10', 0.0):.4f}",
            ]
            self._set_output("\n".join(lines))
            if self.use_csv_var.get():
                csv_path = Path(self.metrics_csv_var.get())
                csv_path.parent.mkdir(parents=True, exist_ok=True)
                with csv_path.open("w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["precision@10", "recall@10", "ndcg@10", "mrr@10"])
                    writer.writerow(
                        [
                            scores.get("precision@10", 0.0),
                            scores.get("recall@10", 0.0),
                            scores.get("ndcg@10", 0.0),
                            scores.get("mrr@10", 0.0),
                        ]
                    )
                lines.append(f"Saved metrics CSV to {csv_path}")
                self._set_output("\n".join(lines))
            self.status.set("Eval complete")
        except Exception as e:
            self.status.set("Error")
            messagebox.showerror("Eval failed", str(e))

    def on_sweep(self):
        queries_path = (self.queries_path_var.get() or "").strip()
        qrels_path = (self.qrels_path_var.get() or "").strip()
        if not queries_path or not qrels_path:
            messagebox.showwarning("Missing files", "Select both queries and qrels JSONL files.")
            return
        try:
            limit = max(1, int(self.limit_var.get()))
            rerank_k = max(1, int(self.rerank_var.get()))
        except ValueError:
            messagebox.showerror("Invalid numbers", "Limit and Rerank K must be integers.")
            return
        retrieve_shard = self.retrieve_shard_var.get()
        csv_path = Path(self.metrics_csv_var.get() or "backend/validation/sweep_metrics.csv")
        self.status.set("Running shard sweep...")
        self.update_idletasks()
        try:
            results = evaluate_sweep(
                Path(queries_path),
                Path(qrels_path),
                retrieve_shard=retrieve_shard,
                rerank_shards=sorted(SHARD_TO_PATH.keys()),
                limit=limit,
                rerank_k=rerank_k,
            )
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            with csv_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["rerank_shard", "precision@10", "recall@10", "ndcg@10", "mrr@10"])
                for row in results:
                    writer.writerow(
                        [
                            row.get("rerank_shard"),
                            row.get("precision@10", 0.0),
                            row.get("recall@10", 0.0),
                            row.get("ndcg@10", 0.0),
                            row.get("mrr@10", 0.0),
                        ]
                    )
            lines = ["Shard sweep complete:"]
            for row in results:
                lines.append(
                    f"{row.get('rerank_shard')}: "
                    f"p@10={row.get('precision@10', 0.0):.4f} "
                    f"r@10={row.get('recall@10', 0.0):.4f} "
                    f"ndcg@10={row.get('ndcg@10', 0.0):.4f} "
                    f"mrr@10={row.get('mrr@10', 0.0):.4f}"
                )
            lines.append(f"Saved sweep CSV to {csv_path}")
            self._set_output("\n".join(lines))
            self.status.set("Sweep complete")
        except Exception as e:
            self.status.set("Error")
            messagebox.showerror("Sweep failed", str(e))


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
