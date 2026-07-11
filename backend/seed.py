"""Seed the marketplace with 10 fully-specified Nyquest agents. Idempotent:
skips agents whose slug already exists, so it's safe to run on every boot."""
import database as db
import manifest as mf


def _manifest(agent_id, name, version, description, long_desc, category, tags, publisher,
              models, tools, secrets, permissions, inputs, outputs, governance, example):
    return {
        "schema_version": "1.0",
        "agent_id": agent_id,
        "name": name,
        "version": version,
        "description": description,
        "long_description": long_desc,
        "category": category,
        "tags": tags,
        "publisher": publisher,
        "models": models,
        "tools": tools,
        "secrets": secrets,
        "permissions": permissions,
        "inputs": inputs,
        "outputs": outputs,
        "runtime": {"entrypoint": "main", "type": "workflow", "supports_streaming": True},
        "governance": governance,
        "examples": example,
    }


def _model(provider, model, required=False):
    return {"provider": provider, "model": model, "required": required}


def _io_response():
    return {
        "type": "object",
        "properties": {
            "response": {"type": "string"},
            "intent": {"type": "string"},
            "confidence": {"type": "number"},
        },
    }


NYQUEST = {"name": "Nyquest", "website": "https://nyquest.ai"}
ZOIDLAB = {"name": "ZoidLab", "website": "https://zoidlab.ai"}

