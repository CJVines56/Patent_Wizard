// Results page
// - Reads the `q` param from the URL
// - Calls the API with RAG enabled
// - Shows answer on the left and a scrollable results column on the right
import { useEffect, useMemo, useRef, useState } from "react";
import SearchBar from "./components/SearchBar.jsx";
import SearchScopeSelector from "./components/SearchScopeSelector.jsx";
import DevTuningPanel from "./components/DevTuningPanel.jsx";
import { normalizeSearchScope, orchestratorSearch } from "./lib/api.js";
import {
  DEFAULT_TUNING,
  DEV_TUNING_VISIBLE,
  loadStoredTuning,
  normalizeTuning,
  saveStoredTuning,
} from "./lib/devTuning.js";

// Helper to read the 'q' query param from the current URL
function getQ() {
  return new URLSearchParams(window.location.search).get("q") || "";
}

function getSearchScope() {
  return normalizeSearchScope(new URLSearchParams(window.location.search).get("scope") || "claim");
}

function formatHistorySearchScope(searchScope) {
  return normalizeSearchScope(searchScope) === "patent" ? "Patent" : "Claim";
}

const RESULTS_PANEL_WIDTH_KEY = "patent_miner_results_panel_width_v1";
const RESULTS_PANEL_DEFAULT_WIDTH = 384;
const RESULTS_PANEL_MIN_WIDTH = 220;
const RESULTS_PANEL_MAX_WIDTH = 900;
const EMPTY_FILTERS = Object.freeze({
  dateFrom: "",
  dateTo: "",
  claimType: "",
  docId: "",
});
const CLAIM_TYPE_FILTER_OPTIONS = [
  { value: "", label: "Any" },
  { value: "independent", label: "Independent" },
  { value: "dependent", label: "Dependent" },
];
function clampPanelWidth(width) {
  return Math.min(RESULTS_PANEL_MAX_WIDTH, Math.max(RESULTS_PANEL_MIN_WIDTH, width));
}

function loadResultsPanelWidth() {
  if (typeof window === "undefined") return RESULTS_PANEL_DEFAULT_WIDTH;
  try {
    const raw = window.localStorage.getItem(RESULTS_PANEL_WIDTH_KEY);
    const parsed = Number.parseInt(String(raw), 10);
    if (!Number.isFinite(parsed)) return RESULTS_PANEL_DEFAULT_WIDTH;
    return clampPanelWidth(parsed);
  } catch {
    return RESULTS_PANEL_DEFAULT_WIDTH;
  }
}

