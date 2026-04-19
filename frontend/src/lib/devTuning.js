export const DEFAULT_TUNING = Object.freeze({
  k: 10,
  k_extra: 10,
  alpha: 0.5,
  retrieval_candidates: 400,
  rerank_k: 200,
});

export const DEV_TUNING_VISIBLE = import.meta.env.VITE_ENABLE_SEARCH_KNOBS !== "false";

const STORAGE_KEY = "patent_miner_dev_tuning_v2";

function clampInt(value, fallback, min, max) {
  const n = Number.parseInt(String(value), 10);
  if (!Number.isFinite(n)) return fallback;
  return Math.min(max, Math.max(min, n));
}

function clampFloat(value, fallback, min, max) {
  const n = Number.parseFloat(String(value));
  if (!Number.isFinite(n)) return fallback;
  return Math.min(max, Math.max(min, n));
}

export function normalizeTuning(raw = {}) {
  const k = clampInt(raw.k, DEFAULT_TUNING.k, 1, 50);
  const kExtra = clampInt(raw.k_extra, DEFAULT_TUNING.k_extra, 0, 100);
  const alpha = clampFloat(raw.alpha, DEFAULT_TUNING.alpha, 0, 1);
  const retrievalCandidates = Math.max(
    k,
    clampInt(raw.retrieval_candidates, DEFAULT_TUNING.retrieval_candidates, 5, 500),
  );
  const rerankK = Math.max(
    k,
    clampInt(raw.rerank_k, DEFAULT_TUNING.rerank_k, 1, 500),
  );
  return {
    k,
    k_extra: kExtra,
    alpha: Number(alpha.toFixed(2)),
    retrieval_candidates: retrievalCandidates,
    rerank_k: rerankK,
  };
}

export function loadStoredTuning() {
  if (typeof window === "undefined") return DEFAULT_TUNING;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_TUNING;
    const parsed = JSON.parse(raw);
    return normalizeTuning(parsed);
  } catch {
    return DEFAULT_TUNING;
  }
}

export function saveStoredTuning(tuning) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(normalizeTuning(tuning)));
  } catch {
    // Ignore storage failures in restricted browser contexts.
  }
}