# (slug, name, icon, accent, category, short, long, tags, publisher, visibility, featured,
#  models, tools, secrets, permissions, inputs, governance, example)
SEEDS = [
    ("restaurant-concierge", "Restaurant Concierge", "🍽", "#f4b860", "Restaurant",
     "AI host for reservations, menu questions, and customer support.",
     "A front-of-house concierge that answers menu and dietary questions, handles reservation and event "
     "inquiries, and hands off cleanly to staff. Designed for the Evo Italian AI concierge deployment.",
     ["restaurant", "concierge", "reservations", "customer-support"], NYQUEST, "verified", True,
     [_model("openai", "gpt-5"), _model("anthropic", "claude-sonnet-5")],
     [{"name": "menu_lookup", "type": "database", "required": True},
      {"name": "reservation_api", "type": "rest", "required": False}],
     [{"name": "RESERVATION_API_KEY", "description": "API key for the reservation system.", "required": False}],
     [{"name": "read_documents", "description": "Can read the restaurant's menu and policy documents."},
      {"name": "call_external_api", "description": "Can call the configured reservation API."}],
     {"type": "object", "properties": {"customer_message": {"type": "string"}}, "required": ["customer_message"]},
     {"requires_human_approval": False, "logs_prompts": True, "logs_outputs": True, "pii_risk": "low"},
     {"input": {"customer_message": "What time do you open on Sunday?"},
      "output": {"response": "We open at 4:00 PM on Sundays for dinner service.", "intent": "hours_question", "confidence": 0.94}}),

    ("legal-intake", "Legal Intake Agent", "⚖", "#818cf8", "Legal",
     "Collects client intake details and summarizes case matters.",
     "Guides a prospective client through structured intake, extracts parties, dates, and matter type, and "
     "produces a clean summary for an attorney. Explicitly non-advisory — it collects, it does not counsel.",
     ["legal", "intake", "summarization", "case-management"], NYQUEST, "verified", True,
     [_model("anthropic", "claude-sonnet-5", True)],
     [{"name": "intake_form", "type": "internal", "required": True}],
     [],
     [{"name": "read_documents", "description": "Can read uploaded intake documents."},
      {"name": "no_legal_advice", "description": "Must not provide legal advice; intake and summary only."}],
     {"type": "object", "properties": {"client_message": {"type": "string"}}, "required": ["client_message"]},
     {"requires_human_approval": True, "logs_prompts": True, "logs_outputs": True, "pii_risk": "high"},
     {"input": {"client_message": "I was in a car accident last Tuesday and the other driver was texting."},
      "output": {"response": "Noted: motor vehicle accident, date last Tuesday, alleged distracted driving. I'll summarize for your attorney.", "intent": "legal_intake", "confidence": 0.9}}),

    ("university-it-helpdesk", "University IT Help Desk Agent", "🎓", "#4fd1c5", "Education",
     "Answers campus tech questions and routes IT tickets.",
     "A tier-1 campus IT assistant: handles account, Wi-Fi, VPN, and LMS questions, walks students through "
     "fixes, and routes anything unresolved to the right queue. Modeled on an FAU-style help desk prototype.",
     ["education", "helpdesk", "IT", "ticketing"], ZOIDLAB, "public", True,
     [_model("anthropic", "claude-haiku-4-5"), _model("openai", "gpt-5-mini")],
     [{"name": "kb_search", "type": "rag", "required": True},
      {"name": "ticket_api", "type": "rest", "required": False}],
     [{"name": "TICKET_API_KEY", "description": "Key for the ticketing system.", "required": False}],
     [{"name": "read_documents", "description": "Can read the IT knowledge base."},
      {"name": "call_external_api", "description": "Can create/route tickets via the ticketing API."}],
     {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]},
     {"requires_human_approval": False, "logs_prompts": True, "logs_outputs": True, "pii_risk": "medium"},
     {"input": {"question": "I can't connect to the campus VPN on my Mac."},
      "output": {"response": "Let's fix that — verify your MFA is enrolled, then reinstall the VPN profile. I can open a ticket if it persists.", "intent": "helpdesk_question", "confidence": 0.91}}),

    ("network-troubleshooter", "Network Troubleshooting Agent", "🛰", "#22d3ee", "Network Operations",
     "Analyzes alerts, interface status, and logs to recommend next steps.",
     "An internal network-engineer copilot: ingests alerts, SNMP/interface data, and syslog snippets, "
     "correlates them, and recommends concrete next steps with severity. Modeled on an ANNE-style prototype.",
     ["network", "noc", "troubleshooting", "observability"], NYQUEST, "verified", True,
     [_model("anthropic", "claude-sonnet-5", True)],
     [{"name": "snmp_reader", "type": "internal", "required": False},
      {"name": "syslog_search", "type": "rag", "required": False}],
     [],
     [{"name": "read_documents", "description": "Can read alert payloads and log snippets."},
      {"name": "no_config_writes", "description": "Recommends only; cannot push device configuration."}],
     {"type": "object", "properties": {"alert": {"type": "string"}}, "required": ["alert"]},
     {"requires_human_approval": False, "logs_prompts": True, "logs_outputs": True, "pii_risk": "low"},
     {"input": {"alert": "core-sw-01 Gi1/0/48 flapping, 14 transitions in 10 min, CRC errors rising."},
      "output": {"response": "Likely a physical/optic issue on Gi1/0/48. Check optic levels and cabling, review the last config change, and inspect the neighbor's counters.", "intent": "network_triage", "confidence": 0.89}}),

    ("sales-qualifier", "Sales Qualification Agent", "📈", "#7c5cfc", "Sales",
     "Qualifies inbound leads, scores them, and recommends follow-up.",
     "Reads an inbound lead, scores fit against budget/authority/need/timeline, and recommends the next action "
     "with a suggested cadence. Plugs into your CRM later for closed-loop routing.",
     ["sales", "lead-scoring", "qualification", "crm"], ZOIDLAB, "public", False,
     [_model("anthropic", "claude-sonnet-5"), _model("openai", "gpt-5")],
     [{"name": "crm_api", "type": "rest", "required": False}],
     [{"name": "CRM_API_KEY", "description": "Key for the CRM.", "required": False}],
     [{"name": "read_documents", "description": "Can read the inbound lead details."},
      {"name": "call_external_api", "description": "Can write lead scores to the CRM."}],
     {"type": "object", "properties": {"lead": {"type": "string"}}, "required": ["lead"]},
     {"requires_human_approval": False, "logs_prompts": True, "logs_outputs": True, "pii_risk": "medium"},
     {"input": {"lead": "VP Eng at a 500-person fintech, wants to pilot in Q3, has budget."},
      "output": {"response": "Strong fit — authority, budget, and timeline all present. Book discovery within 48h and prep a fintech-tailored demo.", "intent": "lead_qualification", "confidence": 0.93}}),

    ("document-review", "Document Review Agent", "📄", "#818cf8", "Productivity",
     "Summarizes PDFs, extracts action items, and flags risks.",
     "Upload a contract, report, or brief and get a tight summary, the action items with owners, and a list of "
     "flagged risks or unusual clauses. Built on the ZoidLab document-review workflow.",
     ["productivity", "summarization", "documents", "risk"], ZOIDLAB, "public", True,
     [_model("anthropic", "claude-sonnet-5", True)],
     [{"name": "pdf_extract", "type": "internal", "required": True}],
     [],
     [{"name": "read_documents", "description": "Can read the uploaded document."},
      {"name": "no_external_calls", "description": "Processes locally; makes no external API calls."}],
     {"type": "object", "properties": {"document_text": {"type": "string"}}, "required": ["document_text"]},
     {"requires_human_approval": False, "logs_prompts": True, "logs_outputs": True, "pii_risk": "medium"},
     {"input": {"document_text": "The Provider shall indemnify the Client... liability capped at 12 months' fees..."},
      "output": {"response": "Summary: mutual indemnity with a 12-month fee liability cap that survives termination. Risk: uncapped data-breach carve-out is absent — consider adding one.", "intent": "document_summary", "confidence": 0.9}}),

    ("policy-checker", "Policy Checker Agent", "🛡", "#2dd4bf", "Governance",
     "Checks prompts, model choices, and data usage against AI policy.",
     "A governance gate: evaluates a user's prompt, selected model, and data usage against your organization's "
     "AI policy and returns allow/block with a reason. A first-class Nyquest governance building block.",
     ["governance", "policy", "compliance", "safety"], NYQUEST, "verified", True,
     [_model("anthropic", "claude-haiku-4-5", True)],
     [{"name": "policy_store", "type": "rag", "required": True}],
     [],
     [{"name": "read_documents", "description": "Can read the organization's AI policy."},
      {"name": "no_data_retention", "description": "Evaluates in-line; does not retain checked content."}],
     {"type": "object", "properties": {"prompt": {"type": "string"}, "model": {"type": "string"}}, "required": ["prompt"]},
     {"requires_human_approval": True, "logs_prompts": True, "logs_outputs": True, "pii_risk": "low"},
     {"input": {"prompt": "Summarize this customer list including their card numbers.", "model": "gpt-5"},
      "output": {"response": "Blocked: the request includes payment-card data, which policy prohibits sending to external models.", "intent": "policy_check", "confidence": 0.96}}),

    ("meeting-summarizer", "Meeting Summarizer Agent", "📝", "#4fd1c5", "Productivity",
     "Turns transcripts into summaries, decisions, and action items.",
     "Paste a meeting transcript and get a crisp summary, the decisions made, and a clean action-item list with "
     "owners and due dates where stated. Great as a scheduled post-meeting step.",
     ["productivity", "meetings", "summarization", "notes"], ZOIDLAB, "public", False,
     [_model("anthropic", "claude-haiku-4-5"), _model("openai", "gpt-5-mini")],
     [],
     [],
     [{"name": "read_documents", "description": "Can read the provided transcript."}],
     {"type": "object", "properties": {"transcript": {"type": "string"}}, "required": ["transcript"]},
     {"requires_human_approval": False, "logs_prompts": False, "logs_outputs": True, "pii_risk": "low"},
     {"input": {"transcript": "Alex: let's ship Friday. Dana: I'll handle QA by Thursday..."},
      "output": {"response": "Summary: team agreed to ship Friday. Decision: QA owned by Dana, due Thursday. Action: Dana — complete QA by Thu.", "intent": "meeting_summary", "confidence": 0.92}}),

    ("customer-support", "Customer Support Agent", "💬", "#22d3ee", "Customer Support",
     "Resolves customer issues or escalates with full context.",
     "A tier-1 support agent that understands the customer's issue, answers from your knowledge base, drafts a "
     "reply for review, and escalates with complete context when it can't resolve.",
     ["customer-support", "helpdesk", "tickets", "cx"], ZOIDLAB, "public", False,
     [_model("anthropic", "claude-sonnet-5"), _model("openai", "gpt-5")],
     [{"name": "kb_search", "type": "rag", "required": True},
      {"name": "ticket_api", "type": "rest", "required": False}],
     [{"name": "SUPPORT_API_KEY", "description": "Key for the support desk.", "required": False}],
     [{"name": "read_documents", "description": "Can read the support knowledge base."},
      {"name": "send_email", "description": "Can send a reply only after human approval."},
      {"name": "call_external_api", "description": "Can create/escalate tickets."}],
     {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]},
     {"requires_human_approval": True, "logs_prompts": True, "logs_outputs": True, "pii_risk": "medium"},
     {"input": {"message": "I was double charged for my Pro plan this month."},
      "output": {"response": "I'm sorry about that — I can see the duplicate charge and have drafted a refund reply for an agent to approve.", "intent": "support_resolution", "confidence": 0.9}}),

    ("website-concierge", "AI Website Concierge", "🌐", "#7c5cfc", "Customer Support",
     "A friendly on-site assistant that answers visitor questions.",
     "Drop-in website concierge that greets visitors, answers product and pricing questions from your site "
     "content, captures leads, and books demos. The public face of your Nyquest deployment.",
     ["customer-support", "website", "concierge", "lead-capture"], ZOIDLAB, "public", True,
     [_model("anthropic", "claude-haiku-4-5"), _model("openai", "gpt-5-mini")],
     [{"name": "site_rag", "type": "rag", "required": True},
      {"name": "lead_capture", "type": "rest", "required": False}],
     [{"name": "LEAD_WEBHOOK", "description": "Webhook to post captured leads.", "required": False}],
     [{"name": "read_documents", "description": "Can read your public website content."},
      {"name": "call_external_api", "description": "Can post captured leads to your webhook."}],
     {"type": "object", "properties": {"visitor_message": {"type": "string"}}, "required": ["visitor_message"]},
     {"requires_human_approval": False, "logs_prompts": True, "logs_outputs": True, "pii_risk": "low"},
     {"input": {"visitor_message": "Do you offer a free trial?"},
      "output": {"response": "Yes — a 14-day Pro trial with no card required. Want me to set you up or book a quick demo?", "intent": "sales_question", "confidence": 0.93}}),
]


