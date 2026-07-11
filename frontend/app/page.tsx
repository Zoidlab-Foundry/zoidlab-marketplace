"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "../lib/api";
import type { Agent, Category } from "../lib/types";
import AgentGrid from "../components/AgentGrid";

export default function Home() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [cats, setCats] = useState<Category[]>([]);
  const [q, setQ] = useState("");

  useEffect(() => {
    api.agents({ sort: "installs" }).then((d) => setAgents(d.agents)).catch(() => {});
    api.categories().then(setCats).catch(() => {});
  }, []);

  const featured = agents.filter((a) => a.featured).slice(0, 6);
  const recent = [...agents].sort((a, b) => (a.created_at! < b.created_at! ? 1 : -1)).slice(0, 6);
  const go = () => router.push(`/agents${q ? `?search=${encodeURIComponent(q)}` : ""}`);

  return (
    <div className="relative">
      <div className="hero-glow" />
      {/* hero */}
      <section className="relative z-10 pt-16 pb-10 text-center">
        <span className="mb-5 inline-flex items-center gap-2 rounded-full border border-line bg-panel px-3 py-1 text-[11px] text-dim">
          <span className="h-1.5 w-1.5 rounded-full bg-vi" /> Prototype · The agent app store for Nyquest
        </span>
        <h1 className="mx-auto max-w-3xl text-[38px] font-bold leading-[1.1] tracking-tight sm:text-[46px]">
          ZoidLab <span className="prism-text">Marketplace</span>
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-[15px] leading-relaxed text-dim">
          Prototype, package, and deploy reusable AI agents across Nyquest.
        </p>
        <div className="mx-auto mt-7 flex max-w-xl items-center gap-2">
          <input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && go()}
            placeholder="Search agents by name, task, or category…"
            className="w-full rounded-xl border border-line bg-panel px-4 py-3 text-[14px] text-ink placeholder-faint outline-none focus:border-vi/60" />
          <button onClick={go} className="rounded-xl bg-vi px-5 py-3 text-[14px] font-semibold text-white hover:opacity-90">Search</button>
        </div>
        <div className="mt-5 flex items-center justify-center gap-3">
          <Link href="/agents" className="rounded-lg border border-line px-4 py-2 text-[13px] text-ink hover:bg-white/5">Browse Agents</Link>
          <Link href="/submit" className="rounded-lg border border-line px-4 py-2 text-[13px] text-ink hover:bg-white/5">Submit Agent</Link>
          <Link href="/my-agents" className="rounded-lg border border-line px-4 py-2 text-[13px] text-ink hover:bg-white/5">My Agents</Link>
        </div>
      </section>

      {/* categories */}
      {cats.length > 0 && (
        <section className="relative z-10 mt-6">
          <div className="flex flex-wrap justify-center gap-2">
            {cats.map((c) => (
              <Link key={c.name} href={`/agents?category=${encodeURIComponent(c.name)}`}
                className="rounded-full border border-line bg-panel px-3 py-1.5 text-[12px] text-dim hover:border-vi/50 hover:text-ink">
                {c.name} <span className="text-faint">{c.count}</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* featured */}
      <section className="relative z-10 mt-14">
        <div className="mb-4 flex items-end justify-between">
          <h2 className="text-[18px] font-semibold">Featured agents</h2>
          <Link href="/agents" className="text-[12px] text-cy hover:underline">View all →</Link>
        </div>
        <AgentGrid agents={featured.length ? featured : agents.slice(0, 6)} empty="Loading agents…" />
      </section>

      {/* recently added */}
      <section className="relative z-10 mt-14">
        <h2 className="mb-4 text-[18px] font-semibold">Recently added</h2>
        <AgentGrid agents={recent} empty="Loading agents…" />
      </section>

      {/* trust strip */}
      <section className="relative z-10 mt-16 rounded-2xl border border-line prism-bg p-6">
        <h3 className="text-[15px] font-semibold text-ink">Built for trust</h3>
        <p className="mt-1 max-w-2xl text-[13px] leading-relaxed text-dim">
          Every listing makes it obvious what an agent does, what it can access, which models it uses, and what risks it carries —
          with governance badges, declared permissions, and required secrets shown up front. No fine print.
        </p>
      </section>
    </div>
  );
}
