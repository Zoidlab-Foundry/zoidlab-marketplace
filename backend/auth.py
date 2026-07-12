"""Shared ZoidLab session — decode the `zb_session` cookie minted by the SSO
handoff (jose HS256, BUILDER_SESSION_SECRET). Same cookie the builder/foundry use,
so signing in once anywhere in *.zoidlab.ai authenticates here too."""
import os
import sys
import jwt
from fastapi import Request

_DEFAULT = "dev-secret-change-me"
SECRET = os.environ.get("BUILDER_SESSION_SECRET", _DEFAULT)
PRO_TIERS = {"pro", "teams", "team", "enterprise"}

if SECRET == _DEFAULT:
    print("[marketplace] WARNING: BUILDER_SESSION_SECRET is unset — using an insecure "
          "default. Session cookies are forgeable. Set a real secret before exposing this API.",
          file=sys.stderr)


def session(request: Request):
    """Return the decoded claims dict, or None if unauthenticated/invalid."""
    tok = request.cookies.get("zb_session")
    if not tok:
        return None
    try:
        return jwt.decode(tok, SECRET, algorithms=["HS256"])
    except Exception:
        return None


def owner_of(request: Request):
    """Nyquest user id (sub claim) or None. This is the ownership key."""
    s = session(request)
    return s.get("sub") if s else None


def is_pro(request: Request):
    s = session(request)
    return bool(s) and str(s.get("tier") or "").lower() in PRO_TIERS
