"""SQLite persistence for the ZoidLab Agent Marketplace.

Lean by design and Postgres-portable — every JSONB column is stored as TEXT
(json-encoded) and all access goes through these helpers, so a later swap to
Postgres/SQLAlchemy touches only this file. Ownership is the Nyquest user id
(session `sub`); public reads are unscoped, user actions are owner-scoped.
"""
import os
import json
import uuid
import sqlite3
import datetime

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "marketplace.db")


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def new_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def _j(v):
    return json.dumps(v if v is not None else None)


def _pj(v, default=None):
    if v is None:
        return default
    try:
        return json.loads(v)
    except Exception:
        return default


# JSONB-ish agent columns, decoded on the way out.
_AGENT_JSON = ["tags", "manifest", "required_models", "required_tools",
               "required_secrets", "permissions", "input_schema", "output_schema"]


def init():
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT,
                name TEXT,
                role TEXT DEFAULT 'user',
                org_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS organizations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                short_description TEXT,
                long_description TEXT,
                category TEXT,
                tags TEXT,
                icon TEXT,
                accent TEXT,
                publisher_name TEXT,
                publisher_user_id TEXT,
                publisher_org_id TEXT,
                visibility TEXT NOT NULL DEFAULT 'public',
                status TEXT NOT NULL DEFAULT 'published',
                version TEXT NOT NULL DEFAULT '0.1.0',
                manifest TEXT,
                required_models TEXT,
                required_tools TEXT,
                required_secrets TEXT,
                permissions TEXT,
                input_schema TEXT,
                output_schema TEXT,
                risk TEXT DEFAULT 'low',
                featured INTEGER NOT NULL DEFAULT 0,
                install_count INTEGER NOT NULL DEFAULT 0,
                rating_avg REAL NOT NULL DEFAULT 0,
                rating_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_agents_cat ON agents(category);
            CREATE INDEX IF NOT EXISTS idx_agents_owner ON agents(publisher_user_id);
            CREATE TABLE IF NOT EXISTS agent_versions (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                version TEXT NOT NULL,
                changelog TEXT,
                manifest TEXT,
                created_by TEXT,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_versions_agent ON agent_versions(agent_id, created_at);
            CREATE TABLE IF NOT EXISTS installed_agents (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                org_id TEXT,
                agent_id TEXT NOT NULL,
                agent_version_id TEXT,
                installed_config TEXT,
                status TEXT NOT NULL DEFAULT 'installed',
                installed_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_installed_user ON installed_agents(user_id);
            CREATE TABLE IF NOT EXISTS agent_reviews (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                rating INTEGER NOT NULL,
                review_text TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS agent_runs (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                installed_agent_id TEXT,
                user_id TEXT,
                input TEXT,
                output TEXT,
                status TEXT NOT NULL,
                logs TEXT,
                cost_estimate REAL,
                latency_ms INTEGER,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_runs_agent ON agent_runs(agent_id, created_at);
            """
        )


# --- users -------------------------------------------------------------
def upsert_user(uid, email=None, name=None):
    if not uid:
        return
    now = now_iso()
    with _conn() as c:
        c.execute(
            """INSERT INTO users (id, email, name, role, created_at, updated_at)
               VALUES (?,?,?,'user',?,?)
               ON CONFLICT(id) DO UPDATE SET email=COALESCE(excluded.email, users.email),
                 name=COALESCE(excluded.name, users.name), updated_at=excluded.updated_at""",
            (uid, email, name, now, now),
        )


def is_admin(uid):
    if not uid:
        return False
    admins = [a.strip() for a in os.environ.get("MARKETPLACE_ADMINS", "").split(",") if a.strip()]
    if uid in admins:
        return True
    with _conn() as c:
        r = c.execute("SELECT role, email FROM users WHERE id=?", (uid,)).fetchone()
    if not r:
        return False
    return r["role"] == "admin" or (r["email"] and r["email"] in admins)


# --- agents ------------------------------------------------------------
def _agent_out(row, full=False):
    if not row:
        return None
    d = dict(row)
    for k in _AGENT_JSON:
        d[k] = _pj(d.get(k), [] if k in ("tags", "required_models", "required_tools", "required_secrets", "permissions") else {})
    d["featured"] = bool(d.get("featured"))
    if not full:
        d.pop("long_description", None)
        d.pop("manifest", None)
        d.pop("input_schema", None)
        d.pop("output_schema", None)
    return d


VISIBLE_PUBLIC = ("public", "verified")


def list_agents(search=None, category=None, tag=None, visibility=None, sort="installs", viewer=None):
    q = "SELECT * FROM agents WHERE status IN ('published','approved')"
    args = []
    # marketplace listing = public/verified agents, plus the viewer's own
    if viewer:
        q += " AND (visibility IN ('public','verified') OR publisher_user_id=?)"
        args.append(viewer)
    else:
        q += " AND visibility IN ('public','verified')"
    if category and category.lower() != "all":
        q += " AND lower(category)=lower(?)"; args.append(category)
    if visibility:
        q += " AND visibility=?"; args.append(visibility)
    if search:
        q += " AND (lower(name) LIKE ? OR lower(short_description) LIKE ? OR lower(tags) LIKE ?)"
        s = f"%{search.lower()}%"; args += [s, s, s]
    if tag:
        q += " AND lower(tags) LIKE ?"; args.append(f'%"{tag.lower()}"%')
    order = {"newest": "created_at DESC", "installs": "install_count DESC",
             "rating": "rating_avg DESC, rating_count DESC", "name": "name ASC"}.get(sort, "install_count DESC")
    q += f" ORDER BY {order}"
    with _conn() as c:
        rows = c.execute(q, args).fetchall()
    out = [_agent_out(r) for r in rows]
    if tag:  # exact tag membership (LIKE was a coarse prefilter)
        out = [a for a in out if tag.lower() in [t.lower() for t in a.get("tags", [])]]
    return out


def get_agent(slug, viewer=None):
    with _conn() as c:
        r = c.execute("SELECT * FROM agents WHERE slug=?", (slug,)).fetchone()
    a = _agent_out(r, full=True)
    if not a:
        return None
    if a["visibility"] not in VISIBLE_PUBLIC and a["publisher_user_id"] != viewer and not is_admin(viewer):
        return None
    return a


def get_agent_by_id(aid):
    with _conn() as c:
        r = c.execute("SELECT * FROM agents WHERE id=?", (aid,)).fetchone()
    return _agent_out(r, full=True)


def categories():
    with _conn() as c:
        rows = c.execute(
            """SELECT category, COUNT(*) n FROM agents
               WHERE status IN ('published','approved') AND visibility IN ('public','verified')
               GROUP BY category ORDER BY n DESC"""
        ).fetchall()
    return [{"name": r["category"], "count": r["n"]} for r in rows if r["category"]]


def create_agent(data, owner):
    aid = data.get("id") or new_id("agent")
    now = now_iso()
    with _conn() as c:
        c.execute(
            """INSERT INTO agents (id,name,slug,short_description,long_description,category,tags,icon,accent,
                 publisher_name,publisher_user_id,publisher_org_id,visibility,status,version,manifest,
                 required_models,required_tools,required_secrets,permissions,input_schema,output_schema,risk,
                 featured,install_count,rating_avg,rating_count,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (aid, data["name"], data["slug"], data.get("short_description"), data.get("long_description"),
             data.get("category"), _j(data.get("tags", [])), data.get("icon", "◆"), data.get("accent", "#7c5cfc"),
             data.get("publisher_name", "Community"), owner, data.get("publisher_org_id"),
             data.get("visibility", "private"), data.get("status", "draft"), data.get("version", "0.1.0"),
             _j(data.get("manifest", {})), _j(data.get("required_models", [])), _j(data.get("required_tools", [])),
             _j(data.get("required_secrets", [])), _j(data.get("permissions", [])),
             _j(data.get("input_schema", {})), _j(data.get("output_schema", {})), data.get("risk", "low"),
             1 if data.get("featured") else 0, 0, 0, 0, now, now),
        )
        c.execute("INSERT INTO agent_versions (id,agent_id,version,changelog,manifest,created_by,created_at) VALUES (?,?,?,?,?,?,?)",
                  (new_id("ver"), aid, data.get("version", "0.1.0"), "Initial version", _j(data.get("manifest", {})), owner, now))
    return get_agent_by_id(aid)


def update_agent(aid, data, owner):
    with _conn() as c:
        r = c.execute("SELECT publisher_user_id, status FROM agents WHERE id=?", (aid,)).fetchone()
        if not r or (r["publisher_user_id"] != owner and not is_admin(owner)):
            return None
        fields, args = [], []
        for col in ("name", "short_description", "long_description", "category", "visibility", "version", "icon", "accent", "risk"):
            if col in data:
                fields.append(f"{col}=?"); args.append(data[col])
        for col in ("tags", "manifest", "required_models", "required_tools", "required_secrets", "permissions", "input_schema", "output_schema"):
            if col in data:
                fields.append(f"{col}=?"); args.append(_j(data[col]))
        fields.append("updated_at=?"); args.append(now_iso())
        args.append(aid)
        c.execute(f"UPDATE agents SET {', '.join(fields)} WHERE id=?", args)
    return get_agent_by_id(aid)


def set_status(aid, status, owner=None, require_owner=False):
    with _conn() as c:
        r = c.execute("SELECT publisher_user_id FROM agents WHERE id=?", (aid,)).fetchone()
        if not r:
            return None
        if require_owner and r["publisher_user_id"] != owner and not is_admin(owner):
            return None
        c.execute("UPDATE agents SET status=?, updated_at=? WHERE id=?", (status, now_iso(), aid))
    return get_agent_by_id(aid)


def clone_agent(aid, owner):
    src = get_agent_by_id(aid)
    if not src:
        return None
    base = src["slug"].split("--")[0]
    data = {
        "name": src["name"] + " (copy)",
        "slug": f"{base}--{uuid.uuid4().hex[:6]}",
        "short_description": src["short_description"],
        "long_description": src["long_description"],
        "category": src["category"], "tags": src["tags"], "icon": src["icon"], "accent": src["accent"],
        "publisher_name": "You", "visibility": "private", "status": "draft", "version": src["version"],
        "manifest": src["manifest"], "required_models": src["required_models"],
        "required_tools": src["required_tools"], "required_secrets": src["required_secrets"],
        "permissions": src["permissions"], "input_schema": src["input_schema"],
        "output_schema": src["output_schema"], "risk": src["risk"],
    }
    return create_agent(data, owner)


def list_versions(aid):
    with _conn() as c:
        rows = c.execute("SELECT id,version,changelog,created_at FROM agent_versions WHERE agent_id=? ORDER BY created_at DESC", (aid,)).fetchall()
    return [dict(r) for r in rows]


# --- installs ----------------------------------------------------------
def install_agent(aid, owner, config=None):
    a = get_agent_by_id(aid)
    if not a:
        return None
    now = now_iso()
    with _conn() as c:
        existing = c.execute("SELECT id FROM installed_agents WHERE user_id=? AND agent_id=?", (owner, aid)).fetchone()
        if existing:
            iid = existing["id"]
            c.execute("UPDATE installed_agents SET status='installed', updated_at=?, installed_config=? WHERE id=?",
                      (now, _j(config or {}), iid))
        else:
            iid = new_id("inst")
            ver = c.execute("SELECT id FROM agent_versions WHERE agent_id=? ORDER BY created_at DESC LIMIT 1", (aid,)).fetchone()
            c.execute(
                """INSERT INTO installed_agents (id,user_id,agent_id,agent_version_id,installed_config,status,installed_at,updated_at)
                   VALUES (?,?,?,?,?,'installed',?,?)""",
                (iid, owner, aid, ver["id"] if ver else None,
                 _j(config or {"model_provider": "auto", "logging": True, "human_approval": False}), now, now),
            )
            c.execute("UPDATE agents SET install_count=install_count+1 WHERE id=?", (aid,))
    return get_install(iid, owner)


def get_install(iid, owner):
    with _conn() as c:
        r = c.execute("SELECT * FROM installed_agents WHERE id=? AND user_id=?", (iid, owner)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["installed_config"] = _pj(d.get("installed_config"), {})
    return d


def uninstall(iid, owner):
    with _conn() as c:
        r = c.execute("SELECT agent_id FROM installed_agents WHERE id=? AND user_id=?", (iid, owner)).fetchone()
        if not r:
            return False
        c.execute("DELETE FROM installed_agents WHERE id=?", (iid,))
    return True


def my_agents(owner):
    with _conn() as c:
        installed = c.execute(
            """SELECT ia.id AS install_id, ia.status AS install_status, ia.installed_at, ia.installed_config,
                      a.* FROM installed_agents ia JOIN agents a ON a.id=ia.agent_id
                      WHERE ia.user_id=? ORDER BY ia.installed_at DESC""", (owner,)).fetchall()
        created = c.execute("SELECT * FROM agents WHERE publisher_user_id=? ORDER BY updated_at DESC", (owner,)).fetchall()
    inst = []
    for r in installed:
        a = _agent_out(r)
        a["install_id"] = r["install_id"]
        a["install_status"] = r["install_status"]
        a["installed_at"] = r["installed_at"]
        a["installed_config"] = _pj(r["installed_config"], {})
        inst.append(a)
    return {"installed": inst, "created": [_agent_out(r) for r in created]}


# --- runs / reviews ----------------------------------------------------
def log_run(agent_id, owner, inp, out, status, latency_ms, cost=0.0, logs=None, install_id=None):
    with _conn() as c:
        c.execute(
            """INSERT INTO agent_runs (id,agent_id,installed_agent_id,user_id,input,output,status,logs,cost_estimate,latency_ms,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (new_id("run"), agent_id, install_id, owner, _j(inp), _j(out), status, _j(logs or []), cost, latency_ms, now_iso()),
        )


def admin_submissions():
    with _conn() as c:
        rows = c.execute("SELECT * FROM agents WHERE status IN ('pending','submitted') ORDER BY updated_at DESC").fetchall()
    return [_agent_out(r, full=True) for r in rows]
