"""Marketplace assistant manifest — what the in-app assistant knows and may do.

The security boundary: only these capabilities exist for the assistant, and they run through
this app's own session-authed API. Uninstall/deletes, submit-for-review (a multi-step human
flow) and admin review actions are deliberately NOT exposed.
"""
from foundry_common.assistant import cap, page

MANIFEST = {
    "app": "Marketplace",
    "description": (
        "The Marketplace is the Foundry's agent app store. Browse a public catalog of agents "
        "by category, open a listing to see what an agent does, which models it uses, what "
        "permissions and secrets it declares and its governance badges, try it in the sandbox "
        "tester, and install the ones you want. Listings are public to every signed-in user; "
        "installs and test runs belong to the individual user."
    ),
    "base_url": "http://127.0.0.1:8300",
    "pages": [
        page("/", "Marketplace", "Featured and recently added agents, plus category filters.",
             assists={"search-agents": "the catalog search box"}),
        page("/agents", "Browse", "The full catalog with search, category and sort."),
        page("/agents/[slug]", "Listing", "One agent: description, models, permissions, reviews, sandbox tester.",
             assists={"install-agent": "the Install agent button"}),
        page("/my-agents", "My Agents", "Agents this user has installed."),
        page("/submit", "Submit", "Publish your own agent for review (human, multi-step form)."),
    ],
    "capabilities": [
        cap("list_agents", "GET", "/api/agents", risk="read",
            desc="Search/browse the public agent catalog.",
            params={"q": "search text", "category": "category filter", "sort": "sort order"}),
        cap("get_agent", "GET", "/api/agents/{slug}", risk="read",
            desc="One listing: what it does, models, tools, permissions, secrets, governance.",
            params={"slug": "agent slug"}),
        cap("list_categories", "GET", "/api/categories", risk="read",
            desc="Catalog categories with agent counts."),
        cap("my_agents", "GET", "/api/my-agents", risk="read",
            desc="The agents this user has installed."),
        cap("list_reviews", "GET", "/api/agents/{aid}/reviews", risk="read",
            desc="Reviews for an agent.", params={"aid": "agent id"}),
        cap("install_agent", "POST", "/api/agents/{aid}/install", risk="write",
            desc="Install an agent into the user's workspace.",
            params={"aid": "agent id", "config": "optional install config object"}),
        cap("test_agent", "POST", "/api/agents/{aid}/test", risk="write",
            desc="Run the listing's sandbox tester with a sample input.",
            params={"aid": "agent id", "input": "the test input"}),
    ],
}
