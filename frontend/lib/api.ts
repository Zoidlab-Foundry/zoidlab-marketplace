import type { Agent, Category, TestResult, WhoAmI } from "./types";

// Same-origin calls; /api/* is proxied to the FastAPI backend, cookie flows automatically.
async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!r.ok) {
    let detail = `HTTP ${r.status}`;
    try { detail = (await r.json()).detail || detail; } catch {}
    const err = new Error(detail) as Error & { status?: number };
    err.status = r.status;
    throw err;
  }
  return r.json();
}

export const api = {
  whoami: () => req<WhoAmI>("/api/whoami"),
  categories: () => req<{ categories: Category[] }>("/api/categories").then((d) => d.categories),
  agents: (q: Record<string, string> = {}) => {
    const qs = new URLSearchParams(Object.entries(q).filter(([, v]) => v)).toString();
    return req<{ agents: Agent[]; count: number }>(`/api/agents${qs ? "?" + qs : ""}`);
  },
  agent: (slug: string) => req<Agent>(`/api/agents/${slug}`),
  test: (id: string, input: any) =>
    req<TestResult>(`/api/agents/${id}/test`, { method: "POST", body: JSON.stringify({ input }) }),
  install: (id: string, config?: any) =>
    req<{ ok: boolean; installed: any }>(`/api/agents/${id}/install`, { method: "POST", body: JSON.stringify({ config }) }),
  uninstall: (installId: string) =>
    req<{ ok: boolean }>(`/api/installed-agents/${installId}`, { method: "DELETE" }),
  myAgents: () => req<{ installed: Agent[]; created: Agent[] }>("/api/my-agents"),
  clone: (id: string) => req<{ ok: boolean; agent: Agent }>(`/api/agents/${id}/clone`, { method: "POST" }),
  create: (draft: any) => req<{ ok: boolean; agent: Agent }>("/api/agents", { method: "POST", body: JSON.stringify(draft) }),
  update: (id: string, draft: any) => req<{ ok: boolean; agent: Agent }>(`/api/agents/${id}`, { method: "PUT", body: JSON.stringify(draft) }),
  submit: (id: string) => req<any>(`/api/agents/${id}/submit`, { method: "POST" }),
  validateManifest: (manifest: any) => req<{ ok: boolean; errors: string[]; warnings: string[] }>("/api/validate/manifest", { method: "POST", body: JSON.stringify({ manifest }) }),
  importManifest: (manifest: any) => req<{ ok: boolean; agent: Agent; validation: any }>("/api/import/manifest", { method: "POST", body: JSON.stringify({ manifest }) }),
  submissions: () => req<{ submissions: Agent[] }>("/api/admin/submissions"),
  approve: (id: string) => req<any>(`/api/admin/agents/${id}/approve`, { method: "POST" }),
  reject: (id: string, reason?: string) => req<any>(`/api/admin/agents/${id}/reject`, { method: "POST", body: JSON.stringify({ reason }) }),
  requestChanges: (id: string, reason?: string) => req<any>(`/api/admin/agents/${id}/request-changes`, { method: "POST", body: JSON.stringify({ reason }) }),
};
