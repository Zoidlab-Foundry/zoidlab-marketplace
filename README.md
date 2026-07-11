# ZoidLab Marketplace

**Prototype. Package. Deploy AI Agents.** — the agent app store for Nyquest.

A marketplace where users browse, test, install, clone, publish, and (soon) deploy
reusable AI agents across the Nyquest platform. Live at **marketplace.zoidlab.ai**.

The differentiator is **trust**: every listing shows what the agent does, what it can
access, which models it uses, what it may cost, and what risks it carries — with
governance badges and declared permissions up front, no fine print.

## Stack

Aligned to the ZoidLab platform standard (same as the Workflow Builder / Foundry):

- **Frontend** — Next.js 15, React 19, TypeScript, TailwindCSS (dark by default)
- **Backend** — FastAPI (Python), SQLite (Postgres-portable — all access behind
  `database.py`; JSONB columns stored as JSON text)
- **Auth** — the shared ZoidLab / Nyquest SSO cookie (`zb_session`). Browsing is
  public; install / clone / submit / admin require a signed-in Nyquest user.
- **Deploy** — systemd + Cloudflare Tunnel on the ZoidLab host (`marketplace-api`
  on :8300, `marketplace-web` on :3300). A `docker-compose.yml` is included for
  local dev / portability.

## Quick start (local)

```bash
cp .env.example .env          # set BUILDER_SESSION_SECRET

# Backend
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8300   # seeds 10 agents on first boot

# Frontend (new shell)
cd frontend
npm install
npm run dev                    # http://localhost:3300
```

Or with Docker:

```bash
docker compose up --build      # frontend :3300, backend :8300 (SQLite volume)
```

## Environment

| Var | Purpose |
|-----|---------|
| `BUILDER_SESSION_SECRET` | Shared SSO secret — must match the other *.zoidlab.ai apps |
| `MARKETPLACE_API_URL` | Backend URL the frontend proxies `/api/*` to |
| `ENABLE_MOCK_SANDBOX` | `true` (default) uses deterministic mock sandbox responses |
| `MARKETPLACE_ADMINS` | Comma-separated Nyquest user ids/emails allowed into `/admin/review` |
| `NYQUEST_API` | Nyquest API base for SSO token verification |
| `SESSION_COOKIE_DOMAIN` | `.zoidlab.ai` — shared cross-app cookie |

## API overview

Public: `GET /api/agents`, `GET /api/agents/{slug}`, `GET /api/categories`,
`POST /api/agents/{id}/test`.
User: `POST /api/agents/{id}/install`, `DELETE /api/installed-agents/{id}`,
`GET /api/my-agents`, `POST /api/agents/{id}/clone`.
Publish: `POST /api/agents`, `PUT /api/agents/{id}`, `POST /api/agents/{id}/submit`,
`POST /api/import/manifest`, `POST /api/validate/manifest`.
Admin: `GET /api/admin/submissions`, `POST /api/admin/agents/{id}/approve|reject|request-changes`.

## Nyquest Agent Manifest

`agent.manifest.json` (schema_version `1.0`) is the portable package format —
identity, models, tools, secrets, permissions, input/output JSON Schema, runtime,
and a governance block (`pii_risk`, `requires_human_approval`, logging flags).
Validated by `backend/manifest.py`; see any seeded agent's **Manifest** tab for a
complete example.

## Data model

`users`, `organizations`, `agents`, `agent_versions`, `installed_agents`,
`agent_reviews`, `agent_runs` — see `backend/database.py`.

## Deploy notes (marketplace.zoidlab.ai)

Runs as two systemd services behind the shared Cloudflare Tunnel:
`marketplace-web` (Next, :3300) and `marketplace-api` (FastAPI, :8300, localhost).
The frontend proxies `/api/*` to the backend. Add the hostname to the tunnel
ingress and route DNS with `cloudflared tunnel route dns`.

## Future Nyquest integration (placeholder seams)

Deploy agent into the ZoidLab Workflow Builder · package a builder workflow as a
marketplace agent · Nyquest multi-model router · BYOK keys · Compression Engine ·
Splicer · Policy Engine · Memory Studio · RAG Builder · Prompt Studio · Evaluation Lab.
