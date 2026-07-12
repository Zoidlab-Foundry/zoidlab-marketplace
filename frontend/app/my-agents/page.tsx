"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "../../lib/api";
import type { Agent } from "../../lib/types";
import { VisibilityBadge } from "../../components/Badges";

const TABS = ["Installed", "Created", "Drafts", "Submitted", "Private"];

export default function MyAgents() {
  const [data, setData] = useState<{ installed: Agent[]; created: Agent[] } | null>(null);
  const [tab, setTab] = useState("Installed");
  const [err, setErr] = useState("");

  const load = () => api.myAgents().then(setData).catch((e) => setErr(e.status === 401 ? "auth" : e.message));
  useEffect(() => { load(); }, []);

  if (err === "auth") {
    return <Empty title="Sign in to manage your agents" body="Open ZoidLab from your Nyquest app to sign in, then your installed and created agents appear here." />;
  }
  if (!data) return <div className="py-24 text-center text-faint">Loading…</div>;

  const created = data.created;
  const rows: Record<string, Agent[]> = {
    Installed: data.installed,
    Created: created,
    Drafts: created.filter((a) => a.status === "draft"),
    Submitted: created.filter((a) => ["pending", "submitted", "rejected"].includes(a.status)),
    Private: created.filter((a) => a.visibility === "private"),
  };
  const list = rows[tab];

  async function remove(a: Agent) {
    if (!a.install_id) return;
    await api.uninstall(a.install_id);
    load();
  }

  return (
    <div className="py-8">
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="text-[22px] font-semibold">My Agents</h1>
          <p className="mt-1 text-[13px] text-dim">Agents you've installed or created.</p>
        </div>
        <Link href="/submit" className="rounded-lg bg-vi px-4 py-2 text-[13px] font-semibold text-white hover:opacity-90">Submit new agent</Link>
      </div>

      <div className="mb-5 flex flex-wrap gap-1 border-b border-line">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-3 py-2 text-[13px] ${tab === t ? "border-b-2 border-vi text-ink" : "text-dim hover:text-ink"}`}>
            {t} <span className="text-faint">{rows[t].length}</span>
          </button>
        ))}
      </div>

      {!list.length ? <Empty title={`No ${tab.toLowerCase()} agents`} body="Browse the marketplace to install one, or submit your own." /> : (
        <div className="space-y-2">
          {list.map((a) => (
            <div key={a.id + (a.install_id || "")} className="flex items-center gap-4 rounded-xl border border-line bg-panel p-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg text-[18px]" style={{ background: `${a.accent}22` }}>{a.icon}</div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <Link href={`/agents/${a.slug}`} className="truncate text-[14px] font-medium text-ink hover:text-cy">{a.name}</Link>
                  <StatusPill status={tab === "Installed" ? (a.install_status || "installed") : a.status} />
                </div>
                <div className="text-[11px] text-faint">v{a.version} · {a.category} · {tab === "Installed" ? `installed ${a.installed_at?.slice(0, 10)}` : `updated ${a.updated_at?.slice(0, 10)}`}</div>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {tab !== "Installed" && <VisibilityBadge visibility={a.visibility} />}
                {tab !== "Installed"
                  ? <Link href={`/agents/${a.slug}/edit`} className="rounded-md border border-line px-3 py-1.5 text-[12px] text-dim hover:text-ink">Edit</Link>
                  : <>
                      <a href="https://builder.zoidlab.ai" target="_blank" rel="noopener" className="rounded-md border border-line px-3 py-1.5 text-[12px] text-cy hover:bg-white/5">Open in Builder ↗</a>
                      <button onClick={() => remove(a)} className="rounded-md border border-line px-3 py-1.5 text-[12px] text-bad hover:bg-bad/10">Remove</button>
                    </>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const style: Record<string, string> = {
    installed: "text-ok border-ok/40 bg-ok/10", published: "text-cy border-cy/40 bg-cy/10",
    approved: "text-cy border-cy/40 bg-cy/10", draft: "text-dim border-line bg-white/5",
    pending: "text-warn border-warn/40 bg-warn/10", rejected: "text-bad border-bad/40 bg-bad/10",
  };
  return <span className={`rounded-full border px-2 py-0.5 text-[10px] ${style[status] || "text-dim border-line bg-white/5"}`}>{status}</span>;
}

function Empty({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-line py-16 text-center">
      <div className="text-[15px] text-dim">{title}</div>
      <div className="mx-auto mt-1 max-w-sm text-[13px] text-faint">{body}</div>
      <Link href="/agents" className="mt-4 inline-block rounded-lg border border-line px-4 py-2 text-[13px] text-ink hover:bg-white/5">Browse agents</Link>
    </div>
  );
}
