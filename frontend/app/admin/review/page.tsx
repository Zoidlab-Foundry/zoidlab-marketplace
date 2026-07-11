"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "../../../lib/api";
import type { Agent } from "../../../lib/types";
import { GovBadges } from "../../../components/Badges";

export default function AdminReview() {
  const [subs, setSubs] = useState<Agent[] | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState("");

  const load = () => api.submissions().then((d) => setSubs(d.submissions)).catch((e) => setErr(e.status === 403 ? "forbidden" : e.status === 401 ? "auth" : e.message));
  useEffect(() => { load(); }, []);

  if (err === "auth") return <Note title="Sign in required" body="Open ZoidLab from your Nyquest app to sign in." />;
  if (err === "forbidden") return <Note title="Admins only" body="This review queue is restricted to marketplace admins." />;
  if (!subs) return <div className="py-24 text-center text-faint">Loading…</div>;

  async function act(a: Agent, kind: "approve" | "reject" | "request-changes") {
    setBusy(a.id + kind);
    try {
      if (kind === "approve") await api.approve(a.id);
      else if (kind === "reject") await api.reject(a.id);
      else await api.requestChanges(a.id);
      load();
    } catch (e: any) { setErr(e.message); } finally { setBusy(""); }
  }

  return (
    <div className="py-8">
      <h1 className="text-[22px] font-semibold">Review queue</h1>
      <p className="mt-1 text-[13px] text-dim">Pending submissions. Approve to publish to the marketplace, reject, or request changes.</p>

      {!subs.length ? <Note title="Queue is empty" body="No agents are pending review." /> : (
        <div className="mt-6 space-y-4">
          {subs.map((a) => {
            const v = (a as any).validation as { ok: boolean; errors: string[]; warnings: string[] };
            return (
              <div key={a.id} className="rounded-2xl border border-line bg-panel p-5">
                <div className="flex items-start gap-4">
                  <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl text-[20px]" style={{ background: `${a.accent}22` }}>{a.icon}</div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <Link href={`/agents/${a.slug}`} className="text-[15px] font-semibold text-ink hover:text-cy">{a.name}</Link>
                      <span className="rounded bg-white/5 px-1.5 py-0.5 text-[11px] text-dim">{a.category}</span>
                    </div>
                    <p className="mt-1 text-[13px] text-dim">{a.short_description}</p>
                    <div className="mt-2"><GovBadges badges={a.badges} /></div>

                    <div className="mt-3 grid gap-3 sm:grid-cols-2">
                      <div className="rounded-lg border border-line bg-panel2 p-3">
                        <div className="mb-1 text-[10px] uppercase tracking-wider text-faint">Permissions requested</div>
                        {(a.permissions || []).map((p: any) => <div key={p.name} className="text-[12px] text-dim">• {p.name}</div>)}
                        {!(a.permissions || []).length && <div className="text-[12px] text-faint">none declared</div>}
                      </div>
                      <div className={`rounded-lg border p-3 ${v?.ok ? "border-ok/40 bg-ok/10" : "border-warn/40 bg-warn/10"}`}>
                        <div className="mb-1 text-[10px] uppercase tracking-wider text-faint">Manifest validation</div>
                        <div className={`text-[12px] ${v?.ok ? "text-ok" : "text-warn"}`}>{v?.ok ? "✓ valid" : "⚠ issues"}</div>
                        {v?.errors?.map((e) => <div key={e} className="text-[11px] text-bad">• {e}</div>)}
                        {v?.warnings?.slice(0, 3).map((w) => <div key={w} className="text-[11px] text-warn">⚠ {w}</div>)}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="mt-4 flex gap-2">
                  <button onClick={() => act(a, "approve")} disabled={!!busy} className="rounded-lg bg-ok/90 px-4 py-2 text-[13px] font-semibold text-white hover:opacity-90 disabled:opacity-50">Approve & publish</button>
                  <button onClick={() => act(a, "request-changes")} disabled={!!busy} className="rounded-lg border border-line px-4 py-2 text-[13px] text-ink hover:bg-white/5 disabled:opacity-50">Request changes</button>
                  <button onClick={() => act(a, "reject")} disabled={!!busy} className="rounded-lg border border-bad/40 px-4 py-2 text-[13px] text-bad hover:bg-bad/10 disabled:opacity-50">Reject</button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Note({ title, body }: { title: string; body: string }) {
  return <div className="rounded-2xl border border-dashed border-line py-16 text-center"><div className="text-[15px] text-dim">{title}</div><div className="mt-1 text-[13px] text-faint">{body}</div></div>;
}
