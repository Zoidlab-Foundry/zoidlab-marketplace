"use client";
import type { Category } from "../lib/types";

const SORTS = [
  { v: "installs", label: "Most installed" },
  { v: "rating", label: "Highest rated" },
  { v: "newest", label: "Newest" },
  { v: "name", label: "A–Z" },
];

export default function AgentFilters({
  categories, category, sort, search, onCategory, onSort, onSearch,
}: {
  categories: Category[]; category: string; sort: string; search: string;
  onCategory: (c: string) => void; onSort: (s: string) => void; onSearch: (q: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint">⌕</span>
          <input value={search} onChange={(e) => onSearch(e.target.value)} placeholder="Search agents…"
            className="w-full rounded-xl border border-line bg-panel py-2.5 pl-9 pr-3 text-[13px] text-ink placeholder-faint outline-none focus:border-vi/60" />
        </div>
        <select value={sort} onChange={(e) => onSort(e.target.value)}
          className="rounded-xl border border-line bg-panel px-3 py-2.5 text-[13px] text-dim outline-none focus:border-vi/60">
          {SORTS.map((s) => <option key={s.v} value={s.v}>{s.label}</option>)}
        </select>
      </div>
      <div className="flex flex-wrap gap-2">
        <button onClick={() => onCategory("all")}
          className={`rounded-full border px-3 py-1 text-[12px] transition ${category === "all" ? "border-vi/60 bg-vi/15 text-ink" : "border-line text-dim hover:text-ink"}`}>
          All
        </button>
        {categories.map((c) => (
          <button key={c.name} onClick={() => onCategory(c.name)}
            className={`rounded-full border px-3 py-1 text-[12px] transition ${category === c.name ? "border-vi/60 bg-vi/15 text-ink" : "border-line text-dim hover:text-ink"}`}>
            {c.name} <span className="text-faint">{c.count}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
