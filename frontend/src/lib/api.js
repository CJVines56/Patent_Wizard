// Resolve the API base URL from Vite env (defined in frontend/.env)
// Fallback to local FastAPI dev server if env is missing.
export const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

// Call the orchestrator-backed search endpoint with RAG enabled.
// - query: user-entered string
// - opts.k: number of cited results to return (fed to LLM)
// - opts.k_extra: additional results not fed to the LLM
export async function orchestratorSearch(query, opts = {}) {
  // Build absolute URL like: http://localhost:8000/api/search?q=...&rag=true
  const url = new URL(API_BASE + "/search");
  url.searchParams.set("q", query);            // user query
  url.searchParams.set("rag", String(opts.rag ?? true));

  // Pass known and future tuning knobs through to the API.
  const passthroughKeys = [
    "k",
    "k_extra",
    "alpha",
    "retrieval_k",
    "retrieval_candidates",
    "rerank_k",
    "rerank_shard",
  ];
  passthroughKeys.forEach((key) => {
    const value = opts[key];
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
