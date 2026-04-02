import { useState } from "react";

export default function DevTuningPanel({
  draftTuning,
  activeTuning,
  onTuningChange,
  onApply,
  onReset,
  subtitle = "Frontend-only knobs",
  note = "",
}) {
  const [open, setOpen] = useState(false);

  function handleSubmit(e) {
    e.preventDefault();
    onApply();
  }

  return (
    <div className="fixed left-4 top-1/2 -translate-y-1/2 z-20 w-72 max-w-[90vw]">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="w-full flex items-center justify-between rounded-lg bg-black/45 border border-white/30 px-3 py-2 text-sm font-semibold text-white backdrop-blur-sm"
      >
        <span>Dev Tuning</span>
        <svg
          aria-hidden="true"
          viewBox="0 0 16 16"
          className={`h-3 w-3 text-white/85 transition-transform ${open ? "rotate-90" : "rotate-180"}`}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M5 3l6 5-6 5" />
        </svg>
      </button>

      {open && (
        <form
          onSubmit={handleSubmit}
          className="mt-2 bg-black/35 border border-white/20 rounded-lg p-4 backdrop-blur-sm"
        >
          <p className="text-xs text-white/60">{subtitle}</p>

          <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
            <label className="flex flex-col gap-1">
              <span className="text-white/70">k</span>
              <input
                type="number"
                min="1"
                max="50"
                value={draftTuning.k}
                onChange={(e) => onTuningChange("k", e.target.value)}
                className="rounded bg-white/95 text-black px-2 py-1"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-white/70">k_extra</span>
              <input
                type="number"
                min="0"
                max="100"
                value={draftTuning.k_extra}
                onChange={(e) => onTuningChange("k_extra", e.target.value)}
                className="rounded bg-white/95 text-black px-2 py-1"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-white/70">alpha</span>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={draftTuning.alpha}
                onChange={(e) => onTuningChange("alpha", e.target.value)}
                className="rounded bg-white/95 text-black px-2 py-1"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-white/70">retrieval_candidates</span>
              <input
                type="number"
                min="5"
                max="500"
                value={draftTuning.retrieval_candidates}
                onChange={(e) => onTuningChange("retrieval_candidates", e.target.value)}
                className="rounded bg-white/95 text-black px-2 py-1"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-white/70">rerank_k</span>
              <input
                type="number"
                min="1"
                max="500"
                value={draftTuning.rerank_k}
                onChange={(e) => onTuningChange("rerank_k", e.target.value)}
                className="rounded bg-white/95 text-black px-2 py-1"
              />
            </label>
          </div>

          <div className="mt-3 flex items-center gap-2">
            <button
              type="submit"
              className="px-3 py-1.5 rounded bg-white text-black text-xs font-semibold hover:bg-white/90"
            >
              Apply
            </button>
            <button
              type="button"
              onClick={onReset}
              className="px-3 py-1.5 rounded bg-white/15 border border-white/30 text-white text-xs hover:bg-white/20"
            >
              Reset
            </button>
          </div>

          <p className="mt-2 text-[11px] text-white/60">
            Active: k={activeTuning.k}, k_extra={activeTuning.k_extra}, alpha={activeTuning.alpha}
          </p>
          <p className="mt-1 text-[11px] text-white/60">
            Active: retrieval_candidates={activeTuning.retrieval_candidates}, rerank_k={activeTuning.rerank_k}
          </p>
          {note ? <p className="mt-1 text-[11px] text-white/60">{note}</p> : null}
        </form>
      )}
    </div>
  );
}
