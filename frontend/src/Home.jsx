// src/pages/Home.jsx
// Landing page with hero and centered search bar.
// On submit, it performs client-side navigation to /search?q=...
import { useMemo, useState } from "react";
import robot from "./assets/robot.png";
import SearchBar from "./components/SearchBar.jsx";
import SearchScopeSelector from "./components/SearchScopeSelector.jsx";
import DevTuningPanel from "./components/DevTuningPanel.jsx";
import {
  DEFAULT_TUNING,
  DEV_TUNING_VISIBLE,
  loadStoredTuning,
  normalizeTuning,
  saveStoredTuning,
} from "./lib/devTuning.js";
import { normalizeSearchScope } from "./lib/api.js";

const EMPTY_FILTERS = Object.freeze({
  dateFrom: "",
  dateTo: "",
  claimType: "",
  docId: "",
});

const HOME_CLAIM_TYPE_OPTIONS = [
  { value: "", label: "Any" },
  { value: "independent", label: "Independent" },
  { value: "dependent", label: "Dependent" },
];

function cloneFilters(filters) {
  return {
    dateFrom: String(filters?.dateFrom || ""),
    dateTo: String(filters?.dateTo || ""),
    claimType: String(filters?.claimType || ""),
    docId: String(filters?.docId || ""),
  };
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

export default function Home() {
  const [draftTuning, setDraftTuning] = useState(() => loadStoredTuning());
  const [activeTuning, setActiveTuning] = useState(() => loadStoredTuning());
  const [searchScope, setSearchScope] = useState("claim");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [filters, setFilters] = useState(() => cloneFilters(EMPTY_FILTERS));
  const isPatentScope = searchScope === "patent";
  const activeFilterCount = useMemo(
    () => Object.values(filters).filter((value) => String(value || "").trim()).length,
    [filters],
  );

  // Parent handler passed to SearchBar. It updates the browser history
  // so the in-file router (see src/main.jsx) renders the Results page.
  function handleSearch(query) {
    // Build new URL with query param
    const url = buildSearchUrl(query, searchScope, filters);
    // Push a new history entry without full page reload
    window.history.pushState({}, "", url);
    // Notify our simple router to re-evaluate location
    window.dispatchEvent(new PopStateEvent("popstate"));
  }

  function handleFilterChange(field, value) {
    setFilters((prev) => ({ ...prev, [field]: value }));
  }

  function resetFilters() {
    setFilters(cloneFilters(EMPTY_FILTERS));
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

  return (
    <div className="min-h-dvh bg-gradient-to-r from-[#500000] via-orange-500 to-[#500000] flex flex-col items-center justify-center text-white px-6 py-10">
      {DEV_TUNING_VISIBLE && (
        <DevTuningPanel
          draftTuning={draftTuning}
          activeTuning={activeTuning}
          onTuningChange={handleTuningChange}
          onApply={applyTuning}
          onReset={resetTuning}
          subtitle="Saved locally, used on the Results page"
          note="Tip: open /search?q=demo to inspect results layout even without API."
        />
      )}

      {/* Hero image */}
      <img
        src={robot}
        alt="Rusty the Patent Miner"
        className="w-40 sm:w-56 md:w-72 lg:w-96 xl:w-[520px] h-auto mx-auto mb-4"
      />
      {/* Title + subtitle */}
      <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-white drop-shadow-lg tracking-tight mb-2 text-center">
        The Patent Miner
      </h1>
      <p className="text-base sm:text-lg text-white/90 mb-8 text-center">
        Rusty uncovers innovation, one swing at a time ⚒️
      </p>

      {/* Centered search bar */}
      <div className="w-full flex flex-col items-center gap-4 px-2">
        <SearchScopeSelector value={searchScope} onChange={setSearchScope} />
        <p className="text-sm text-white/85 text-center max-w-2xl">
          {isPatentScope
            ? "Patent search returns one result per patent and ranks patents by the highest-ranked matching claim."
            : "Claim search keeps the current behavior and returns the best-matching individual claims."}
        </p>
        <SearchBar
          onSearch={handleSearch}
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
                  <p className="text-sm text-white/80">Filter the next search</p>
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
                  {HOME_CLAIM_TYPE_OPTIONS.map((option) => (
                    <option key={option.value || "any"} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={resetFilters}
                  className="px-3 py-1.5 rounded bg-white/15 border border-white/30 text-white text-xs hover:bg-white/20"
                >
                  Clear Filters
                </button>
                <p className="text-xs text-white/60">
                  These filters will be used the next time you search.
                </p>
              </div>
            </div>
          </div>
        ) : activeFilterCount ? (
          <p className="text-xs text-white/60 text-center max-w-2xl">
            {activeFilterCount} filter{activeFilterCount === 1 ? "" : "s"} ready for the next search.
          </p>
        ) : null}
      </div>
    </div>
  );
}
