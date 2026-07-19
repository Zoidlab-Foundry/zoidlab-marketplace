"""Postgres data layer for the ZoidLab Agent Marketplace with Row-Level Security (§3.2).

The marketplace is a public catalog: agents, versions, and reviews are meant to be
readable by every signed-in user, so those tables carry app-level visibility checks
(status/visibility filters, owner guards on writes) and are NOT RLS-restricted.
Per-user data — installed_agents and agent_runs — is tenant-scoped: FORCE ROW LEVEL
SECURITY with a policy exposing only rows whose user_id matches `app.current_owner`
(set per transaction) or is NULL. Public API mirrors the former sqlite database.py
exactly; JSON columns stay TEXT (json-encoded) via _j/_pj.
"""
import os
import json
import uuid
import datetime

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

# App connections use the RLS-enforced role (app_rls); DDL + cross-tenant admin use the
# superuser (foundry), which bypasses RLS by design.
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://app_rls@127.0.0.1:5433/marketplace")
DATABASE_URL_ADMIN = os.environ.get("DATABASE_URL_ADMIN", "postgresql://foundry@127.0.0.1:5433/marketplace")
_pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=10, open=True, kwargs={"autocommit": False})


def admin_conn():
    return psycopg.connect(DATABASE_URL_ADMIN, row_factory=dict_row)


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def new_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _j(v):
    return json.dumps(v if v is not None else None)


def _pj(v, default=None):
    if v is None:
        return default
    try:
        return json.loads(v)
    except Exception:
        return default


class _tx:
    """Transaction scoped to a tenant: sets app.current_owner so RLS applies."""
    def __init__(self, owner):
        self.owner = owner or ""

    def __enter__(self):
        self.conn = _pool.getconn()
        self.cur = self.conn.cursor(row_factory=dict_row)
        self.cur.execute("SELECT set_config('app.current_owner', %s, true)", (self.owner,))
        return self.cur

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                self.conn.rollback()
            else:
                self.conn.commit()
        finally:
            self.cur.close()
            _pool.putconn(self.conn)


# JSONB-ish agent columns, decoded on the way out.
_AGENT_JSON = ["tags", "manifest", "required_models", "required_tools",
               "required_secrets", "permissions", "input_schema", "output_schema"]

# Tenant tables (per-user rows) and their owner column. agents / agent_versions /
# agent_reviews are public-catalog tables read by everyone and stay un-RLS'd.
_TENANT_TABLES = {"installed_agents": "user_id", "agent_runs": "user_id"}


