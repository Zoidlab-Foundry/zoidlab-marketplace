"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api";

const SAMPLE = {
  schema_version: "1.0", agent_id: "my-agent", name: "My Agent", version: "0.1.0",
  description: "What this agent does.", category: "Productivity", tags: ["example"],
  publisher: { name: "You" }, models: [], tools: [], secrets: [],
  permissions: [{ name: "read_documents", description: "Can read inputs." }],
  inputs: { type: "object", properties: { message: { type: "string" } }, required: ["message"] },
  outputs: { type: "object", properties: { response: { type: "string" } } },
  runtime: { entrypoint: "main", type: "workflow", supports_streaming: true },
  governance: { requires_human_approval: false, logs_prompts: true, logs_outputs: true, pii_risk: "low" },
};

export default function ImportPage() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [validation, setValidation] = useState<{ ok: boolean; errors: string[]; warnings: string[] } | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  function parse(): any | null {
    try { return JSON.parse(text); } catch { setErr("Invalid JSON — check for syntax errors."); return null; }
  }

  async function validate() {
    setErr(""); setValidation(null);
    const m = parse(); if (!m) return;
    try { setValidation(await api.validateManifest(m)); } catch (e: any) { setErr(e.message); }
  }

  async function doImport() {
    setErr(""); const m = parse(); if (!m) return;
    setBusy(true);
    try {
      const r = await api.importManifest(m);
      router.push(`/agents/${r.agent.slug}/edit`);
    } catch (e: any) {
      if (e.status === 401) setErr("Sign in from your Nyquest app to import.");
      else setErr(e.message);
    } finally { setBusy(false); }
  }

  function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]; if (!file) return;
    file.text().then(setText);
  }

  return (
    <div className="mx-auto max-w-3xl py-8">
      <h1 className="text-[22px] font-semibold">Import agent manifest</h1>
      <p className="mt-1 text-[13px] text-dim">Paste or upload a <span className="text-ink">Nyquest Agent Manifest</span> (agent.manifest.json). It imports as a private draft you can edit.</p>

      <div className="mt-5 flex items-center gap-3">
        <label className="cursor-pointer rounded-lg border border-line px-4 py-2 text-[13px] text-dim hover:text-ink">
          Upload .json<input type="file" accept="application/json,.json" onChange={onFile} className="hidden" />
        </label>
        <button onClick={() => { setText(JSON.stringify(SAMPLE, null, 2)); setValidation(null); }} className="text-[12px] text-cy hover:underline">Insert sample</button>
      </div>

      <textarea value={text} onChange={(e) => { setText(e.target.value); setValidation(null); }} rows={16}
        placeholder="Paste manifest JSON here…"
        className="mt-4 w-full resize-y rounded-xl border border-line bg-panel2 p-4 font-mono text-[12px] text-ink placeholder-faint outline-none focus:border-vi/60" />

      {err && <div className="mt-3 rounded-lg border border-bad/40 bg-bad/10 px-4 py-2 text-[13px] text-bad">{err}</div>}
      {validation && (
        <div className={`mt-3 rounded-lg border px-4 py-3 text-[13px] ${validation.ok ? "border-ok/40 bg-ok/10" : "border-bad/40 bg-bad/10"}`}>
          <div className={validation.ok ? "text-ok" : "text-bad"}>{validation.ok ? "✓ Manifest is valid" : "✗ Manifest has errors"}</div>
          {validation.errors.map((e) => <div key={e} className="mt-1 text-bad">• {e}</div>)}
          {validation.warnings.map((w) => <div key={w} className="mt-1 text-warn">⚠ {w}</div>)}
        </div>
      )}

      <div className="mt-4 flex gap-3">
        <button onClick={validate} disabled={!text.trim()} className="rounded-lg border border-line px-5 py-2.5 text-[13px] font-semibold text-ink hover:bg-white/5 disabled:opacity-50">Validate</button>
        <button onClick={doImport} disabled={busy || !text.trim()} className="rounded-lg bg-vi px-5 py-2.5 text-[13px] font-semibold text-white hover:opacity-90 disabled:opacity-50">{busy ? "Importing…" : "Import as draft"}</button>
      </div>
    </div>
  );
}
