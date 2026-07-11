import type { Agent } from "../lib/types";
import AgentCard from "./AgentCard";

export default function AgentGrid({ agents, empty }: { agents: Agent[]; empty?: string }) {
  if (!agents.length) {
    return <div className="rounded-2xl border border-dashed border-line py-16 text-center text-[13px] text-faint">{empty || "No agents found."}</div>;
  }
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {agents.map((a) => <AgentCard key={a.id} agent={a} />)}
    </div>
  );
}
