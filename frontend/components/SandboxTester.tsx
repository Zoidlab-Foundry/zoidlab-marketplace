"use client";
import { useState } from "react";
import { api } from "../lib/api";
import type { Agent, TestResult } from "../lib/types";

function exampleInput(agent: Agent): string {
  const ex = agent.manifest?.examples?.input;
  if (ex && typeof ex === "object") {
    const v = Object.values(ex)[0];
    if (typeof v === "string") return v;
  }
  return "";
}

export default function SandboxTester({ agent }: { agent: Agent }) {
  const [input, setInput] = useState(exampleInput(agent));
  const [result, setResult] = useState<TestResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function run() {
    setBusy(true); setErr(""); setResult(null);
    try {
      setResult(await api.test(agent.id, input));
    } catch (e: any) {
      setErr(e.message || "Test failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-2xl border border-line bg-panel p-5">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-[14px] font-semibold text-ink">Test in Sandbox</h3>
        <span className="rounded-full border border-line px-2 py-0.5 text-[10px] text-faint">mock runtime</span>
      </div>
      <p className="mb-3 text-[12px] text-dim">Send a sample input and see a simulated response. Connect real Nyquest routing after install.</p>
      <textarea value={input} onChange={(e) => setInput(e.target.value)} rows={3}
        placeholder="Type a sample message…"
        className="w-full resize-y rounded-xl border border-line bg-panel2 p-3 text-[13px] text-ink placeholder-faint outline-none focus:border-vi/60" />
      <div className="mt-3 flex items-center gap-3">
        <button onClick={run} disabled={busy || !input.trim()}
          className="rounded-lg bg-vi px-4 py-2 text-[13px] font-semibold text-white hover:opacity-90 disabled:opacity-40">
          {busy ? "Running…" : "Run test"}
        </button>
        {result && <span className="text-[11px] text-faint">{result.latency_ms} ms · conf {(result.output.confidence * 100).toFixed(0)}% · {result.output.intent}</span>}
      </div>
      {err && <p className="mt-3 text-[12px] text-bad">{err}</p>}
      {result && (
        <div className="mt-4 space-y-3">
          <div className="rounded-xl border border-line bg-panel2 p-3">
            <div className="mb-1 text-[10px] uppercase tracking-wider text-cy">response</div>
            <p className="text-[13px] leading-relaxed text-ink">{result.output.response}</p>
          </div>
          <details className="rounded-xl border border-line bg-panel2 p-3">
            <summary className="cursor-pointer text-[11px] text-dim">Raw output + logs</summary>
            <pre className="mt-2 overflow-auto text-[11px] text-faint">{JSON.stringify(result.output, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );
}
