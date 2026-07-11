"""Nyquest Agent Manifest (schema_version 1.0) — validation + coercion.

The manifest is the portable package format for a marketplace agent. This module
validates it and maps it onto the flat agent row the DB stores.
"""

SCHEMA_VERSION = "1.0"

REQUIRED_TOP = ["schema_version", "name", "version", "category"]


def _is_jsonschema(obj):
    return isinstance(obj, dict) and (obj.get("type") == "object" or "properties" in obj or obj == {})


def validate(manifest: dict) -> dict:
    """Return {ok, errors:[...], warnings:[...]}. Clear, human-readable messages."""
    errors, warnings = [], []
    if not isinstance(manifest, dict):
        return {"ok": False, "errors": ["Manifest must be a JSON object."], "warnings": []}

    for k in REQUIRED_TOP:
        if not manifest.get(k):
            errors.append(f"Missing required field: '{k}'.")

    sv = str(manifest.get("schema_version", ""))
    if sv and sv != SCHEMA_VERSION:
        warnings.append(f"schema_version is '{sv}'; this marketplace targets '{SCHEMA_VERSION}'.")

    inputs = manifest.get("inputs")
    if inputs is not None and not _is_jsonschema(inputs):
        errors.append("'inputs' must be a JSON Schema object (type: object with properties).")
    outputs = manifest.get("outputs")
    if outputs is not None and not _is_jsonschema(outputs):
        errors.append("'outputs' must be a JSON Schema object (type: object with properties).")

    for arr in ("tools", "secrets", "permissions", "models"):
        v = manifest.get(arr)
        if v is not None and not isinstance(v, list):
            errors.append(f"'{arr}' must be an array.")

    if "permissions" not in manifest:
        warnings.append("No 'permissions' declared — declare what the agent can access (trust matters).")
    if "governance" not in manifest:
        warnings.append("No 'governance' block — add pii_risk / requires_human_approval / logging flags.")
    else:
        gov = manifest.get("governance") or {}
        if not isinstance(gov, dict):
            errors.append("'governance' must be an object.")
        elif gov.get("pii_risk") not in (None, "none", "low", "medium", "high"):
            warnings.append("governance.pii_risk should be one of: none, low, medium, high.")

    return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings}


def risk_from_manifest(manifest: dict) -> str:
    gov = manifest.get("governance") or {}
    pii = str(gov.get("pii_risk", "")).lower()
    if pii == "high":
        return "high"
    perms = manifest.get("permissions") or []
    names = " ".join(str((p or {}).get("name", "")) for p in perms).lower()
    if pii == "medium" or "external" in names or "call_external_api" in names or (manifest.get("secrets")):
        return "medium"
    return "low"


def to_agent_row(manifest: dict, publisher_name=None) -> dict:
    """Flatten a validated manifest into the fields create_agent expects."""
    pub = manifest.get("publisher") or {}
    return {
        "name": manifest.get("name"),
        "short_description": (manifest.get("description") or "")[:200],
        "long_description": manifest.get("long_description") or manifest.get("description") or "",
        "category": manifest.get("category"),
        "tags": manifest.get("tags") or [],
        "version": manifest.get("version") or "0.1.0",
        "publisher_name": publisher_name or pub.get("name") or "Community",
        "manifest": manifest,
        "required_models": manifest.get("models") or [],
        "required_tools": manifest.get("tools") or [],
        "required_secrets": manifest.get("secrets") or [],
        "permissions": manifest.get("permissions") or [],
        "input_schema": manifest.get("inputs") or {},
        "output_schema": manifest.get("outputs") or {},
        "risk": risk_from_manifest(manifest),
    }


# governance badges surfaced on the agent card / detail page
def badges(agent: dict) -> list:
    out = []
    risk = (agent.get("risk") or "low").lower()
    out.append({"low": "Low Risk", "medium": "Medium Risk", "high": "High Risk"}.get(risk, "Low Risk"))
    man = agent.get("manifest") or {}
    gov = man.get("governance") or {}
    if agent.get("required_secrets"):
        out.append("Requires Secrets")
    perms = " ".join(str((p or {}).get("name", "")) for p in (agent.get("permissions") or [])).lower()
    if "external" in perms:
        out.append("External API Access")
    if gov.get("requires_human_approval"):
        out.append("Human Approval Recommended")
    if gov.get("logs_prompts"):
        out.append("Logs Prompts")
    if gov.get("logs_outputs"):
        out.append("Logs Outputs")
    if str(gov.get("pii_risk", "")).lower() in ("medium", "high"):
        out.append("PII Risk")
    return out
