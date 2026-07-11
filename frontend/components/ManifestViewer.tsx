"use client";
import { useState } from "react";

export default function ManifestViewer({ manifest }: { manifest: any }) {
  const [copied, setCopied] = useState(false);
  const text = JSON.stringify(manifest ?? {}, null, 2);
  return (
    <div className="relative">
      <button
        onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1200); }}
        className="absolute right-3 top-3 rounded-md border border-line bg-panel px-2 py-1 text-[11px] text-dim hover:text-ink">
        {copied ? "Copied" : "Copy"}
      </button>
      <pre className="max-h-[520px] overflow-auto rounded-xl border border-line bg-panel2 p-4 text-[12px] leading-relaxed text-dim">
        <code>{text}</code>
      </pre>
    </div>
  );
}
