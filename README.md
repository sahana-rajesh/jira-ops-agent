# Jira / Confluence Ops Agent

An AI agent that automates the manual work of release/program management:
reading through Jira tickets and comment threads, then generating a release
health summary, a go/no-go recommendation, and a stakeholder status update
ready to paste into Confluence.

Built on Anthropic's Claude API, with a Streamlit dashboard on top so the
output is reviewable, not just printed to a terminal.

## Why this project

In release management, a large amount of time goes into manually reading
ticket status and comment threads across a sprint, then synthesizing that
into a go/no-go call and a status update for stakeholders. This project
automates that synthesis step: point it at ticket data (Jira export, API
pull, or the included synthetic dataset) and it produces the same artifacts
a release manager would otherwise write by hand.

## Features

- **Release Dashboard** — status/priority breakdown, blocked-ticket count, story points, filterable by release.
- **AI Release Summary** — a 4-6 sentence health summary calling out the biggest risk drivers, citing specific ticket keys.
- **Go/No-Go Assessment** — a GO / NO-GO / CONDITIONAL GO recommendation with rationale, color-coded in the UI.
- **Stakeholder Update Draft** — a markdown-formatted status update (Overview, Completed, At Risk, Blockers, Next Steps) with a one-click download, ready to paste into Confluence.
- **Ticket Explorer** — summarizes an individual ticket's comment thread and suggests one concrete next action.
- **Demo Mode** — the app works immediately with zero setup using pre-generated sample AI output, so it's always demoable even without an API key or credits.

## Architecture

```
jira-ops-agent/
├── app.py                  # Streamlit UI
├── src/
│   ├── data.py              # synthetic Jira ticket generator + loader
│   └── agent.py             # JiraOpsAgent — wraps the Claude API, handles demo-mode fallback
├── data/
│   ├── mock_tickets.json    # pre-generated sample dataset (42 tickets across 3 releases)
│   └── demo_outputs.json    # canned AI outputs used in Demo Mode
├── requirements.txt
├── .env.example
└── README.md
```

The dataset is synthetic (bank/enterprise-style release tickets: SIT,
regression, CAB approval, rollback plans, upstream dependencies) so the repo
is safe to make public with no risk of exposing real company data.

## Setup

```bash
git clone <this-repo>
cd jira-ops-agent
pip install -r requirements.txt
cp .env.example .env   # add your Anthropic API key, or skip to run in Demo Mode
streamlit run app.py
```


## Using real Jira/Confluence data (future enhancement)

The current version ships with synthetic data for portability, but the
`src/data.py` `load_tickets()` function is the only integration point that
needs to change to go live:

1. Use the [Jira REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/) (`/rest/api/3/search`) to pull tickets for a given sprint/release JQL query, and reshape the response to match the same ticket schema used here (`key`, `summary`, `status`, `priority`, `assignee`, `comments`, etc.).
2. To publish the generated stakeholder update directly to Confluence, use the [Confluence REST API](https://developer.atlassian.com/cloud/confluence/rest/v2/) `POST /pages` endpoint with the markdown converted to Confluence storage format.

Both are drop-in replacements — the agent and UI layers don't need to change.

## Tech stack

- **Streamlit** — dashboard UI
- **Anthropic Claude API** (`claude-sonnet-5`) — release summarization, go/no-go reasoning, status update drafting
- **Pandas** — ticket data handling and charting
- **Python** — synthetic data generation, agent logic

## Roadmap

- [ ] Live Jira REST API integration
- [ ] Auto-publish status updates to a Confluence page via API
- [ ] Slack notification when a release flips to NO-GO
- [ ] Historical trend view across multiple releases (deployment frequency, rollback rate)

## About

Built by [Sahana Rajesh](mailto:sraje015@ucr.edu) — Program/Release
Management professional with experience in release governance, ITSM
(Remedy/ServiceNow), Agile delivery, and applied AI automation for
process improvement.
