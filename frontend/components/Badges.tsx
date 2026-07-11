import { RISK_STYLE, VISIBILITY_STYLE } from "../lib/categories";

const BADGE_STYLE: Record<string, string> = {
  "Low Risk": RISK_STYLE.low,
  "Medium Risk": RISK_STYLE.medium,
  "High Risk": RISK_STYLE.high,
  "Requires Secrets": "text-warn border-warn/40 bg-warn/10",
  "External API Access": "text-ind border-ind/40 bg-ind/10",
  "Human Approval Recommended": "text-vi border-vi/40 bg-vi/10",
  "PII Risk": "text-bad border-bad/40 bg-bad/10",
  "Logs Prompts": "text-dim border-line bg-white/5",
  "Logs Outputs": "text-dim border-line bg-white/5",
};

export function Badge({ label, className = "" }: { label: string; className?: string }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium ${className}`}>
      {label}
    </span>
  );
}

export function GovBadges({ badges, max }: { badges?: string[]; max?: number }) {
  if (!badges?.length) return null;
  const shown = max ? badges.slice(0, max) : badges;
  return (
    <div className="flex flex-wrap gap-1.5">
      {shown.map((b) => <Badge key={b} label={b} className={BADGE_STYLE[b] || "text-dim border-line bg-white/5"} />)}
    </div>
  );
}

export function VisibilityBadge({ visibility }: { visibility: string }) {
  const label = visibility === "verified" ? "Nyquest Verified" : visibility[0].toUpperCase() + visibility.slice(1);
  return <Badge label={label} className={VISIBILITY_STYLE[visibility] || VISIBILITY_STYLE.private} />;
}
