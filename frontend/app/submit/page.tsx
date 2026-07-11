"use client";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api";
import { CATEGORIES } from "../../lib/categories";

const VISIBILITIES = [
  { v: "private", label: "Private" },
  { v: "organization", label: "Organization" },
  { v: "public", label: "Public Marketplace" },
  { v: "verified", label: "Nyquest Verified" },
];

export default function Submit() {
  const router = useRouter();
  const [f, setF] = useState({
    name: "", short_description: "", long_description: "", category: "Customer Support",
    tags: "", icon: "◆", visibility: "public", version: "0.1.0",
  });
  const [pii, setPii] = useState("low");
  const [approval, setApproval] = useState(false);
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const set = (k: string, v: any) => setF((s) => ({ ...s, [k]: v }));

  const manifest = useMemo(() => ({
    schema_version: "1.0",
    agent_id: (f.name || "agent").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""),
    name: f.name, version: f.version, description: f.short_description,
    long_description: f.long_description, category: f.category,
    tags: f.tags.split(",").map((t) => t.trim()).filter(Boolean),
    publisher: { name: "You" },
    models: [], tools: [], secrets: [],
    permissions: [{ name: "read_documents", description: "Can read inputs provided to the agent." }],
    inputs: { type: "object", properties: { message: { type: "string" } }, required: ["message"] },
    outputs: { type: "object", properties: { response: { type: "string" }, intent: { type: "string" }, confidence: { type: "number" } } },
    runtime: { entrypoint: "main", type: "workflow", supports_streaming: true },
    governance: { requires_human_approval: approval, logs_prompts: true, logs_outputs: true, pii_risk: pii },
  }), [f, pii, approval]);

  async function go(submit: boolean) {
    if (!f.name.trim()) { setMsg({ kind: "err", text: "Name is required." }); return; }
    setBusy(submit ? "submit" : "draft"); setMsg(null);
    try {
      const draft = {
        name: f.name, short_description: f.short_description, long_description: f.long_description,
        category: f.category, tags: manifest.tags, icon: f.icon, visibility: f.visibility,
        version: f.version, manifest,
        required_models: manifest.models, required_tools: manifest.tools,
        required_secrets: manifest.secrets, permissions: manifest.permissions,
        input_schema: manifest.inputs, output_schema: manifest.outputs,
      };
      const { agent } = await api.create(draft);
      if (submit) {
        const r = await api.submit(agent.id);
        if (r.ok === false) { setMsg({ kind: "err", text: "Validation failed: " + (r.validation?.errors || []).join("; ") }); setBusy(""); return; }
        setMsg({ kind: "ok", text: "Submitted for review. Track it under My Agents → Submitted." });
      } else {
        setMsg({ kind: "ok", text: "Draft saved. Continue editing under My Agents." });
      }
      setTimeout(() => router.push(`/agents/${agent.slug}/edit`), 900);
    } catch (e: any) {
      setMsg({ kind: "err", text: e.status === 401 ? "Sign in from your Nyquest app to publish." : e.message });
    } finally { setBusy(""); }
  }

  return (
    <div className="mx-auto max-w-3xl py-8">
      <h1 className="text-[22px] font-semibold">Submit an agent</h1>
      <p className="mt-1 text-[13px] text-dim">Package a reusable agent for the marketplace. Public submissions enter review before they go live.</p>
      <div className="mt-3 text-[12px]"><a href="/import" className="text-cy hover:underline">…or import an existing agent manifest →</a></div>

      <div className="mt-6 space-y-5">
        <div className="grid gap-4 sm:grid-cols-[80px_1fr]">
          <Field label="Icon"><input value={f.icon} onChange={(e) => set("icon", e.target.value)} className={inp + " text-center text-[20px]"} maxLength={2} /></Field>
          <Field label="Agent name"><input value={f.name} onChange={(e) => set("name", e.target.value)} placeholder="Restaurant Concierge" className={inp} /></Field>
        </div>
        <Field label="Short description"><input value={f.short_description} onChange={(e) => set("short_description", e.target.value)} placeholder="One line shown on the card." className={inp} /></Field>
        <Field label="Long description"><textarea value={f.long_description} onChange={(e) => set("long_description", e.target.value)} rows={4} placeholder="What it does, who it's for, how it behaves." className={inp} /></Field>
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Category">
            <select value={f.category} onChange={(e) => set("category", e.target.value)} className={inp}>
              {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </Field>
          <Field label="Version"><input value={f.version} onChange={(e) => set("version", e.target.value)} className={inp} /></Field>
          <Field label="Visibility">
            <select value={f.visibility} onChange={(e) => set("visibility", e.target.value)} className={inp}>
              {VISIBILITIES.map((v) => <option key={v.v} value={v.v}>{v.label}</option>)}
            </select>
          </Field>
        </div>
        <Field label="Tags (comma-separated)"><input value={f.tags} onChange={(e) => set("tags", e.target.value)} placeholder="restaurant, concierge, reservations" className={inp} /></Field>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="PII risk">
            <select value={pii} onChange={(e) => setPii(e.target.value)} className={inp}>
              {["none", "low", "medium", "high"].map((p) => <option key={p}>{p}</option>)}
            </select>
          </Field>
          <Field label="Human approval">
            <label className="flex items-center gap-2 rounded-xl border border-line bg-panel px-3 py-2.5 text-[13px] text-dim">
              <input type="checkbox" checked={approval} onChange={(e) => setApproval(e.target.checked)} /> Recommended before actions
            </label>
          </Field>
        </div>

        <details className="rounded-xl border border-line bg-panel2 p-4">
          <summary className="cursor-pointer text-[13px] text-dim">Preview generated manifest</summary>
          <pre className="mt-3 max-h-72 overflow-auto text-[11px] text-faint">{JSON.stringify(manifest, null, 2)}</pre>
        </details>

        {msg && <div className={`rounded-lg border px-4 py-2 text-[13px] ${msg.kind === "ok" ? "border-ok/40 bg-ok/10 text-ok" : "border-bad/40 bg-bad/10 text-bad"}`}>{msg.text}</div>}

        <div className="flex gap-3">
          <button onClick={() => go(false)} disabled={!!busy} className="rounded-lg border border-line px-5 py-2.5 text-[13px] font-semibold text-ink hover:bg-white/5 disabled:opacity-50">
            {busy === "draft" ? "Saving…" : "Save draft"}
          </button>
          <button onClick={() => go(true)} disabled={!!busy} className="rounded-lg bg-vi px-5 py-2.5 text-[13px] font-semibold text-white hover:opacity-90 disabled:opacity-50">
            {busy === "submit" ? "Submitting…" : "Submit for review"}
          </button>
        </div>
      </div>
    </div>
  );
}

const inp = "w-full rounded-xl border border-line bg-panel px-3 py-2.5 text-[13px] text-ink placeholder-faint outline-none focus:border-vi/60";
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block"><span className="mb-1.5 block text-[12px] text-faint">{label}</span>{children}</label>;
}