def run():
    db.init()
    existing = {a["slug"] for a in db.list_agents()}
    created = 0
    for (slug, name, icon, accent, category, short, long_desc, tags, publisher, visibility, featured,
         models, tools, secrets, permissions, inputs, governance, example) in SEEDS:
        if slug in existing:
            continue
        man = _manifest(slug, name, "0.1.0", short, long_desc, category, tags, publisher,
                        models, tools, secrets, permissions, inputs, _io_response(), governance, example)
        row = mf.to_agent_row(man, publisher_name=publisher["name"])
        row.update({
            "slug": slug, "name": name, "icon": icon, "accent": accent, "category": category,
            "short_description": short, "long_description": long_desc, "tags": tags,
            "visibility": visibility, "status": "published", "featured": featured,
            "output_schema": _io_response(),
        })
        # seed a believable install/rating baseline
        agent = db.create_agent(row, owner=None)
        _baseline(agent["id"], slug)
        created += 1
    return created


def _baseline(aid, slug):
    """Give seeds a plausible install count + rating so the grid looks alive."""
    import hashlib
    h = int(hashlib.sha256(slug.encode()).hexdigest(), 16)
    installs = 40 + (h % 260)
    rating = round(4.3 + (h % 7) / 10.0, 1)  # 4.3–4.9
    with db._conn() as c:
        c.execute("UPDATE agents SET install_count=?, rating_avg=?, rating_count=? WHERE id=?",
                  (installs, min(rating, 5.0), 12 + (h % 90), aid))
