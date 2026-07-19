"""ZoidLab Agent Marketplace API.

Public browse is unauthenticated; install / clone / submit / my-agents / admin
require the shared ZoidLab session (Nyquest SSO). Owner = the Nyquest user id.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Any

import db_pg as db
import manifest as mf
import sandbox
import seed
from auth import owner_of, session, is_pro as auth_is_pro


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    n = seed.run()
    if n:
        print(f"[marketplace] seeded {n} agents")
    db.normalize_ratings()  # ratings reflect real reviews only (zeroes any seed placeholders)
    yield


app = FastAPI(title="ZoidLab Marketplace API", lifespan=lifespan)


def require_owner(request: Request):
    """Gated actions (install / clone / submit / review) require a signed-in Nyquest
    Pro user — matches the README. Browsing and sandbox test stay public."""
    o = owner_of(request)
    if not o:
        raise HTTPException(status_code=401, detail="sign_in_required")
    if not auth_is_pro(request):
        raise HTTPException(status_code=403, detail="pro_required")
    s = session(request)
    db.upsert_user(o, s.get("email"), s.get("name"))
    return o


def _decorate(agent):
    if agent:
        agent["badges"] = mf.badges(agent)
    return agent


# ---- public marketplace -------------------------------------------------
@app.get("/api/health")
def health():
    return {"ok": True, "agents": len(db.list_agents())}


@app.get("/api/categories")
def categories():
    return {"categories": db.categories()}


@app.get("/api/agents")
def agents(request: Request, search: Optional[str] = None, category: Optional[str] = None,
           tag: Optional[str] = None, visibility: Optional[str] = None, sort: str = "installs"):
    viewer = owner_of(request)
    items = db.list_agents(search=search, category=category, tag=tag, visibility=visibility, sort=sort, viewer=viewer)
    for a in items:
        a["badges"] = mf.badges(a)
    return {"agents": items, "count": len(items)}


@app.get("/api/agents/{slug}")
def agent_detail(slug: str, request: Request):
    a = db.get_agent(slug, viewer=owner_of(request))
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    a["versions"] = db.list_versions(a["id"])
    installed = False
    o = owner_of(request)
    if o:
        installed = any(x["id"] == a["id"] for x in db.my_agents(o)["installed"])
    a["installed"] = installed
    return _decorate(a)


# ---- sandbox ------------------------------------------------------------
class TestBody(BaseModel):
    input: Any = None


@app.post("/api/agents/{aid}/test")
def test_agent(aid: str, body: TestBody, request: Request):
    a = db.get_agent_by_id(aid) or db.get_agent(aid, viewer=owner_of(request))
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    inp = body.input
    text = inp if isinstance(inp, str) else (inp.get("customer_message") or inp.get("message") or inp.get("question")
            or inp.get("prompt") or next(iter(inp.values()), "")) if isinstance(inp, dict) else str(inp or "")
    res = sandbox.run(a, text)
    # Only persist a run row for signed-in users — prevents anonymous callers from
    # inserting unbounded agent_runs rows.
    if owner_of(request):
        db.log_run(a["id"], owner_of(request), {"input": inp}, res["output"], "complete",
                   res["latency_ms"], res["cost_estimate"], res["logs"])
    return res


# ---- reviews ------------------------------------------------------------
class ReviewBody(BaseModel):
    rating: int
    text: Optional[str] = None


@app.get("/api/agents/{aid}/reviews")
def agent_reviews(aid: str, request: Request):
    a = db.get_agent_by_id(aid) or db.get_agent(aid, viewer=owner_of(request))
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    return {"reviews": db.list_reviews(a["id"]), "my_review": db.my_review(a["id"], owner_of(request)),
            "rating_avg": a.get("rating_avg", 0), "rating_count": a.get("rating_count", 0)}


@app.post("/api/agents/{aid}/reviews")
def write_review(aid: str, body: ReviewBody, request: Request):
    owner = require_owner(request)  # Pro sign-in required
    a = db.get_agent_by_id(aid)
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    if not (1 <= int(body.rating) <= 5):
        raise HTTPException(status_code=400, detail="rating_must_be_1_to_5")
    stats = db.add_review(a["id"], owner, body.rating, body.text)
    return {"ok": True, **stats, "reviews": db.list_reviews(a["id"]), "my_review": db.my_review(a["id"], owner)}


# ---- user actions (auth) ------------------------------------------------
class InstallBody(BaseModel):
    config: Optional[dict] = None


@app.post("/api/agents/{aid}/install")
def install(aid: str, body: InstallBody, request: Request):
    o = require_owner(request)
    inst = db.install_agent(aid, o, body.config)
    if not inst:
        raise HTTPException(status_code=404, detail="not_found")
    return {"ok": True, "installed": inst}


@app.delete("/api/installed-agents/{iid}")
def uninstall(iid: str, request: Request):
    o = require_owner(request)
    if not db.uninstall(iid, o):
        raise HTTPException(status_code=404, detail="not_found")
    return {"ok": True}


@app.get("/api/my-agents")
def my_agents(request: Request):
    o = require_owner(request)
    data = db.my_agents(o)
    for group in data.values():
        for a in group:
            a["badges"] = mf.badges(a)
    return data


@app.post("/api/agents/{aid}/clone")
def clone(aid: str, request: Request):
    o = require_owner(request)
    a = db.clone_agent(aid, o)
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    return {"ok": True, "agent": a}


# ---- publishing ---------------------------------------------------------
class AgentDraft(BaseModel):
    name: str
    slug: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list] = None
    icon: Optional[str] = None
    accent: Optional[str] = None
    visibility: Optional[str] = "private"
    version: Optional[str] = "0.1.0"
    manifest: Optional[dict] = None
    required_models: Optional[list] = None
    required_tools: Optional[list] = None
    required_secrets: Optional[list] = None
    permissions: Optional[list] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None


def _slugify(s):
    import re
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:60] or "agent"


@app.post("/api/agents")
def create_agent(draft: AgentDraft, request: Request):
    o = require_owner(request)
    data = draft.model_dump()
    data["slug"] = _slugify(data.get("slug") or data["name"]) + "--" + db.uuid.uuid4().hex[:6]
    if data.get("manifest"):
        data["risk"] = mf.risk_from_manifest(data["manifest"])
    s = session(request)
    data["publisher_name"] = s.get("name") or "You"
    data["status"] = "draft"
    a = db.create_agent(data, o)
    return {"ok": True, "agent": a}


@app.put("/api/agents/{aid}")
def update_agent(aid: str, draft: AgentDraft, request: Request):
    o = require_owner(request)
    data = {k: v for k, v in draft.model_dump().items() if v is not None}
    if data.get("manifest"):
        data["risk"] = mf.risk_from_manifest(data["manifest"])
    a = db.update_agent(aid, data, o)
    if not a:
        raise HTTPException(status_code=404, detail="not_found_or_forbidden")
    return {"ok": True, "agent": a}


@app.post("/api/agents/{aid}/submit")
def submit_agent(aid: str, request: Request):
    o = require_owner(request)
    a = db.get_agent_by_id(aid)
    if not a or a["publisher_user_id"] != o:
        raise HTTPException(status_code=404, detail="not_found_or_forbidden")
    v = mf.validate(a.get("manifest") or {})
    if not v["ok"]:
        return JSONResponse({"ok": False, "validation": v}, status_code=400)
    a = db.set_status(aid, "pending", o, require_owner=True)
    return {"ok": True, "agent": a, "validation": v}


class ManifestBody(BaseModel):
    manifest: dict


@app.post("/api/validate/manifest")
def validate_manifest(body: ManifestBody):
    return mf.validate(body.manifest)


@app.post("/api/import/manifest")
def import_manifest(body: ManifestBody, request: Request):
    o = require_owner(request)
    v = mf.validate(body.manifest)
    if not v["ok"]:
        return JSONResponse({"ok": False, "validation": v}, status_code=400)
    row = mf.to_agent_row(body.manifest, publisher_name=(session(request) or {}).get("name"))
    row["slug"] = _slugify(body.manifest.get("agent_id") or row["name"]) + "--" + db.uuid.uuid4().hex[:6]
    row["visibility"] = "private"
    row["status"] = "draft"
    row["icon"] = "◆"
    a = db.create_agent(row, o)
    return {"ok": True, "agent": a, "validation": v}


# ---- admin review -------------------------------------------------------
def require_admin(request: Request):
    o = require_owner(request)
    if not db.is_admin(o):
        raise HTTPException(status_code=403, detail="admin_only")
    return o


@app.get("/api/admin/submissions")
def admin_submissions(request: Request):
    require_admin(request)
    subs = db.admin_submissions()
    for a in subs:
        a["badges"] = mf.badges(a)
        a["validation"] = mf.validate(a.get("manifest") or {})
    return {"submissions": subs}


@app.get("/api/admin/is-admin")
def admin_check(request: Request):
    o = owner_of(request)
    return {"admin": db.is_admin(o) if o else False}


@app.post("/api/admin/agents/{aid}/approve")
def approve(aid: str, request: Request):
    require_admin(request)
    a = db.get_agent_by_id(aid)
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    # approving publishes it to the marketplace
    db.set_status(aid, "published")
    a = db.update_agent(aid, {"visibility": "public"}, owner=a["publisher_user_id"])
    return {"ok": True, "agent": db.get_agent_by_id(aid)}


class RejectBody(BaseModel):
    reason: Optional[str] = None


@app.post("/api/admin/agents/{aid}/reject")
def reject(aid: str, body: RejectBody, request: Request):
    require_admin(request)
    a = db.set_status(aid, "rejected")
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    return {"ok": True, "agent": a}


@app.post("/api/admin/agents/{aid}/request-changes")
def request_changes(aid: str, body: RejectBody, request: Request):
    require_admin(request)
    a = db.set_status(aid, "draft")
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    return {"ok": True, "agent": a}


@app.get("/api/whoami")
def whoami(request: Request):
    s = session(request)
    if not s:
        return {"authenticated": False}
    return {"authenticated": True, "email": s.get("email"), "name": s.get("name"),
            "tier": s.get("tier"), "admin": db.is_admin(s.get("sub"))}
