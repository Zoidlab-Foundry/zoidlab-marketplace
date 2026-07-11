"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "../../lib/api";
import type { Agent, Category } from "../../lib/types";
import AgentGrid from "../../components/AgentGrid";
import AgentFilters from "../../components/AgentFilters";

function Browse() {
  const params = useSearchParams();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [cats, setCats] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState(params.get("category") || "all");
  const [sort, setSort] = useState("installs");
  const [search, setSearch] = useState(params.get("search") || "");

  useEffect(() => { api.categories().then(setCats).catch(() => {}); }, []);

  useEffect(() => {
    setLoading(true);
    const t = setTimeout(() => {
      api.agents({ category: category === "all" ? "" : category, sort, search })
        .then((d) => setAgents(d.agents)).catch(() => setAgents([])).finally(() => setLoading(false));
    }, 180);
    return () => clearTimeout(t);
  }, [category, sort, search]);

  return (
    <div className="py-8">
      <div className="mb-6">
        <h1 className="text-[22px] font-semibold">Browse agents</h1>
        <p className="mt-1 text-[13px] text-dim">Discover reusable AI agents. Filter by category, sort, and open any agent to test or install it.</p>
      </div>
      <AgentFilters categories={cats} category={category} sort={sort} search={search}
        onCategory={setCategory} onSort={setSort} onSearch={setSearch} />
      <div className="mt-6">
        <div className="mb-3 text-[12px] text-faint">{loading ? "Loading…" : `${agents.length} agent${agents.length === 1 ? "" : "s"}`}</div>
        <AgentGrid agents={agents} empty={loading ? "Loading agents…" : "No agents match your filters."} />
      </div>
    </div>
  );
}

export default function AgentsPage() {
  return <Suspense fallback={<div className="py-16 text-center text-faint">Loading…</div>}><Browse /></Suspense>;
}
