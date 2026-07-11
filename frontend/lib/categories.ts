// Canonical category list (Submit/Edit forms). Live counts come from the API.
export const CATEGORIES = [
  "Restaurant", "Legal", "Medical", "Education", "University", "Network Operations",
  "Finance", "Sales", "Customer Support", "Marketing", "HR", "Security",
  "Developer Tools", "Research", "Personal Productivity", "Productivity", "Governance",
];

export const RISK_STYLE: Record<string, string> = {
  low: "text-ok border-ok/40 bg-ok/10",
  medium: "text-warn border-warn/40 bg-warn/10",
  high: "text-bad border-bad/40 bg-bad/10",
};

export const VISIBILITY_STYLE: Record<string, string> = {
  verified: "text-cy border-cy/40 bg-cy/10",
  public: "text-ind border-ind/40 bg-ind/10",
  private: "text-dim border-line bg-white/5",
  organization: "text-vi border-vi/40 bg-vi/10",
};