function normalizeDateToken(value) {
  if (!value) return "";
  const raw = String(value).trim();
  if (!raw) return "";
  if (/^\d{8}$/.test(raw)) return raw;
  const digits = raw.replace(/\D/g, "");
  if (digits.length >= 8) return digits.slice(0, 8);
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return "";
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}${m}${day}`;
}

function formatAuthors(authors) {
  if (Array.isArray(authors)) return authors.join(", ");
  return String(authors || "");
}

function formatDateDisplay(value) {
  if (!value) return value;
  const s = String(value);
  return /^\d{8}$/.test(s) ? `${s.slice(0, 4)}/${s.slice(4, 6)}/${s.slice(6, 8)}` : s;
}

function googlePatentDocId(docId) {
  return String(docId || "").replace(/^0+(?=\d)/, "");
}

function buildFilterRequestParams(filters) {
  const dateFrom = normalizeDateToken(filters.dateFrom);
  const dateTo = normalizeDateToken(filters.dateTo);
  return {
    filter_doc_id: String(filters.docId || "").trim(),
    filter_claim_type: String(filters.claimType || "").trim(),
    filter_date_from: dateFrom,
    filter_date_to: dateTo,
  };
}

function readSearchFilters() {
  const params = new URLSearchParams(window.location.search);
  return {
    dateFrom: String(params.get("dateFrom") || ""),
    dateTo: String(params.get("dateTo") || ""),
    claimType: String(params.get("claimType") || ""),
    docId: String(params.get("docId") || ""),
  };
}

function cloneFilters(filters) {
  return {
    dateFrom: String(filters?.dateFrom || ""),
    dateTo: String(filters?.dateTo || ""),
    claimType: String(filters?.claimType || ""),
    docId: String(filters?.docId || ""),
  };
}

function hasAnyFilterParams(filterParams) {
  return Object.values(filterParams).some(Boolean);
}

function buildSearchUrl(query, searchScope, filters = EMPTY_FILTERS) {
  const params = new URLSearchParams({
    q: query,
    scope: normalizeSearchScope(searchScope),
  });
  const nextFilters = cloneFilters(filters);
  if (nextFilters.docId.trim()) params.set("docId", nextFilters.docId.trim());
  if (nextFilters.claimType.trim()) params.set("claimType", nextFilters.claimType.trim());
  if (nextFilters.dateFrom) params.set("dateFrom", nextFilters.dateFrom);
  if (nextFilters.dateTo) params.set("dateTo", nextFilters.dateTo);
  return "/search?" + params.toString();
}

function buildMockResult(query, tuning, searchScope) {
  const normalizedScope = normalizeSearchScope(searchScope);
  const cited = Array.from({ length: tuning.k }, (_, i) => ({
    id: normalizedScope === "patent" ? `mock-patent-${i + 1}` : `mock-cited-${i + 1}`,
    title: `Mock Cited Patent ${i + 1}`,
    snippet: `Preview snippet ${i + 1} for "${query}".`,
    doc_id: `12345${i + 1}`,
    claim_id: `C-${i + 1}`,
    claim_type: "independent",
    best_claim_id: `C-${i + 1}`,
    best_claim_type: "independent",
    filing_date: "20240101",
    classification: "G06F",
    authors: "Preview Inventor",
    kind: "A1",
    fig_images: [],
  }));
  const other = Array.from({ length: tuning.k_extra }, (_, i) => ({
    id: `mock-other-${i + 1}`,
    title: `Mock Additional Patent ${i + 1}`,
    snippet: `Additional preview result ${i + 1}.`,
    doc_id: `98765${i + 1}`,
    claim_id: `O-${i + 1}`,
    claim_type: "dependent",
    filing_date: "20230915",
    classification: "H04L",
    authors: "Preview Team",
    kind: "B2",
    fig_images: [],
  }));

  return {
    query,
    total: cited.length + other.length,
    page: 1,
    page_size: tuning.k,
    items: cited,
    cited_items: cited,
    other_items: other,
    mode: "rag",
    search_scope: normalizedScope,
    answer:
      `Preview mode: API unreachable, showing mock data.\n` +
      `${normalizedScope === "patent"
        ? "WIP patent mode ranks patents by their best matching claim."
        : "Claim mode returns individual matching claims."}\n` +
      `Applied tuning -> k=${tuning.k}, k_extra=${tuning.k_extra}, alpha=${tuning.alpha}, ` +
      `retrieval_candidates=${tuning.retrieval_candidates}, rerank_k=${tuning.rerank_k}.`,
  };
}

export default function Results() {
  const [q, setQ] = useState(getQ());       // current query from the URL
  const [searchScope, setSearchScope] = useState(getSearchScope());
  const [submittedSearchScope, setSubmittedSearchScope] = useState(getSearchScope());
  const [loading, setLoading] = useState(false); // fetch-in-progress flag
  const [error, setError] = useState(null);      // error message to show above cards
  const [result, setResult] = useState(null);    // API response
  const [showErrorBar, setShowErrorBar] = useState(true);
  const [showPreviewBar, setShowPreviewBar] = useState(true);
  const [errorBarVisible, setErrorBarVisible] = useState(true);
  const [previewBarVisible, setPreviewBarVisible] = useState(true);
  const [modalFig, setModalFig] = useState(null); // full-size figure modal
  const [historyEntries, setHistoryEntries] = useState([]);
  const [activeHistoryId, setActiveHistoryId] = useState(null);
  const [previewMode, setPreviewMode] = useState(false);
  const [draftTuning, setDraftTuning] = useState(() => loadStoredTuning());
  const [activeTuning, setActiveTuning] = useState(() => loadStoredTuning());
  const [resultsPanelWidth, setResultsPanelWidth] = useState(() => loadResultsPanelWidth());
  const [leftPanelWidth, setLeftPanelWidth] = useState(256);
  const [showScrollToInput, setShowScrollToInput] = useState(false);
  const conversationRef = useRef(null);
  const inputRef = useRef(null);
  const skipNextFetchRef = useRef(false);
    function startLeftPanelResize(e) {
      e.preventDefault();
      const startX = e.clientX;
      const startWidth = leftPanelWidth;
      const minWidth = 80;
      const maxWidth = 700;
      const onMove = (ev) => {
        const delta = ev.clientX - startX;
        const next = Math.min(maxWidth, Math.max(minWidth, startWidth + delta));
        setLeftPanelWidth(next);
      };
      const onUp = () => {
        window.removeEventListener("mousemove", onMove);
        window.removeEventListener("mouseup", onUp);
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
      };
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      window.addEventListener("mousemove", onMove);
      window.addEventListener("mouseup", onUp);
    }
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [filters, setFilters] = useState(() => readSearchFilters());
  const [submittedFilters, setSubmittedFilters] = useState(() => readSearchFilters());
  const isNarrowResultsPanel = resultsPanelWidth < 340;
  const isWideResultsPanel = resultsPanelWidth > 520;
  const activeHistoryEntry = useMemo(
    () => historyEntries.find((entry) => entry.id === activeHistoryId) || null,
    [historyEntries, activeHistoryId],
  );
  const displayQuery = activeHistoryEntry?.query || q;
  const resultSearchScope = result?.search_scope || activeHistoryEntry?.searchScope || submittedSearchScope;
  const isPatentResultScope = resultSearchScope === "patent";
  const normalizedFilters = useMemo(() => ({
    dateFrom: normalizeDateToken(filters.dateFrom),
    dateTo: normalizeDateToken(filters.dateTo),
    claimType: filters.claimType.trim().toLowerCase(),
    docId: filters.docId.trim().toLowerCase(),
  }), [filters]);
  const submittedFilterParams = useMemo(
    () => buildFilterRequestParams(submittedFilters),
    [submittedFilters],
  );
  const draftFilterParams = useMemo(
    () => buildFilterRequestParams(filters),
    [filters],
  );
  const activeFilterCount = useMemo(
    () => Object.values(normalizedFilters).filter(Boolean).length,
    [normalizedFilters],
  );
  const submittedFilterCount = useMemo(
    () => Object.values(submittedFilterParams).filter(Boolean).length,
    [submittedFilterParams],
  );
  const filtersDirty = useMemo(
    () => JSON.stringify(draftFilterParams) !== JSON.stringify(submittedFilterParams),
    [draftFilterParams, submittedFilterParams],
  );

  // Watch for browser navigation (Back/Forward) and update query state
  useEffect(() => {
    const onPop = () => {
      const scope = getSearchScope();
      const urlFilters = readSearchFilters();
      setQ(getQ());
      setSearchScope(scope);
      setSubmittedSearchScope(scope);
      setFilters(urlFilters);
      setSubmittedFilters(urlFilters);
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  useEffect(() => {
    function handleScroll() {
      if (!inputRef.current) return;
      const inputRect = inputRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
      setShowScrollToInput(
        inputRect.top > viewportHeight || inputRect.bottom < 0
      );
    }
    window.addEventListener('scroll', handleScroll);
    window.addEventListener('resize', handleScroll);
    handleScroll();
    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleScroll);
    };
  }, []);

  // On query change, (re)fetch results from the API
  // When the query (`q`) changes:
  // - reset local UI state
  // - call the orchestrator search with top-K settings
  // - guard every state update with `cancelled` so unmounted components aren't updated
  useEffect(() => {
    if (skipNextFetchRef.current) {
      skipNextFetchRef.current = false;
      return;
    }
    let cancelled = false;
    async function run() {
      if (!q) return;
      const hasSubmittedFilters = hasAnyFilterParams(submittedFilterParams);
      setLoading(true);
      setError(null);
      setResult(null);
      setShowErrorBar(true);
      setShowPreviewBar(true);
      setErrorBarVisible(true);
      setPreviewBarVisible(true);
      try {
        const data = await orchestratorSearch(q, {
          ...activeTuning,
          search_scope: submittedSearchScope,
          ...submittedFilterParams,
          rag: hasSubmittedFilters ? false : undefined,
        });
        if (!cancelled) {
          const entry = {
            id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
            query: q,
            searchScope: submittedSearchScope,
            filters: cloneFilters(submittedFilters),
            result: data,
            error: null,
            previewMode: false,
            createdAt: Date.now(),
          };
          setResult(data);
          setError(null);
          setPreviewMode(false);
          setHistoryEntries((prev) => [...prev, entry]);
          setActiveHistoryId(entry.id);
        }
      } catch (e) {
        if (!cancelled) {
          const fallback = buildMockResult(q, normalizeTuning(activeTuning), submittedSearchScope);
          const errorMessage = e?.message || String(e);
          const entry = {
            id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
            query: q,
            searchScope: submittedSearchScope,
            filters: cloneFilters(submittedFilters),
            result: fallback,
            error: errorMessage,
            previewMode: true,
            createdAt: Date.now(),
          };
          setError(errorMessage);
          setResult(fallback);
          setPreviewMode(true);
          setShowErrorBar(false); // Reset first
          setShowPreviewBar(false);
          setTimeout(() => {
            setShowErrorBar(true);
            setShowPreviewBar(true);
          }, 10);
          setHistoryEntries((prev) => [...prev, entry]);
          setActiveHistoryId(entry.id);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    run();
    return () => {
      cancelled = true;
    };
  }, [q, activeTuning, submittedSearchScope, submittedFilterParams, submittedFilters]);

  // Close modal on Escape
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") setModalFig(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(RESULTS_PANEL_WIDTH_KEY, String(resultsPanelWidth));
    } catch {
      // Ignore storage failures and keep in-memory width.
    }
  }, [resultsPanelWidth]);

  const filteredCitedItems = useMemo(() => {
    return result?.cited_items || [];
  }, [result]);

  const filteredOtherItems = useMemo(() => {
    return result?.other_items || [];
  }, [result]);

  const figureEntries = useMemo(() => {
    if (!filteredCitedItems.length) return [];
    const entries = [];
    filteredCitedItems.forEach((item, docIdx) => {
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
  }, [filteredCitedItems]);

  // Search from this page: push a new URL and refresh local `q`
  function submitSearch(nextQ, nextFilters = filters) {
    const normalizedNextFilters = cloneFilters(nextFilters);
    const url = buildSearchUrl(nextQ, searchScope, normalizedNextFilters);
    window.history.pushState({}, "", url);
    setSubmittedSearchScope(searchScope);
    setSubmittedFilters(normalizedNextFilters);
    setFiltersOpen(false);
    setQ(nextQ);
  }

  function handleSearch(nextQ) {
    submitSearch(nextQ, filters);
  }

  function handleSearchScopeChange(nextScope) {
    const normalizedScope = normalizeSearchScope(nextScope);
    if (normalizedScope === searchScope) return;
    setSearchScope(normalizedScope);
  }

  function handleTuningChange(field, value) {
    setDraftTuning((prev) => ({ ...prev, [field]: value }));
  }

  function applyTuning() {
    const normalized = normalizeTuning(draftTuning);
    saveStoredTuning(normalized);
    setDraftTuning(normalized);
    setActiveTuning(normalized);
  }

  function resetTuning() {
    saveStoredTuning(DEFAULT_TUNING);
    setDraftTuning(DEFAULT_TUNING);
    setActiveTuning(DEFAULT_TUNING);
  }

  function handleFilterChange(field, value) {
    setFilters((prev) => ({ ...prev, [field]: value }));
  }

  function applyFilters() {
    setFiltersOpen(false);
  }

  function resetFilters() {
    setFilters(cloneFilters(EMPTY_FILTERS));
  }

  function selectHistoryEntry(entryId) {
    const entry = historyEntries.find((item) => item.id === entryId);
    if (!entry) return;
    const entryScope = normalizeSearchScope(entry.searchScope || entry.result?.search_scope);
    const entryFilters = cloneFilters(entry.filters || EMPTY_FILTERS);
    skipNextFetchRef.current = true;
    setActiveHistoryId(entryId);
    setResult(entry.result);
    setError(entry.error);
    setPreviewMode(Boolean(entry.previewMode));
    setQ(entry.query);
    setSearchScope(entryScope);
    setSubmittedSearchScope(entryScope);
    setFilters(entryFilters);
    setSubmittedFilters(entryFilters);
    window.history.replaceState({}, "", buildSearchUrl(entry.query, entryScope, entryFilters));
  }

  function startResultsPanelResize(e) {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = resultsPanelWidth;

    const onMove = (ev) => {
      const delta = startX - ev.clientX;
      const next = clampPanelWidth(startWidth + delta);
      setResultsPanelWidth(next);
    };
    const onUp = () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };

    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
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
        {DEV_TUNING_VISIBLE && (
          <DevTuningPanel
            draftTuning={draftTuning}
            activeTuning={activeTuning}
            onTuningChange={handleTuningChange}
            onApply={applyTuning}
            onReset={resetTuning}
          />
        )}
        <div className="max-w-6xl mx-auto pb-16">

        {/* Lightweight status area above the content */}
        <div className="flex flex-col gap-2 items-center">
          {loading && <p className="text-white/80">Searching…</p>}
          {isPatentResultScope && (
            <div className="w-full max-w-4xl mx-auto rounded border border-blue-200/40 bg-blue-500/15 px-3 py-2 text-sm text-blue-50">
              Current results are from WIP patent search. Each patent is ranked by its highest-ranked matching claim.
            </div>
          )}
          {error && showErrorBar && (
            <div
              className={`h-12 px-3 rounded bg-red-500/20 border border-red-300/40 text-red-100 flex items-center justify-between transition-opacity duration-300 ${errorBarVisible ? 'opacity-100' : 'opacity-0 pointer-events-none'} w-full max-w-4xl mx-auto`}
            >
              <p className="truncate" title={error}>{error}</p>
              <button
                className="ml-3 text-red-200 hover:text-red-100 text-lg font-bold px-2 py-1 rounded focus:outline-none"
                aria-label="Close error bar"
                onClick={() => {
                  setErrorBarVisible(false);
                  setTimeout(() => setShowErrorBar(false), 300);
                }}
              >
                ×
              </button>
            </div>
          )}
          {previewMode && showPreviewBar && (
            <div
              className={`h-12 px-3 rounded bg-amber-500/20 border border-amber-300/50 text-amber-100 flex items-center justify-between transition-opacity duration-300 ${previewBarVisible ? 'opacity-100' : 'opacity-0 pointer-events-none'} w-full max-w-4xl mx-auto`}
            >
              <p className="truncate">API unavailable. Showing mock preview so you can inspect the page.</p>
              <button
                className="ml-3 text-amber-200 hover:text-amber-100 text-lg font-bold px-2 py-1 rounded focus:outline-none"
                aria-label="Close preview bar"
                onClick={() => {
                  setPreviewBarVisible(false);
                  setTimeout(() => setShowPreviewBar(false), 300);
                }}
              >
                ×
              </button>
            </div>
          )}
        </div>

        {result && (
          <div className="mt-2 relative">
            {/* Left sidebar message history */}
            {historyEntries.length > 0 && (
              <aside
                className="hidden md:block fixed left-0 top-0 h-screen overflow-y-auto z-10 bg-black/30 border-r border-white/20 p-4"
                style={{ width: `${leftPanelWidth}px`, overflowX: 'hidden' }}
              >
                <div
                  className="absolute right-0 top-0 h-full w-3 translate-x-1/2 cursor-col-resize flex items-center justify-center hover:bg-white/10"
                  onMouseDown={startLeftPanelResize}
                  title="Drag to resize left panel"
                >
                  <div className="h-full w-px bg-white/25" />
                </div>
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-sm text-white/80">History</p>
                  <p className="text-xs text-white/60">{historyEntries.length} queries</p>
                </div>
                <div className="space-y-2">
                  {historyEntries.map((entry, idx) => {
                    const isActive = entry.id === activeHistoryId;
                    const entryScopeLabel = formatHistorySearchScope(
                      entry.searchScope || entry.result?.search_scope,
                    );
                    return (
                      <button
                        key={entry.id}
                        type="button"
                        onClick={() => selectHistoryEntry(entry.id)}
                        className={`w-full text-left rounded border border-white/15 p-2 transition-colors ${
                          isActive ? "bg-white" : "bg-black/40 hover:bg-black/50 text-white"
                        }`}
                      >
                        <p className={`text-[11px] ${isActive ? "text-black/60" : "text-white/60"}`}>
                          Query {idx + 1} · {entryScopeLabel}
                        </p>
                        <p
                          title={entry.query}
                          className={`mt-1 text-xs font-semibold break-words line-clamp-2 ${isActive ? "text-black" : "text-white"}`}
                        >
                          {entry.query}
                        </p>
                      </button>
                    );
                  })}
                </div>
              </aside>
            )}
            {/* Center column content */}
            <div className="relative w-full max-w-4xl px-4 md:px-0 z-0 flex flex-col gap-4 pb-12 mx-auto">
              {historyEntries.length > 0 && (
                <div className="w-full relative" ref={conversationRef}>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <p className="text-sm text-white/80">Conversation</p>
                    <p className="text-xs text-white/60">{historyEntries.length} queries</p>
                  </div>
                  <div className="space-y-8 pr-1">
                    {historyEntries.map((entry, idx) => (
                      <div key={entry.id}>
                        {/* User query bubble, right-aligned */}
                        <div className="flex justify-end mb-2">
                          <div className="bg-gray-300 text-gray-900 rounded-xl px-4 py-3 max-w-xl text-base shadow border border-gray-400 break-words whitespace-pre-line">
                            {entry.query}
                          </div>
                        </div>
                        {/* Assistant response, left-aligned */}
                        <div className="flex justify-start">
                          <div className="bg-white text-black rounded-xl px-4 py-3 max-w-2xl text-base shadow border border-white/15 whitespace-pre-line">
                            {entry.result?.answer || entry.error || "No response."}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 flex flex-col items-center gap-3" ref={inputRef}>
                    <SearchScopeSelector value={searchScope} onChange={handleSearchScopeChange} />
                    <p className="text-xs text-white/70 text-center max-w-2xl">
                      {searchScope === "patent"
                        ? "Next search will use WIP patent mode and return one hit per patent using the best matching claim as the snippet."
                        : "Next search will use claim mode and return the best individual matching claims."}
                    </p>
                    {searchScope !== resultSearchScope ? (
                      <p className="text-xs text-white/55 text-center max-w-2xl">
                        Current results stay in {resultSearchScope} mode until you submit a new query.
                      </p>
                    ) : null}
                    <SearchBar
                      onSearch={handleSearch}
                      placeholder="Refine your query..."
                      extraControls={(
                        <button
                          type="button"
                          onClick={() => setFiltersOpen((open) => !open)}
                          className={`px-3 py-3 rounded-lg border text-sm font-medium whitespace-nowrap transition ${
                            filtersOpen || activeFilterCount
                              ? "bg-white text-black border-white"
                              : "bg-black/30 border-white/20 text-white hover:bg-black/40"
                          }`}
                          aria-expanded={filtersOpen}
                          aria-label="Toggle filters"
                        >
                          Filters{activeFilterCount ? ` (${activeFilterCount})` : ""}
                        </button>
                      )}
                    />
                    {filtersOpen ? (
                      <div className="w-full max-w-2xl rounded-xl border border-white/20 bg-black/40 p-4 shadow-lg shadow-black/20">
                        <div className="space-y-3">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="text-sm text-white/80">Filter search results</p>
                              <p className="text-xs text-white/55">
                                Available filters: doc_id, claim type, and filing date.
                              </p>
                            </div>
                            <button
                              type="button"
                              onClick={() => setFiltersOpen(false)}
                              className="rounded border border-white/20 px-2 py-1 text-xs text-white/70 hover:bg-white/10"
                            >
                              Close
                            </button>
                          </div>
                          <label className="block text-xs text-white/70">
                            doc_id contains
                            <input
                              type="text"
                              value={filters.docId}
                              onChange={(e) => handleFilterChange("docId", e.target.value)}
                              className="mt-1 w-full rounded bg-white/95 text-black px-2 py-1.5"
                              placeholder="e.g. 12345"
                            />
                          </label>
                          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                            <label className="block text-xs text-white/70">
                              Filing from
                              <input
                                type="date"
                                value={filters.dateFrom}
                                onChange={(e) => handleFilterChange("dateFrom", e.target.value)}
                                className="mt-1 w-full rounded bg-white/95 text-black px-2 py-1.5"
                              />
                            </label>
                            <label className="block text-xs text-white/70">
                              Filing to
                              <input
                                type="date"
                                value={filters.dateTo}
                                onChange={(e) => handleFilterChange("dateTo", e.target.value)}
                                className="mt-1 w-full rounded bg-white/95 text-black px-2 py-1.5"
                              />
                            </label>
                          </div>
                          <label className="block text-xs text-white/70">
                            Claim type
                            <select
                              value={filters.claimType}
                              onChange={(e) => handleFilterChange("claimType", e.target.value)}
                              className="mt-1 w-full rounded bg-white/95 text-black px-2 py-1.5"
                            >
                              {CLAIM_TYPE_FILTER_OPTIONS.map((option) => (
                                <option key={option.value || "any"} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                          </label>
                          <div className="flex flex-wrap items-center gap-2">
                            <button
                              type="button"
                              onClick={applyFilters}
                              className="px-3 py-1.5 rounded bg-white text-black border border-white text-xs hover:bg-white/90"
                            >
                              Use on Next Search
                            </button>
                            <button
                              type="button"
                              onClick={resetFilters}
                              className="px-3 py-1.5 rounded bg-white/15 border border-white/30 text-white text-xs hover:bg-white/20"
                            >
                              Clear Filters
                            </button>
                            <p className="text-xs text-white/60">
                              Current returned results: cited {filteredCitedItems.length}, other {filteredOtherItems.length}
                            </p>
                          </div>
                        </div>
                      </div>
                    ) : filtersDirty ? (
                      <p className="text-xs text-white/60 text-center max-w-2xl">
                        Edited filters will be used the next time you submit a search.
                      </p>
                    ) : submittedFilterCount ? (
                      <p className="text-xs text-white/60 text-center max-w-2xl">
                        {submittedFilterCount} filter{submittedFilterCount === 1 ? "" : "s"} applied to the current search.
                      </p>
                    ) : null}
                    <button
                      type="button"
                      className="mt-2 px-4 py-2 rounded bg-black/60 text-white font-semibold border border-white/20 hover:bg-black/80 transition"
                      onClick={() => {
                        window.history.replaceState({}, '', '/');
                        window.dispatchEvent(new PopStateEvent('popstate'));
                      }}
                    >
                      Back to Home
                    </button>
                  </div>
                  {showScrollToInput && (
                    <button
                      type="button"
                      className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 rounded-full border border-orange-200/40 bg-[#500000]/90 px-5 py-2 text-sm font-semibold text-orange-50 shadow-lg shadow-black/30 backdrop-blur-sm transition hover:bg-orange-600/95"
                      onClick={() => {
                        inputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
                      }}
                    >
                      Scroll to Input
                    </button>
                  )}
                </div>
              )}

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
              {/* Search bar is now at the bottom of the conversation history */}
            </div>

            {/* Right: fixed, full-height scrollable results panel at the very edge */}
            <aside
              className="hidden md:block fixed right-0 top-0 h-screen overflow-y-auto z-10 bg-white/10 border-l border-white/20"
              style={{ width: `${resultsPanelWidth}px`, maxWidth: `900px` }}
            >
              <div
                className="absolute left-0 top-0 h-full w-3 -translate-x-1/2 cursor-col-resize flex items-center justify-center hover:bg-white/10"
                onMouseDown={startResultsPanelResize}
                title="Drag to resize results panel"
              >
                <div className="h-full w-px bg-white/25" />
              </div>
              <div className="p-4 pt-24 text-base">
                <p className="text-base text-white/70 mb-2">Results</p>
                <p className="text-sm text-white/60">Cited Patents ({filteredCitedItems.length})</p>
                {filteredCitedItems.map((it, idx) => {
                      const kind = (it.kind || "").trim();
                      const patentDocId = googlePatentDocId(it.doc_id);
                      const gpUrl = patentDocId
                        ? `https://patents.google.com/patent/US${patentDocId}${kind ? kind : ""}/en?oq=${patentDocId}`
                        : null;
                      return (
                        <div key={`cited-${it.id}`} id={`ref-${idx + 1}`} className="bg-black/30 p-3 rounded mt-2">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="text-base font-semibold break-words">[{idx + 1}] {it.title}</p>
                              {it.snippet && (
                                <p
                                  className={`${isNarrowResultsPanel ? "line-clamp-7" : isWideResultsPanel ? "line-clamp-3" : "line-clamp-4"} text-sm text-white/70 mt-1 break-words`}
                                >
                                  {it.snippet}
                                </p>
                              )}
                              <div className="mt-2 text-sm text-white/80 space-y-1">
                                {isPatentResultScope && it.best_claim_id ? (
                                  <p><span className="text-white/60">Best Claim Match:</span> {it.best_claim_id}</p>
                                ) : null}
                                {isPatentResultScope && it.best_claim_type ? (
                                  <p><span className="text-white/60">Best Claim Type:</span> {it.best_claim_type}</p>
                                ) : null}
                                {it.authors ? (
                                  <p><span className="text-white/60">Authors:</span> {formatAuthors(it.authors)}</p>
                                ) : null}
                                {it.classification ? (
                                  <p><span className="text-white/60">Classification:</span> {it.classification}</p>
                                ) : null}
                                {it.filing_date ? (
                                  <p><span className="text-white/60">Filing Date:</span> {formatDateDisplay(it.filing_date)}</p>
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
                                      className="text-blue-200 hover:text-blue-100 underline break-all"
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
                {filteredCitedItems.length === 0 ? (
                  <p className="text-xs text-white/60 mt-2">No cited results match the current filters.</p>
                ) : null}

                {filteredOtherItems.length ? (
                  <>
                    <p className="text-xs text-white/60 mt-4">More Results ({filteredOtherItems.length})</p>
                    {filteredOtherItems.map((it, idx) => {
                          const kind = (it.kind || "").trim();
                          const patentDocId = googlePatentDocId(it.doc_id);
                          const gpUrl = patentDocId
                            ? `https://patents.google.com/patent/US${patentDocId}${kind ? kind : ""}/en?oq=${patentDocId}`
                            : null;
                          return (
                            <div key={`other-${it.id}`} className="bg-black/30 p-3 rounded mt-2">
                              <div className="flex items-start justify-between gap-3">
                                <div className="min-w-0">
                                  <p className="text-base font-semibold break-words">[{filteredCitedItems.length + idx + 1}] {it.title}</p>
                                  {it.snippet && (
                                    <p
                                      className={`${isNarrowResultsPanel ? "line-clamp-7" : isWideResultsPanel ? "line-clamp-3" : "line-clamp-5"} text-xs text-white/70 mt-1 break-words`}
                                    >
                                      {it.snippet}
                                    </p>
                                  )}
                                  <div className="mt-2 text-xs text-white/80 space-y-1">
                                    {isPatentResultScope && it.best_claim_id ? (
                                      <p><span className="text-white/60">Best Claim Match:</span> {it.best_claim_id}</p>
                                    ) : null}
                                    {isPatentResultScope && it.best_claim_type ? (
                                      <p><span className="text-white/60">Best Claim Type:</span> {it.best_claim_type}</p>
                                    ) : null}
                                    {it.authors ? (
                                      <p><span className="text-white/60">Authors:</span> {formatAuthors(it.authors)}</p>
                                    ) : null}
                                    {it.classification ? (
                                      <p><span className="text-white/60">Classification:</span> {it.classification}</p>
                                    ) : null}
                                    {it.filing_date ? (
                                      <p><span className="text-white/60">Filing Date:</span> {formatDateDisplay(it.filing_date)}</p>
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
                                          className="text-blue-200 hover:text-blue-100 underline break-all"
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
