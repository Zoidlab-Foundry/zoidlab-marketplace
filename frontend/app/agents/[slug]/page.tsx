"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "../../../lib/api";
import type { Agent } from "../../../lib/types";
import { GovBadges, VisibilityBadge } from "../../../components/Badges";
import ManifestViewer from "../../../components/ManifestViewer";
import SandboxTester from "../../../components/SandboxTester";
import { useUser } from "../../../lib/useUser";
import ReviewsTab from "../../../components/ReviewsTab";

const TABS = ["Overview", "Capabilities", "Requirements", "Permissions", "Manifest", "Reviews", "Versions"];


export default function AgentDetail() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const { authed } = useUser();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [tab, setTab] = useState("Overview");
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  const load = () => api.agent(slug).then(setAgent).catch(() => setAgent(null));
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [slug]);

  if (agent === null) {
    return <div className="py-24 text-center text-faint">Loading agent… <div className="mt-2 text-[12px]">If this persists, the agent may be private or not found.</div></div>;
  }

  async function action(kind: "install" | "clone") {
    if (!authed) { setMsg({ kind: "err", text: "Sign in from your Nyquest app to install or clone." }); return; }
    setBusy(kind); setMsg(null);
    try {
      if (kind === "install") {
        await api.install(agent!.id);
        setMsg({ kind: "ok", text: "Installed. Find it under My Agents." });
        load();
      } else {
        const r = await api.clone(agent!.id);
        router.push(`/agents/${r.agent.slug}/edit`);
      }
    } catch (e: any) {
      setMsg({ kind: "err", text: e.status === 401 ? "Sign in required." : e.message });
    } finally { setBusy(""); }
  }

  const man = agent.manifest || {};
  const example = man.examples || {};

  return (
    <div className="py-8">
      <Link href="/agents" className="text-[12px] text-faint hover:text-dim">← Back to agents</Link>

      {/* header */}
      <div className="mt-4 flex flex-col gap-5 rounded-2xl border border-line bg-panel p-6 sm:flex-row sm:items-start">
        <div className="grid h-16 w-16 shrink-0 place-items-center rounded-2xl text-[32px]"
          style={{ background: `${agent.accent}22`, boxShadow: `inset 0 0 0 1px ${agent.accent}44` }}>{agent.icon}</div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-[24px] font-bold">{agent.name}</h1>
            <VisibilityBadge visibility={agent.visibility} />
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-dim">
            <span>by {agent.publisher_name}</span><span className="text-line">·</span>
            <span>v{agent.version}</span><span className="text-line">·</span>
            <span className="rounded bg-white/5 px-1.5 py-0.5">{agent.category}</span><span className="text-line">·</span>
            <span>by {agent.publisher_name}</span>
            {(agent.rating_count ?? 0) > 0 && <><span className="text-line">·</span><span className="text-warn">★ {agent.rating_avg.toFixed(1)}</span><span className="text-faint">({agent.rating_count})</span></>}
          </div>
          <p className="mt-3 max-w-2xl text-[13.5px] leading-relaxed text-dim">{agent.short_description}</p>
          <div className="mt-3"><GovBadges badges={agent.badges} /></div>
        </div>
        <div className="flex shrink-0 flex-col gap-2">
          <button onClick={() => action("install")} disabled={!!busy}
            className="rounded-lg bg-vi px-5 py-2.5 text-[13px] font-semibold text-white hover:opacity-90 disabled:opacity-50">
            {agent.installed ? "Reinstall" : busy === "install" ? "Installing…" : "Install Agent"}
          </button>
          <button onClick={() => action("clone")} disabled={!!busy}
            className="rounded-lg border border-line px-5 py-2.5 text-[13px] font-semibold text-ink hover:bg-white/5 disabled:opacity-50">
            {busy === "clone" ? "Cloning…" : "Clone & Customize"}
          </button>
          <a href="#sandbox" className="rounded-lg border border-line px-5 py-2.5 text-center text-[13px] text-dim hover:text-ink">Test in Sandbox</a>
        </div>
      </div>
      {msg && <div className={`mt-3 rounded-lg border px-4 py-2 text-[13px] ${msg.kind === "ok" ? "border-ok/40 bg-ok/10 text-ok" : "border-bad/40 bg-bad/10 text-bad"}`}>{msg.text}</div>}

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        {/* main column */}
        <div>
          <div className="flex flex-wrap gap-1 border-b border-line">
            {TABS.map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-3 py-2 text-[13px] transition ${tab === t ? "border-b-2 border-vi text-ink" : "text-dim hover:text-ink"}`}>{t}</button>
            ))}
          </div>
          <div className="py-5">
            {tab === "Overview" && (
              <div className="space-y-4 text-[13.5px] leading-relaxed text-dim">
                <p>{agent.long_description || agent.short_description}</p>
                {example.input && (
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-xl border border-line bg-panel2 p-3">
                      <div className="mb-1 text-[10px] uppercase tracking-wider text-faint">Example input</div>
                      <pre className="overflow-auto text-[12px] text-ink">{JSON.stringify(example.input, null, 2)}</pre>
                    </div>
                    <div className="rounded-xl border border-line bg-panel2 p-3">
                      <div className="mb-1 text-[10px] uppercase tracking-wider text-faint">Example output</div>
                      <pre className="overflow-auto text-[12px] text-ink">{JSON.stringify(example.output, null, 2)}</pre>
                    </div>
                  </div>
                )}
              </div>
            )}
            {tab === "Capabilities" && (
              <ul className="space-y-2 text-[13px] text-dim">
                {(agent.tags || []).map((t) => <li key={t} className="flex items-center gap-2"><span className="text-cy">▸</span> Handles <span className="text-ink">{t}</span> tasks</li>)}
                <li className="flex items-center gap-2"><span className="text-cy">▸</span> Runtime: <span className="text-ink">{man.runtime?.type || "workflow"}</span>{man.runtime?.supports_streaming && " · streaming"}</li>
              </ul>
            )}
            {tab === "Requirements" && (
              <div className="space-y-5">
                <Req title="Model providers" items={(agent.required_models || []).map((m: any) => `${m.provider}/${m.model}${m.required ? " (required)" : ""}`)} empty="Uses Nyquest auto-routing." />
                <Req title="Tools" items={(agent.required_tools || []).map((t: any) => `${t.name} · ${t.type}${t.required ? " (required)" : ""}`)} empty="No external tools required." />
                <Req title="Secrets" items={(agent.required_secrets || []).map((s: any) => `${s.name} — ${s.description}`)} empty="No secrets required." />
              </div>
            )}
            {tab === "Permissions" && (
              <div className="space-y-2">
                <p className="mb-3 text-[12px] text-faint">Exactly what this agent can and cannot access. No fine print.</p>
                {(agent.permissions || []).map((p: any) => (
                  <div key={p.name} className="flex items-start gap-3 rounded-xl border border-line bg-panel2 p-3">
                    <span className="mt-0.5 text-cy">🔓</span>
                    <div><div className="text-[13px] font-medium text-ink">{p.name}</div><div className="text-[12px] text-dim">{p.description}</div></div>
                  </div>
                ))}
                {!(agent.permissions || []).length && <p className="text-[13px] text-faint">No permissions declared.</p>}
              </div>
            )}
            {tab === "Manifest" && <ManifestViewer manifest={agent.manifest} />}
            {tab === "Reviews" && <ReviewsTab agentId={agent.id} authed={authed} />}
            {tab === "Versions" && (
              <div className="space-y-2">
                {(agent.versions || []).map((v) => (
                  <div key={v.id} className="flex items-center justify-between rounded-xl border border-line bg-panel2 p-3 text-[13px]">
                    <span className="font-medium text-ink">v{v.version}</span>
                    <span className="text-dim">{v.changelog}</span>
                    <span className="text-faint">{v.created_at?.slice(0, 10)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* side column */}
        <div className="space-y-5" id="sandbox">
          <SandboxTester agent={agent} />
          <div className="rounded-2xl border border-line bg-panel p-5">
            <h3 className="mb-3 text-[14px] font-semibold">Governance & safety</h3>
            <GovBadges badges={agent.badges} />
            <dl className="mt-4 space-y-2 text-[12px]">
              <Row k="PII risk" v={man.governance?.pii_risk || "low"} />
              <Row k="Human approval" v={man.governance?.requires_human_approval ? "recommended" : "not required"} />
              <Row k="Logs prompts" v={man.governance?.logs_prompts ? "yes" : "no"} />
              <Row k="Logs outputs" v={man.governance?.logs_outputs ? "yes" : "no"} />
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}

function Req({ title, items, empty }: { title: string; items: string[]; empty: string }) {
  return (
    <div>
      <h4 className="mb-2 text-[12px] uppercase tracking-wider text-faint">{title}</h4>
      {items.length ? (
        <ul className="space-y-1.5">{items.map((i) => <li key={i} className="rounded-lg border border-line bg-panel2 px-3 py-2 text-[13px] text-dim">{i}</li>)}</ul>
      ) : <p className="text-[13px] text-faint">{empty}</p>}
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return <div className="flex items-center justify-between"><dt className="text-faint">{k}</dt><dd className="text-dim">{v}</dd></div>;
}
