"""
agent.py
Core AI logic for the Jira/Confluence Ops Agent.

JiraOpsAgent wraps the Anthropic Claude API to turn raw ticket data into:
  1. A release health summary
  2. A go/no-go recommendation with rationale
  3. A stakeholder-ready status update (Confluence-style markdown)
  4. A per-ticket blocker summary

If no API key is available (or demo_mode=True), the agent falls back to
canned "demo mode" outputs stored in data/demo_outputs.json, so the app is
always demoable without burning API credits or requiring a key.
"""

import json
import os
from pathlib import Path

try:
    import anthropic
except ImportError:  # pragma: no cover - anthropic is an optional runtime dep
    anthropic = None

MODEL = "claude-sonnet-5"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_demo_outputs():
    path = DATA_DIR / "demo_outputs.json"
    with open(path) as f:
        return json.load(f)


def _ticket_context(tickets, release):
    """Flatten a release's tickets into a compact text block for the prompt."""
    lines = []
    for t in tickets:
        if t["release"] != release:
            continue
        comment_str = " | ".join(f"{c['author']}: {c['text']}" for c in t["comments"])
        lines.append(
            f"- [{t['key']}] ({t['status']}, {t['priority']} priority, {t['type']}) "
            f"{t['summary']} — Assignee: {t['assignee']}. Comments: {comment_str}"
        )
    return "\n".join(lines)


class JiraOpsAgent:
    def __init__(self, api_key: str | None = None, demo_mode: bool = False):
        self.demo_mode = demo_mode or not api_key
        self.client = None
        if not self.demo_mode and anthropic is not None:
            self.client = anthropic.Anthropic(api_key=api_key)
        self._demo = _load_demo_outputs()

    # ------------------------------------------------------------------ #
    # Internal helper
    # ------------------------------------------------------------------ #
    def _ask_claude(self, system_prompt: str, user_prompt: str, max_tokens: int = 700) -> str:
        if self.demo_mode or self.client is None:
            raise RuntimeError("Agent is in demo mode; use the *_demo methods instead.")
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    # ------------------------------------------------------------------ #
    # Public methods (each checks demo_mode and falls back automatically)
    # ------------------------------------------------------------------ #
    def summarize_release(self, tickets, release: str) -> str:
        if self.demo_mode:
            return self._demo.get(release, {}).get(
                "summary", "No demo summary available for this release."
            )
        context = _ticket_context(tickets, release)
        system_prompt = (
            "You are an IT release management assistant. Summarize the health of a "
            "software release for an engineering leadership audience: overall status, "
            "key risk themes, and which tickets are driving the biggest risk. Be concise "
            "and specific, referencing ticket keys."
        )
        user_prompt = f"Release: {release}\n\nTickets:\n{context}\n\nWrite a 4-6 sentence release health summary."
        return self._ask_claude(system_prompt, user_prompt)

    def go_no_go_recommendation(self, tickets, release: str) -> str:
        if self.demo_mode:
            return self._demo.get(release, {}).get(
                "go_no_go", "No demo recommendation available for this release."
            )
        context = _ticket_context(tickets, release)
        system_prompt = (
            "You are supporting a release governance go/no-go decision. Based on the "
            "ticket data, issue a clear recommendation: GO, NO-GO, or CONDITIONAL GO. "
            "Justify it with specific blockers, open high-priority tickets, or risks. "
            "Format as:\nRecommendation: <GO/NO-GO/CONDITIONAL GO>\nRationale: <2-4 sentences>"
        )
        user_prompt = f"Release: {release}\n\nTickets:\n{context}"
        return self._ask_claude(system_prompt, user_prompt)

    def draft_status_update(self, tickets, release: str) -> str:
        if self.demo_mode:
            return self._demo.get(release, {}).get(
                "status_update", "No demo status update available for this release."
            )
        context = _ticket_context(tickets, release)
        system_prompt = (
            "You write concise, well-formatted stakeholder status updates suitable for "
            "posting to a Confluence page. Use markdown with headers and bullet points. "
            "Include sections: Overview, Completed This Period, In Progress / At Risk, "
            "Blockers Requiring Attention, Next Steps."
        )
        user_prompt = f"Release: {release}\n\nTickets:\n{context}\n\nDraft the status update."
        return self._ask_claude(system_prompt, user_prompt, max_tokens=900)

    def summarize_ticket(self, ticket: dict) -> str:
        if self.demo_mode:
            return (
                f"[Demo mode] {ticket['key']} is currently '{ticket['status']}'. "
                f"Latest comment: \"{ticket['comments'][-1]['text']}\" "
                "Connect an API key to get a live AI-generated summary and suggested next action."
            )
        comment_str = "\n".join(f"- {c['author']} ({c['date']}): {c['text']}" for c in ticket["comments"])
        system_prompt = (
            "You summarize a single Jira ticket's status and comment thread for a busy "
            "program manager, and suggest one concrete next action."
        )
        user_prompt = (
            f"Ticket {ticket['key']}: {ticket['summary']}\n"
            f"Status: {ticket['status']}, Priority: {ticket['priority']}, Assignee: {ticket['assignee']}\n"
            f"Comments:\n{comment_str}\n\n"
            "Summarize in 2-3 sentences and suggest one next action."
        )
        return self._ask_claude(system_prompt, user_prompt, max_tokens=300)
