"""Sandbox runner. Deterministic, category-aware mock responses for the MVP
(no funds / auth required), with a clean seam to swap in real Nyquest model
routing later (set ENABLE_MOCK_SANDBOX=false + provide a relay key)."""
import os
import time
import hashlib

MOCK = os.environ.get("ENABLE_MOCK_SANDBOX", "true").lower() != "false"

# category → (canned response, intent). Keeps sandbox believable without a model.
_BY_CATEGORY = {
    "Restaurant": ("I can help with hours, reservations, the menu, dietary questions, and private events. "
                   "Connect your restaurant's knowledge base to make these answers live and specific.", "restaurant_question"),
    "Legal": ("Thanks — I've noted the key intake details (parties, dates, matter type). I'll summarize the case and "
              "flag missing items. Note: this is intake only and not legal advice.", "legal_intake"),
    "Medical": ("I've captured the reported symptoms and history. I can triage urgency and prepare a structured summary "
                "for a clinician. This is not a diagnosis.", "medical_triage"),
    "Education": ("I can answer campus tech questions, reset-account guidance, and route tickets to the right queue. "
                  "Point me at your IT knowledge base to go live.", "helpdesk_question"),
    "University": ("Routing this to the correct campus service desk and drafting a first-response with next steps.", "campus_support"),
    "Network Operations": ("The alert suggests an interface or uplink issue. Check recent flaps, optics levels, CRC/error counters, "
                           "and neighboring device logs; correlate with the last config change.", "network_triage"),
    "Finance": ("I've parsed the figures and can produce a variance summary with the top drivers and a recommended action.", "finance_analysis"),
    "Sales": ("Lead scored. Fit looks strong on budget and timeline; recommend a discovery call within 48h and a tailored demo.", "lead_qualification"),
    "Customer Support": ("I understand the issue and can resolve it or escalate with full context. Draft reply prepared for review.", "support_resolution"),
    "Marketing": ("Here are three on-brand angles with headlines and a suggested channel mix for the campaign.", "marketing_ideation"),
    "HR": ("I've structured the request and can answer from policy or route to HR with the relevant context.", "hr_question"),
    "Security": ("Reviewed the indicators. Severity looks moderate; recommend isolating the host, rotating the exposed key, "
                 "and checking auth logs for lateral movement.", "security_triage"),
    "Developer Tools": ("Analyzed the snippet. Here's the likely root cause, a minimal fix, and a test to prevent regression.", "dev_assist"),
    "Research": ("I gathered and synthesized the key findings with sources, and flagged where the evidence is thin.", "research_synthesis"),
    "Productivity": ("Summary ready: the main points, the decisions, and a clean list of action items with owners.", "document_summary"),
    "Governance": ("Policy check complete. The request is within policy; logging is enabled and no restricted data was accessed.", "policy_check"),
}
_DEFAULT = ("I've processed your input and produced a structured response. Connect this agent's tools and knowledge base "
            "to make it fully live.", "general_response")


def _confidence(seed: str) -> float:
    h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    return round(0.82 + (h % 16) / 100.0, 2)  # 0.82–0.97, stable per input


def run(agent: dict, user_input: str) -> dict:
    """Returns {output, latency_ms, cost_estimate, logs}."""
    t0 = time.time()
    category = agent.get("category") or ""
    base, intent = _BY_CATEGORY.get(category, _DEFAULT)
    msg = (user_input or "").strip()
    # light echo so the response feels addressed to the input
    lead = f'For "{msg[:120]}" — ' if msg else ""
    response = lead + base
    logs = [
        {"step": "route", "detail": f"matched category '{category or 'general'}'"},
        {"step": "model", "detail": "mock:deterministic" if MOCK else "nyquest:auto"},
    ]
    out = {"response": response, "intent": intent, "confidence": _confidence(msg or category)}
    return {
        "output": out,
        "latency_ms": int((time.time() - t0) * 1000) + 180,  # believable floor
        "cost_estimate": 0.0 if MOCK else 0.002,
        "logs": logs,
    }
