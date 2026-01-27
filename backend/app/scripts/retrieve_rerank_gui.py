"""
Simple Tkinter GUI for retrieval + reranking and doc_id lookup.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from backend.app.scripts.retrieve_rerank import (
    SHARD_TO_PATH,
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
        self.shard_var = tk.StringVar(value="768_f16")

        self._build()

    def _build(self):
        pad = {"padx": 8, "pady": 6}

        top = ttk.Frame(self)
        top.pack(fill=tk.X, **pad)

        ttk.Label(top, text="Query").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.query_var, width=80).grid(
            row=0, column=1, columnspan=5, sticky="ew", **pad
        )

        ttk.Label(top, text="Shard").grid(row=1, column=0, sticky="w")
        shard_box = ttk.Combobox(
            top,
            textvariable=self.shard_var,
            values=sorted(SHARD_TO_PATH.keys()),
            state="readonly",
            width=12,
        )
        shard_box.grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(top, text="Limit").grid(row=1, column=2, sticky="e")
        ttk.Entry(top, textvariable=self.limit_var, width=8).grid(
            row=1, column=3, sticky="w", **pad
        )

        ttk.Label(top, text="Rerank K").grid(row=1, column=4, sticky="e")
        ttk.Entry(top, textvariable=self.rerank_var, width=8).grid(
            row=1, column=5, sticky="w", **pad
        )

        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, **pad)
        ttk.Button(btns, text="Retrieve + Rerank", command=self.on_search).pack(
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
        shard = self.shard_var.get()
        self.status.set("Retrieving from Weaviate...")
        self.update_idletasks()
        try:
            hits = retrieve_claims(query, limit=limit)
            self.status.set(f"Retrieved {len(hits)}. Reranking with {shard}...")
            self.update_idletasks()
            reranked = rerank_with_lmdb(hits, query, shard=shard, rerank_k=rerank_k)
            self._set_output(_format_hits(reranked, k=10))
            self.status.set(
                f"Done. Retrieved={len(hits)} reranked_top={min(rerank_k, len(hits))} shard={shard}"
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


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()

