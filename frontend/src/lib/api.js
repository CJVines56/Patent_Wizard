// Resolve the API base URL from Vite env (defined in frontend/.env)
// Fallback to local FastAPI dev server if env is missing.
export const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
export const PATENT_SEARCH_MINIMUMS = Object.freeze({
  retrieval_candidates: 800,
  rerank_k: 400,
});

export function normalizeSearchScope(value) {
  return String(value || "claim").trim().toLowerCase() === "patent" ? "patent" : "claim";
}

function withSearchScopeDefaults(opts = {}) {
  const searchScope = normalizeSearchScope(opts.search_scope ?? opts.scope);
  const scoped = {
    ...opts,
    search_scope: searchScope,
  };
  if (searchScope !== "patent") {
    return scoped;
  }

  const retrievalCandidates = Number.parseInt(String(scoped.retrieval_candidates ?? 0), 10);
  const rerankK = Number.parseInt(String(scoped.rerank_k ?? 0), 10);
  return {
    ...scoped,
    rag: false,
    retrieval_candidates: Math.max(
      Number.isFinite(retrievalCandidates) ? retrievalCandidates : 0,
      PATENT_SEARCH_MINIMUMS.retrieval_candidates,
    ),
    rerank_k: Math.max(
      Number.isFinite(rerankK) ? rerankK : 0,
      PATENT_SEARCH_MINIMUMS.rerank_k,
    ),
  };
}

// Call the orchestrator-backed search endpoint with RAG enabled.
// - query: user-entered string
// - opts.k: number of cited results to return (fed to LLM)
// - opts.k_extra: additional results not fed to the LLM
export async function orchestratorSearch(query, opts = {}) {
  const scopedOpts = withSearchScopeDefaults(opts);
  // Build absolute URL like: http://localhost:8000/api/search?q=...&rag=true
  const url = new URL(API_BASE + "/search");
  url.searchParams.set("q", query);            // user query
  url.searchParams.set("rag", String(scopedOpts.rag ?? true));

  // Pass known and future tuning knobs through to the API.
  const passthroughKeys = [
    "search_scope",
    "k",
    "k_extra",
    "alpha",
    "retrieval_k",
    "retrieval_candidates",
    "rerank_k",
    "rerank_shard",
    "filter_doc_id",
    "filter_claim_type",
    "filter_kind",
    "filter_date_from",
    "filter_date_to",
  ];
  passthroughKeys.forEach((key) => {
    const value = scopedOpts[key];
    if (value != null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });

  // Helpful debug to see exactly what URL is requested
  console.log("[orchestratorSearch] GET", url.toString());

  // Fire the GET request
  const res = await fetch(url.toString());
  if (!res.ok) {
    // Surface server error body in the thrown message for easier debugging
    const body = await res.text().catch(() => "");
    throw new Error(`GET ${url} failed: ${res.status} ${body}`);
  }
  // Parse and return JSON response
  return res.json();
}
