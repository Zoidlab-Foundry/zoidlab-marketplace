"use client";
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

/* In-app guide: what Marketplace is and how to find, test, install, and publish agents.
   Auto-opens once per browser (localStorage) and lives behind the Guide nav button. */

const STORAGE_KEY = "mp_guide_v1";

const STEPS: { title: string; body: string }[] = [
  {
    title: "Browse the agent catalog",
    body: "Search from the home page or head to Agents — filter by category, sort by installs, rating, or newest. Every card shows governance badges and declared permissions up front, so you know what an agent can access before you open it.",
  },
  {
    title: "Open an agent's listing",
    body: "The detail page lays out everything: Overview with example input/output, Capabilities, Requirements, Permissions, the full Manifest, community Reviews with ratings, and the Versions history.",
  },
  {
    title: "Test it in the sandbox",
    body: "Hit Test in Sandbox on any listing to send a sample input against a mock runtime — you get a simulated response with latency, confidence, and detected intent before you commit to installing.",
  },
  {
    title: "Install or clone",
    body: "Install adds the agent to My Agents, where you can open it in ZoidLab Builder or remove it later. Clone & Customize copies it into your own editable draft so you can adapt it to your workflow.",
  },
  {
    title: "Submit your own agent",
    body: "On Submit (or Import a manifest), package your agent with a category, tags, visibility, and governance settings. Save as a draft or submit — public submissions are validated and enter admin review before going live. Track status under My Agents → Submitted.",
  },
];

export default function HelpGuide() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    try {
      if (!localStorage.getItem(STORAGE_KEY)) setOpen(true);
    } catch {}
  }, []);

  const dismiss = () => {
    try { localStorage.setItem(STORAGE_KEY, "1"); } catch {}
    setOpen(false);
  };

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") dismiss(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="rounded-lg border border-line px-3 py-1.5 text-[12px] text-dim transition hover:text-ink hover:bg-white/5"
        aria-label="Open the Marketplace guide"
      >
        Guide
      </button>
      {open && createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={dismiss} role="dialog" aria-modal="true" aria-label="Marketplace guide">
          <div className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-xl border border-line bg-panel p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="mb-1 flex items-center gap-2">
              <span className="grid h-6 w-6 place-items-center rounded-md bg-vi/15 text-[13px] text-vi">◈</span>
              <h2 className="text-[16px] font-semibold">How Marketplace works</h2>
            </div>
            <p className="mb-5 text-[13px] text-dim">
              The agent app store for Nyquest — discover reusable AI agents, test them safely, and publish your own. Five steps from browsing to shipping:
            </p>
            <ol className="space-y-4">
              {STEPS.map((s, i) => (
                <li key={i} className="flex gap-3">
                  <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-vi/15 text-[12px] font-semibold text-vi">{i + 1}</span>
                  <div>
                    <div className="text-[13.5px] font-medium">{s.title}</div>
                    <div className="text-[12.5px] leading-relaxed text-dim">{s.body}</div>
                  </div>
                </li>
              ))}
            </ol>
            <div className="mt-6 flex items-center justify-between border-t border-line pt-4">
              <a href="https://foundry.zoidlab.ai" className="text-[12px] text-dim hover:text-ink">◈ All Foundry apps</a>
              <button onClick={dismiss} className="rounded-lg bg-vi px-4 py-1.5 text-[12.5px] font-semibold text-white hover:opacity-90">
                Got it
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