def init():
    with admin_conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT,
            name TEXT,
            role TEXT DEFAULT 'user',
            org_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS organizations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS agents (
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
            rating_avg DOUBLE PRECISION NOT NULL DEFAULT 0,
            rating_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL)""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_agents_cat ON agents(category)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_agents_owner ON agents(publisher_user_id)")
        c.execute("""CREATE TABLE IF NOT EXISTS agent_versions (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            version TEXT NOT NULL,
            changelog TEXT,
            manifest TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL)""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_versions_agent ON agent_versions(agent_id, created_at)")
        c.execute("""CREATE TABLE IF NOT EXISTS installed_agents (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            org_id TEXT,
            agent_id TEXT NOT NULL,
            agent_version_id TEXT,
            installed_config TEXT,
            status TEXT NOT NULL DEFAULT 'installed',
            installed_at TEXT NOT NULL,
            updated_at TEXT NOT NULL)""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_installed_user ON installed_agents(user_id)")
        c.execute("""CREATE TABLE IF NOT EXISTS agent_reviews (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            rating INTEGER NOT NULL,
            review_text TEXT,
            created_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS agent_runs (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            installed_agent_id TEXT,
            user_id TEXT,
            input TEXT,
            output TEXT,
            status TEXT NOT NULL,
            logs TEXT,
            cost_estimate DOUBLE PRECISION,
            latency_ms INTEGER,
            created_at TEXT NOT NULL)""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_runs_agent ON agent_runs(agent_id, created_at)")
        for t, col in _TENANT_TABLES.items():
            c.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
            c.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
            c.execute(f"DROP POLICY IF EXISTS {t}_isolation ON {t}")
            c.execute(f"""CREATE POLICY {t}_isolation ON {t}
                USING ({col} IS NULL OR {col} = current_setting('app.current_owner', true))
                WITH CHECK ({col} IS NULL OR {col} = current_setting('app.current_owner', true))""")
        c.execute("GRANT USAGE ON SCHEMA public TO app_rls")
        c.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO app_rls")
        c.commit()


# --- users -------------------------------------------------------------
def upsert_user(uid, email=None, name=None):
    if not uid:
        return
    now = now_iso()
    with _tx(uid) as cur:
        cur.execute(
            """INSERT INTO users (id, email, name, role, created_at, updated_at)
               VALUES (%s,%s,%s,'user',%s,%s)
               ON CONFLICT (id) DO UPDATE SET email=COALESCE(EXCLUDED.email, users.email),
                 name=COALESCE(EXCLUDED.name, users.name), updated_at=EXCLUDED.updated_at""",
            (uid, email, name, now, now),
        )


def is_admin(uid):
    if not uid:
        return False
    admins = [a.strip() for a in os.environ.get("MARKETPLACE_ADMINS", "").split(",") if a.strip()]
    if uid in admins:
        return True
    with _tx(uid) as cur:
        cur.execute("SELECT role, email FROM users WHERE id=%s", (uid,))
        r = cur.fetchone()
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
        q += " AND (visibility IN ('public','verified') OR publisher_user_id=%s)"
        args.append(viewer)
    else:
        q += " AND visibility IN ('public','verified')"
    if category and category.lower() != "all":
        q += " AND lower(category)=lower(%s)"; args.append(category)
    if visibility:
        q += " AND visibility=%s"; args.append(visibility)
    if search:
        q += " AND (lower(name) LIKE %s OR lower(short_description) LIKE %s OR lower(tags) LIKE %s)"
        s = f"%{search.lower()}%"; args += [s, s, s]
    if tag:
        q += " AND lower(tags) LIKE %s"; args.append(f'%"{tag.lower()}"%')
    order = {"newest": "created_at DESC", "installs": "install_count DESC",
             "rating": "rating_avg DESC, rating_count DESC", "name": "name ASC"}.get(sort, "install_count DESC")
    q += f" ORDER BY {order}"
    with _tx(viewer) as cur:
        cur.execute(q, args)
        rows = cur.fetchall()
    out = [_agent_out(r) for r in rows]
    if tag:  # exact tag membership (LIKE was a coarse prefilter)
        out = [a for a in out if tag.lower() in [t.lower() for t in a.get("tags", [])]]
    return out


def get_agent(slug, viewer=None):
    with _tx(viewer) as cur:
        cur.execute("SELECT * FROM agents WHERE slug=%s", (slug,))
        r = cur.fetchone()
    a = _agent_out(r, full=True)
    if not a:
        return None
    if a["visibility"] not in VISIBLE_PUBLIC and a["publisher_user_id"] != viewer and not is_admin(viewer):
        return None
    return a


def get_agent_by_id(aid):
    with _tx(None) as cur:
        cur.execute("SELECT * FROM agents WHERE id=%s", (aid,))
        r = cur.fetchone()
    return _agent_out(r, full=True)


def categories():
    with _tx(None) as cur:
        cur.execute(
            """SELECT category, COUNT(*) n FROM agents
               WHERE status IN ('published','approved') AND visibility IN ('public','verified')
               GROUP BY category ORDER BY n DESC""")
        rows = cur.fetchall()
    return [{"name": r["category"], "count": int(r["n"])} for r in rows if r["category"]]


def create_agent(data, owner):
    aid = data.get("id") or new_id("agent")
    now = now_iso()
    with _tx(owner) as cur:
        cur.execute(
            """INSERT INTO agents (id,name,slug,short_description,long_description,category,tags,icon,accent,
                 publisher_name,publisher_user_id,publisher_org_id,visibility,status,version,manifest,
                 required_models,required_tools,required_secrets,permissions,input_schema,output_schema,risk,
                 featured,install_count,rating_avg,rating_count,created_at,updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (aid, data["name"], data["slug"], data.get("short_description"), data.get("long_description"),
             data.get("category"), _j(data.get("tags", [])), data.get("icon", "◆"), data.get("accent", "#7c5cfc"),
             data.get("publisher_name", "Community"), owner, data.get("publisher_org_id"),
             data.get("visibility", "private"), data.get("status", "draft"), data.get("version", "0.1.0"),
             _j(data.get("manifest", {})), _j(data.get("required_models", [])), _j(data.get("required_tools", [])),
             _j(data.get("required_secrets", [])), _j(data.get("permissions", [])),
             _j(data.get("input_schema", {})), _j(data.get("output_schema", {})), data.get("risk", "low"),
             1 if data.get("featured") else 0, 0, 0, 0, now, now),
        )
        cur.execute("INSERT INTO agent_versions (id,agent_id,version,changelog,manifest,created_by,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (new_id("ver"), aid, data.get("version", "0.1.0"), "Initial version", _j(data.get("manifest", {})), owner, now))
    return get_agent_by_id(aid)


def update_agent(aid, data, owner):
    with _tx(owner) as cur:
        cur.execute("SELECT publisher_user_id, status FROM agents WHERE id=%s", (aid,))
        r = cur.fetchone()
        if not r or (r["publisher_user_id"] != owner and not is_admin(owner)):
            return None
        fields, args = [], []
        for col in ("name", "short_description", "long_description", "category", "visibility", "version", "icon", "accent", "risk"):
            if col in data:
                fields.append(f"{col}=%s"); args.append(data[col])
        for col in ("tags", "manifest", "required_models", "required_tools", "required_secrets", "permissions", "input_schema", "output_schema"):
            if col in data:
                fields.append(f"{col}=%s"); args.append(_j(data[col]))
        fields.append("updated_at=%s"); args.append(now_iso())
        args.append(aid)
        cur.execute(f"UPDATE agents SET {', '.join(fields)} WHERE id=%s", args)
    return get_agent_by_id(aid)


def set_status(aid, status, owner=None, require_owner=False):
    with _tx(owner) as cur:
        cur.execute("SELECT publisher_user_id FROM agents WHERE id=%s", (aid,))
        r = cur.fetchone()
        if not r:
            return None
        if require_owner and r["publisher_user_id"] != owner and not is_admin(owner):
            return None
        cur.execute("UPDATE agents SET status=%s, updated_at=%s WHERE id=%s", (status, now_iso(), aid))
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
    with _tx(None) as cur:
        cur.execute("SELECT id,version,changelog,created_at FROM agent_versions WHERE agent_id=%s ORDER BY created_at DESC", (aid,))
        rows = cur.fetchall()
    return [dict(r) for r in rows]


# --- installs ----------------------------------------------------------
def install_agent(aid, owner, config=None):
    a = get_agent_by_id(aid)
    if not a:
        return None
    now = now_iso()
    with _tx(owner) as cur:
        cur.execute("SELECT id FROM installed_agents WHERE user_id=%s AND agent_id=%s", (owner, aid))
        existing = cur.fetchone()
        if existing:
            iid = existing["id"]
            cur.execute("UPDATE installed_agents SET status='installed', updated_at=%s, installed_config=%s WHERE id=%s",
                        (now, _j(config or {}), iid))
        else:
            iid = new_id("inst")
            cur.execute("SELECT id FROM agent_versions WHERE agent_id=%s ORDER BY created_at DESC LIMIT 1", (aid,))
            ver = cur.fetchone()
            cur.execute(
                """INSERT INTO installed_agents (id,user_id,agent_id,agent_version_id,installed_config,status,installed_at,updated_at)
                   VALUES (%s,%s,%s,%s,%s,'installed',%s,%s)""",
                (iid, owner, aid, ver["id"] if ver else None,
                 _j(config or {"model_provider": "auto", "logging": True, "human_approval": False}), now, now),
            )
            cur.execute("UPDATE agents SET install_count=install_count+1 WHERE id=%s", (aid,))
    return get_install(iid, owner)


def get_install(iid, owner):
    with _tx(owner) as cur:
        cur.execute("SELECT * FROM installed_agents WHERE id=%s AND user_id=%s", (iid, owner))
        r = cur.fetchone()
    if not r:
        return None
    d = dict(r)
    d["installed_config"] = _pj(d.get("installed_config"), {})
    return d


def uninstall(iid, owner):
    with _tx(owner) as cur:
        cur.execute("SELECT agent_id FROM installed_agents WHERE id=%s AND user_id=%s", (iid, owner))
        r = cur.fetchone()
        if not r:
            return False
        cur.execute("DELETE FROM installed_agents WHERE id=%s", (iid,))
    return True


# --- reviews / ratings (real) -----------------------------------------
def is_installed(aid, user_id):
    if not user_id:
        return False
    with _tx(user_id) as cur:
        cur.execute("SELECT 1 FROM installed_agents WHERE user_id=%s AND agent_id=%s AND status='installed'",
                    (user_id, aid))
        return bool(cur.fetchone())


def recompute_rating(aid):
    """Set an agent's rating_avg/rating_count from its REAL reviews (0 when none).
    Engine-internal write with no owner in scope; PG aggregates come back as Decimal."""
    with admin_conn() as c:
        row = c.execute("SELECT COUNT(*) n, AVG(rating) a FROM agent_reviews WHERE agent_id=%s", (aid,)).fetchone()
        cnt = int(row["n"] or 0)
        avg = round(float(row["a"]), 2) if row["a"] is not None else 0.0
        c.execute("UPDATE agents SET rating_count=%s, rating_avg=%s, updated_at=%s WHERE id=%s", (cnt, avg, now_iso(), aid))
        c.commit()
    return {"rating_avg": avg, "rating_count": cnt}


def normalize_ratings():
    """Recompute every agent's rating from real reviews — zeroes any seeded placeholders."""
    with admin_conn() as c:
        ids = [r["id"] for r in c.execute("SELECT id FROM agents").fetchall()]
    for aid in ids:
        recompute_rating(aid)
    return len(ids)


def add_review(aid, user_id, rating, text=None):
    rating = max(1, min(5, int(rating)))
    now = now_iso()
    with _tx(user_id) as cur:
        cur.execute("SELECT id FROM agent_reviews WHERE agent_id=%s AND user_id=%s", (aid, user_id))
        existing = cur.fetchone()
        if existing:
            cur.execute("UPDATE agent_reviews SET rating=%s, review_text=%s, created_at=%s WHERE id=%s",
                        (rating, (text or "").strip() or None, now, existing["id"]))
        else:
            cur.execute("INSERT INTO agent_reviews (id,agent_id,user_id,rating,review_text,created_at) VALUES (%s,%s,%s,%s,%s,%s)",
                        (new_id("rev"), aid, user_id, rating, (text or "").strip() or None, now))
    return recompute_rating(aid)


def list_reviews(aid, limit=50):
    # Reviews are public, and the verified_install badge needs to see OTHER users'
    # installed_agents rows (RLS'd) — so this cross-tenant read goes through admin.
    # It exposes only a boolean per review, exactly as the sqlite version did.
    with admin_conn() as c:
        rows = c.execute(
            """SELECT r.rating, r.review_text, r.created_at, r.user_id, u.name AS user_name, u.email AS user_email,
                      (SELECT 1 FROM installed_agents i WHERE i.user_id=r.user_id AND i.agent_id=r.agent_id LIMIT 1) AS installed
               FROM agent_reviews r LEFT JOIN users u ON u.id=r.user_id
               WHERE r.agent_id=%s ORDER BY r.created_at DESC LIMIT %s""", (aid, limit)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["verified_install"] = bool(d.pop("installed", None))
        d["reviewer"] = d.get("user_name") or (str(d.get("user_email") or "user").split("@")[0])
        d.pop("user_email", None)
        d.pop("user_name", None)
        d.pop("user_id", None)
        out.append(d)
    return out


def my_review(aid, user_id):
    if not user_id:
        return None
    with _tx(user_id) as cur:
        cur.execute("SELECT rating, review_text FROM agent_reviews WHERE agent_id=%s AND user_id=%s", (aid, user_id))
        r = cur.fetchone()
    return dict(r) if r else None


def my_agents(owner):
    with _tx(owner) as cur:
        cur.execute(
            """SELECT ia.id AS install_id, ia.status AS install_status, ia.installed_at, ia.installed_config,
                      a.* FROM installed_agents ia JOIN agents a ON a.id=ia.agent_id
                      WHERE ia.user_id=%s ORDER BY ia.installed_at DESC""", (owner,))
        installed = cur.fetchall()
        cur.execute("SELECT * FROM agents WHERE publisher_user_id=%s ORDER BY updated_at DESC", (owner,))
        created = cur.fetchall()
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
    with _tx(owner) as cur:
        cur.execute(
            """INSERT INTO agent_runs (id,agent_id,installed_agent_id,user_id,input,output,status,logs,cost_estimate,latency_ms,created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (new_id("run"), agent_id, install_id, owner, _j(inp), _j(out), status, _j(logs or []), cost, latency_ms, now_iso()),
        )


def admin_submissions():
    # Admin moderation queue: sees every pending agent regardless of visibility.
    with admin_conn() as c:
        rows = c.execute("SELECT * FROM agents WHERE status IN ('pending','submitted') ORDER BY updated_at DESC").fetchall()
    return [_agent_out(r, full=True) for r in rows]
