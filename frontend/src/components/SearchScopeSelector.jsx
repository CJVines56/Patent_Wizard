const SEARCH_SCOPE_OPTIONS = [
  { value: "claim", label: "Claim Search" },
  { value: "patent", label: "WIP Patent Search" },
];

export default function SearchScopeSelector({
  value = "claim",
  onChange,
  className = "",
}) {
  return (
    <div className={`inline-flex flex-wrap items-center gap-2 ${className}`.trim()}>
      {SEARCH_SCOPE_OPTIONS.map((option) => {
        const isActive = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange?.(option.value)}
            className={`rounded-full border px-4 py-2 text-sm font-semibold transition-colors ${
              isActive
                ? "border-white bg-white text-[#500000]"
                : "border-white/30 bg-black/20 text-white hover:bg-black/30"
            }`}
            aria-pressed={isActive}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
