// src/components/SearchBar.jsx
// Simple controlled input that calls the parent onSearch handler.
import { useState } from "react";

export default function SearchBar({
  onSearch,
  placeholder = "Search patents...",
  topK = null,
  onTopKAdjust = null,
}) {
  // Local input state (the query text)
  const [q, setQ] = useState("");
  // Brief loading flag while the parent is performing the search
  const [loading, setLoading] = useState(false);
  // Short user-facing error message if the parent throws
  const [err, setErr] = useState("");

  // Handle form submit (Enter). Prevent default page reload, validate, call parent.
  async function handleSubmit(e) {
    e.preventDefault();
    setErr("");
    const query = q.trim();
    if (!query) return; // ignore empty submits

    try {
      setLoading(true);
      // Delegate the behavior to the parent (navigate or fetch)
      await onSearch(query);
    } catch (e) {
      // Keep error message generic for the UI; logs can be added upstream
      setErr("Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    // Center the bar with mx-auto; limit width for readability
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="flex items-center gap-2">
        <input
          value={q}                            // controlled input value
          onChange={(e) => setQ(e.target.value)} // update local state as user types
          type="text"
          placeholder={placeholder}
          className="flex-1 px-4 py-3 rounded-lg text-black shadow
                     focus:outline-none focus:ring-2 focus:ring-white"
          aria-label="Search patents"
        />
        {typeof onTopKAdjust === "function" && (
          <button
            type="button"
            onClick={onTopKAdjust}
            className="px-3 py-3 rounded-lg bg-black/30 border border-white/20
                       text-white text-sm font-medium hover:bg-black/40 whitespace-nowrap"
            aria-label="Adjust top K"
            title="Adjust retrieval top K"
          >
            K: {topK ?? "-"}
          </button>
        )}
        <button
          type="submit"
          disabled={loading || !q.trim()}
          className="px-3 py-3 rounded-lg bg-orange-600 text-white text-sm font-medium
                     hover:bg-orange-500 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Submit search"
        >
          Search
        </button>
      </div>
      {/* Inline status and error messages below the input */}
      {err && <p className="mt-2 text-sm text-red-200">{err}</p>}
      {loading && <p className="mt-2 text-sm text-white/80">Searching...</p>}
    </form>
  );
}
