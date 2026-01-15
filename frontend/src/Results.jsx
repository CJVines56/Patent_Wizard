// Results page
// - Reads the `q` param from the URL
// - Calls the API with RAG enabled
// - Shows answer on the left and a scrollable results column on the right
import { useEffect, useMemo, useState } from "react";
import SearchBar from "./components/SearchBar.jsx";
import { orchestratorSearch } from "./lib/api.js";

// Helper to read the 'q' query param from the current URL
function getQ() {
  return new URLSearchParams(window.location.search).get("q") || "";
}

export default function Results() {
  const [q, setQ] = useState(getQ());       // current query from the URL
  const [loading, setLoading] = useState(false); // fetch-in-progress flag
  const [error, setError] = useState(null);      // error message to show above cards
  const [result, setResult] = useState(null);    // API response
  const [modalFig, setModalFig] = useState(null); // full-size figure modal

  // Watch for browser navigation (Back/Forward) and update query state
  useEffect(() => {
    const onPop = () => setQ(getQ());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  // On query change, (re)fetch results from the API
  // When the query (`q`) changes:
  // - reset local UI state
  // - call the orchestrator search with top-K settings
  // - guard every state update with `cancelled` so unmounted components aren't updated
  useEffect(() => {
    let cancelled = false;
    async function run() {
      if (!q) return;           // don’t call API without a query
      setLoading(true);
      setError(null);
      setResult(null);
      try {
        const K = 5;           // cited results (fed to LLM)
        const data = await orchestratorSearch(q, { k: K, k_extra: K });
        if (!cancelled) setResult(data);
      } catch (e) {
        if (!cancelled) setError(e?.message || String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    run();
    return () => {
      cancelled = true;        // guard against state updates after unmount
    };
  }, [q]);

  // Close modal on Escape
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") setModalFig(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const figureEntries = useMemo(() => {
    if (!result?.cited_items) return [];
    const entries = [];
    result.cited_items.forEach((item, docIdx) => {
      (item.fig_images || []).forEach((img, figIdx) => {
        if (!img?.data_b64) {
          return;
        }
        const mediaType = img.media_type || "image/png";
        entries.push({
          key: `${item.doc_id || docIdx}-${figIdx}`,
          src: `data:${mediaType};base64,${img.data_b64}`,
          label:
            img.file ||
            (img.fig_ids && img.fig_ids.length ? img.fig_ids[0] : img.num
              ? `Figure ${img.num}`
              : `Figure ${figIdx + 1}`),
          docTitle: item.title || item.doc_id || "Patent",
        });
      });
    });
    return entries.slice(0, 6);
  }, [result]);

  // Search from this page: push a new URL and refresh local `q`
  function handleSearch(nextQ) {
    const url = "/search?" + new URLSearchParams({ q: nextQ }).toString();
    window.history.pushState({}, "", url);
    setQ(nextQ);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }

  if (!q) {
    // no query provided; bounce home
    window.history.replaceState({}, "", "/");
    window.dispatchEvent(new PopStateEvent("popstate"));
    return null;
  }

  return (
    <>
      <div className="min-h-dvh bg-gradient-to-r from-[#500000] via-orange-500 to-[#500000] text-white px-6 py-6 overflow-y-auto">
        <div className="max-w-6xl mx-auto pb-16">

        {/* Lightweight status area above the content */}
        {loading && <p className="text-white/80">Searching…</p>}
        {error && (
          <div className="p-3 rounded bg-red-500/20 border border-red-300/40 text-red-100">{error}</div>
        )}

        {result && (
          <div className="relative">
            {/* Left column content */}
            <div className="relative w-full max-w-4xl px-4 md:px-0 z-0 flex flex-col gap-4 pb-12 mx-auto">
              {figureEntries.length > 0 && (
                <div className="bg-white/10 border border-white/20 rounded-lg p-4 md:p-5 shadow-lg shadow-black/10 backdrop-blur-sm">
                  <div className="mb-2">
                    <p className="text-sm text-white/70">Referenced Figures</p>
                    <p className="text-xs text-white/60">
                      Pulled from retrieved patent chunks
                    </p>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {figureEntries.map((fig) => (
                      <figure
                        key={fig.key}
                        className="bg-black/20 rounded-md overflow-hidden border border-white/10 transition-transform duration-150 hover:scale-105 cursor-zoom-in"
                        onClick={() => setModalFig(fig)}
                      >
                        <img
                          src={fig.src}
                          alt={fig.label}
                          className="w-full h-32 object-contain bg-white"
                        />
                        <figcaption className="p-2 text-xs text-white/80">
                          <p className="font-semibold truncate">{fig.label}</p>
                          <p className="text-white/60 truncate">{fig.docTitle}</p>
                        </figcaption>
                      </figure>
                    ))}
                  </div>
                </div>
              )}
              <div className="bg-white/10 border border-white/20 rounded-lg p-6 md:p-8">
                <div className="mb-3">
                  <p className="text-sm text-white/70">Query</p>
                  <p className="text-lg">{q}</p>
                </div>
                {result.answer && (
                  <div className="mb-6">
                    <p className="text-sm text-white/70">Answer (RAG)</p>
                    <div className="whitespace-pre-wrap bg-black/30 p-4 rounded text-white/90 text-base leading-relaxed font-sans">{result.answer}</div>
                  </div>
                )}
                {/* Place the search bar on the card, beneath the RAG answer */}
                <SearchBar onSearch={handleSearch} placeholder="Refine your query..." />
              </div>
            </div>

            {/* Right: fixed, full-height scrollable results panel at the very edge */}
            <aside className="hidden md:block fixed right-0 top-0 h-screen w-80 lg:w-96 overflow-y-auto z-10 bg-white/10 border-l border-white/20">
              <div className="p-4 pt-24 text-base">
                <p className="text-base text-white/70 mb-2">Results</p>
                <p className="text-sm text-white/60">Cited Patents</p>
                {result.cited_items?.map((it, idx) => {
                  const kind = (it.kind || "").trim();
                  const gpUrl = it.doc_id
                    ? `https://patents.google.com/patent/US${it.doc_id}${kind ? kind : ""}/en?oq=${it.doc_id}`
                    : null;
                  const fmtDate = (d) => {
                    if (!d) return d;
                    const s = String(d);
                    return /^\d{8}$/.test(s)
                      ? `${s.slice(0,4)}/${s.slice(4,6)}/${s.slice(6,8)}`
                      : s;
                  };
                  return (
                    <div key={`cited-${it.id}`} id={`ref-${idx + 1}`} className="bg-black/30 p-3 rounded mt-2">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="font-semibold text-base">[{idx + 1}] {it.title}</p>
                          {it.snippet && (
                            <p className="text-sm text-white/70 mt-1 line-clamp-3">{it.snippet}</p>
                          )}
                          <div className="mt-2 text-sm text-white/80 space-y-1">
                            <p><span className="text-white/60">Title:</span> {it.title}</p>
                            {it.authors ? (
                              <p><span className="text-white/60">Authors:</span> {it.authors}</p>
                            ) : null}
                            {it.classification ? (
                              <p><span className="text-white/60">Classification:</span> {it.classification}</p>
                            ) : null}
                            {it.filing_date ? (
                              <p><span className="text-white/60">Filing Date:</span> {fmtDate(it.filing_date)}</p>
                            ) : null}
                            {it.kind ? (
                              <p><span className="text-white/60">Kind:</span> {it.kind}</p>
                            ) : null}
                            {it.doc_id ? (
                              <p><span className="text-white/60">doc_id:</span> {it.doc_id}</p>
                            ) : null}
                            {gpUrl ? (
                              <p>
                                <a
                                  href={gpUrl}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-blue-200 hover:text-blue-100 underline"
                                >
                                  Google Patents full text
                                </a>
                              </p>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}

                {result.other_items?.length ? (
                  <>
                    <p className="text-xs text-white/60 mt-4">More Results</p>
                    {result.other_items.map((it, idx) => {
                      const kind = (it.kind || "").trim();
                      const gpUrl = it.doc_id
                        ? `https://patents.google.com/patent/US${it.doc_id}${kind ? kind : ""}/en?oq=${it.doc_id}`
                        : null;
                      const fmtDate = (d) => {
                        if (!d) return d;
                        const s = String(d);
                        return /^\d{8}$/.test(s)
                          ? `${s.slice(0,4)}/${s.slice(4,6)}/${s.slice(6,8)}`
                          : s;
                      };
                      return (
                        <div key={`other-${it.id}`} className="bg-black/30 p-3 rounded mt-2">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="font-semibold">[{(result.cited_items?.length || 0) + idx + 1}] {it.title}</p>
                              {it.snippet && (
                                <p className="text-xs text-white/70 mt-1 line-clamp-3">{it.snippet}</p>
                              )}
                              <div className="mt-2 text-xs text-white/80 space-y-1">
                                <p><span className="text-white/60">Title:</span> {it.title}</p>
                                {it.authors ? (
                                  <p><span className="text-white/60">Authors:</span> {it.authors}</p>
                                ) : null}
                                {it.classification ? (
                                  <p><span className="text-white/60">Classification:</span> {it.classification}</p>
                                ) : null}
                                {it.filing_date ? (
                                  <p><span className="text-white/60">Filing Date:</span> {fmtDate(it.filing_date)}</p>
                                ) : null}
                                {it.kind ? (
                                  <p><span className="text-white/60">Kind:</span> {it.kind}</p>
                                ) : null}
                                {it.doc_id ? (
                                  <p><span className="text-white/60">doc_id:</span> {it.doc_id}</p>
                                ) : null}
                                {gpUrl ? (
                                  <p>
                                    <a
                                      href={gpUrl}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="text-blue-200 hover:text-blue-100 underline"
                                    >
                                      Google Patents full text
                                    </a>
                                  </p>
                                ) : null}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </>
                ) : null}
              </div>
            </aside>
          </div>
        )}
        </div>
      </div>

      {modalFig && (
        <div
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center px-4"
          onClick={() => setModalFig(null)}
        >
          <div
            className="bg-black rounded-lg shadow-2xl border border-white/20 max-w-5xl w-full max-h-[90vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center p-3 border-b border-white/10 text-white/80 text-sm">
              <div>
                <p className="font-semibold">{modalFig.label}</p>
                <p className="text-white/60">{modalFig.docTitle}</p>
              </div>
              <button
                onClick={() => setModalFig(null)}
                className="px-3 py-1 rounded bg-white/10 hover:bg-white/20 text-white text-xs"
              >
                Close
              </button>
            </div>
            <div className="bg-white flex items-center justify-center">
              <img
                src={modalFig.src}
                alt={modalFig.label}
                className="max-h-[80vh] object-contain w-full"
              />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
