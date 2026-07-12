"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "../../../../lib/api";
import type { Agent } from "../../../../lib/types";
import { CATEGORIES } from "../../../../lib/categories";

export default function EditAgent() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [manifestText, setManifestText] = useState("");
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [validation, setValidation] = useState<{ ok: boolean; errors: string[]; warnings: string[] } | null>(null);

  useEffect(() => {
    api.agent(slug).then((a) => { setAgent(a); setManifestText(JSON.stringify(a.manifest ?? {}, null, 2)); })
      .catch((e) => setMsg({ kind: "err", text: e.status === 404 ? "Not found or not yours to edit." : e.message }));
  }, [slug]);

  if (!agent) return <div className="py-24 text-center text-faint">{msg?.text || "Loading…"}</div>;

  const set = (k: keyof Agent, v: any) => setAgent({ ...agent, [k]: v });

  function parseManifest(): any | null {
    try { return JSON.parse(manifestText); } catch { setMsg({ kind: "err", text: "Manifest is not valid JSON." }); return null; }
  }

  async function save(then?: "submit") {
    const manifest = parseManifest(); if (!manifest) return;
    setBusy(then || "save"); setMsg(null);
    try {
      await api.update(agent!.id, {
        name: agent!.name, short_description: agent!.short_description, long_description: agent!.long_description,
        category: agent!.category, visibility: agent!.visibility, version: agent!.version,
        tags: manifest.tags || agent!.tags, manifest,
        required_models: manifest.models, required_tools: manifest.tools, required_secrets: manifest.secrets,
        permissions: manifest.permissions, input_schema: manifest.inputs, output_schema: manifest.outputs,
      });
      if (then === "submit") {
        const r = await api.submit(agent!.id);
        if (r.ok === false) { setMsg({ kind: "err", text: "Cannot submit: " + (r.validation?.errors || []).join("; ") }); setBusy(""); return; }
        setMsg({ kind: "ok", text: "Submitted for review." });
      } else {
        setMsg({ kind: "ok", text: "Saved." });
      }
    } catch (e: any) {
      setMsg({ kind: "err", text: e.status === 401 ? "Sign in required." : e.message });
    } finally { setBusy(""); }
  }

  async function validate() {
    const m = parseManifest(); if (!m) return;
    try { setValidation(await api.validateManifest(m)); } catch (e: any) { setMsg({ kind: "err", text: e.message }); }
  }

  return (
    <div className="mx-auto max-w-3xl py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-[22px] font-semibold">Edit agent</h1>
        <Link href={`/agents/${agent.slug}`} className="text-[12px] text-cy hover:underline">View listing →</Link>
      </div>
      <p className="mt-1 text-[13px] text-dim">Status: <span className="text-ink">{agent.status}</span> · visibility: {agent.visibility}</p>

      <div className="mt-6 space-y-5">
        <Field label="Name"><input value={agent.name} onChange={(e) => set("name", e.target.value)} className={inp} /></Field>
        <Field label="Short description"><input value={agent.short_description} onChange={(e) => set("short_description", e.target.value)} className={inp} /></Field>
        <Field label="Long description"><textarea value={agent.long_description || ""} onChange={(e) => set("long_description", e.target.value)} rows={4} className={inp} /></Field>
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Category"><select value={agent.category} onChange={(e) => set("category", e.target.value)} className={inp}>{CATEGORIES.map((c) => <option key={c}>{c}</option>)}</select></Field>
          <Field label="Version"><input value={agent.version} onChange={(e) => set("version", e.target.value)} className={inp} /></Field>
          <Field label="Visibility">
            <select value={agent.visibility} onChange={(e) => set("visibility", e.target.value as any)} className={inp}>
              {["private", "public", "verified"].map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
          </Field>
        </div>

        <Field label="Manifest (agent.manifest.json)">
          <textarea value={manifestText} onChange={(e) => { setManifestText(e.target.value); setValidation(null); }} rows={16}
            className={inp + " font-mono text-[12px]"} />
        </Field>

        {validation && (
          <div className={`rounded-lg border px-4 py-3 text-[13px] ${validation.ok ? "border-ok/40 bg-ok/10" : "border-bad/40 bg-bad/10"}`}>
            <div className={validation.ok ? "text-ok" : "text-bad"}>{validation.ok ? "✓ Valid manifest" : "✗ Errors"}</div>
            {validation.errors.map((e) => <div key={e} className="mt-1 text-bad">• {e}</div>)}
            {validation.warnings.map((w) => <div key={w} className="mt-1 text-warn">⚠ {w}</div>)}
          </div>
        )}
        {msg && <div className={`rounded-lg border px-4 py-2 text-[13px] ${msg.kind === "ok" ? "border-ok/40 bg-ok/10 text-ok" : "border-bad/40 bg-bad/10 text-bad"}`}>{msg.text}</div>}

        <div className="flex flex-wrap gap-3">
          <button onClick={validate} className="rounded-lg border border-line px-4 py-2.5 text-[13px] text-ink hover:bg-white/5">Validate manifest</button>
          <button onClick={() => save()} disabled={!!busy} className="rounded-lg border border-line px-5 py-2.5 text-[13px] font-semibold text-ink hover:bg-white/5 disabled:opacity-50">{busy === "save" ? "Saving…" : "Save"}</button>
          <button onClick={() => save("submit")} disabled={!!busy} className="rounded-lg bg-vi px-5 py-2.5 text-[13px] font-semibold text-white hover:opacity-90 disabled:opacity-50">{busy === "submit" ? "Submitting…" : "Save & submit for review"}</button>
        </div>
      </div>
    </div>
  );
}

const inp = "w-full rounded-xl border border-line bg-panel px-3 py-2.5 text-[13px] text-ink placeholder-faint outline-none focus:border-vi/60";
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block"><span className="mb-1.5 block text-[12px] text-faint">{label}</span>{children}</label>;
}
