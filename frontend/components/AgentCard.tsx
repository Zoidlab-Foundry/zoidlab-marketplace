import Link from "next/link";
import type { Agent } from "../lib/types";
import { VisibilityBadge } from "./Badges";

export default function AgentCard({ agent }: { agent: Agent }) {
  return (
    <Link href={`/agents/${agent.slug}`}
      className="group relative flex flex-col rounded-2xl border border-line bg-panel p-4 transition hover:border-vi/50 hover:shadow-glow">
      <div className="mb-3 flex items-start gap-3">
        <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl text-[22px]"
          style={{ background: `${agent.accent}22`, boxShadow: `inset 0 0 0 1px ${agent.accent}33` }}>
          {agent.icon}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="truncate text-[14px] font-semibold text-ink">{agent.name}</h3>
          </div>
          <div className="mt-0.5 flex items-center gap-2 text-[11px] text-faint">
            <span className="rounded bg-white/5 px-1.5 py-0.5 text-dim">{agent.category}</span>
            <span>· {agent.publisher_name}</span>
          </div>
        </div>
        <VisibilityBadge visibility={agent.visibility} />
      </div>

      <p className="mb-3 line-clamp-2 text-[12.5px] leading-relaxed text-dim">{agent.short_description}</p>

      <div className="mb-3 flex flex-wrap gap-1.5">
        {agent.tags.slice(0, 3).map((t) => (
          <span key={t} className="rounded-md bg-white/5 px-1.5 py-0.5 text-[10px] text-faint">{t}</span>
        ))}
      </div>

      <div className="mt-auto flex items-center justify-between border-t border-line pt-3 text-[11px] text-faint">
        <span className="text-dim">{agent.publisher_name}</span>
        <span>v{agent.version}</span>
      </div>
    </Link>
  );
}
