"""
data.py
Generates a realistic, synthetic Jira/Confluence dataset so the AI Ops Agent
can be demoed with zero external accounts or credentials.

Run directly to (re)write data/mock_tickets.json:
    python src/data.py
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

RELEASES = ["Release 3.1", "Release 3.2", "Release 3.3"]
SPRINTS = {
    "Release 3.1": ["Sprint 21", "Sprint 22"],
    "Release 3.2": ["Sprint 23", "Sprint 24"],
    "Release 3.3": ["Sprint 25", "Sprint 26"],
}
ASSIGNEES = [
    "M. Chen", "R. Patel", "J. Alvarez", "K. Nguyen", "S. Osei",
    "T. Fischer", "L. Romano", "A. Whitfield",
]
ISSUE_TYPES = ["Story", "Bug", "Task", "Change Request"]
PRIORITIES = ["Highest", "High", "Medium", "Low"]

STATUS_WEIGHTS = {
    "Release 3.1": [("Done", 0.9), ("Blocked", 0.05), ("In Progress", 0.05)],
    "Release 3.2": [("Done", 0.45), ("In Progress", 0.25), ("Blocked", 0.2), ("Ready for QA", 0.1)],
    "Release 3.3": [("To Do", 0.5), ("In Progress", 0.3), ("Blocked", 0.2)],
}

SUMMARY_TEMPLATES = [
    "Update {system} API to support new {feature} schema",
    "Fix regression in {system} caused by upstream {dependency} change",
    "Add rollback plan for {system} deployment",
    "Resolve SIT failure in {system} integration test suite",
    "Implement {feature} for {system} per compliance requirement",
    "Investigate CI/CD pipeline timeout during {system} build",
    "Update deployment runbook for {system} go-live",
    "Address smoke test failure on {system} after {dependency} patch",
    "Coordinate CAB approval for {system} production change",
    "Refactor {system} data layer for {feature} tracking",
]
SYSTEMS = ["Payments Gateway", "Loan Origination", "Customer Portal", "Reporting Service", "Auth Service", "Ledger Engine"]
FEATURES = ["fraud scoring", "audit logging", "multi-currency", "SSO", "real-time notifications", "regulatory reporting"]
DEPENDENCIES = ["Kafka", "Oracle DB", "Auth0", "internal SDK", "third-party vendor API", "network firewall"]

BLOCKER_COMMENTS = [
    "Waiting on QA sign-off — regression suite still running, ETA end of day.",
    "Blocked by upstream dependency team; {dep} change not yet merged.",
    "CAB approval pending, change window not yet confirmed.",
    "Rollback plan needs revision before this can move to Ready for QA.",
    "Environment contention with another release in the same deployment window.",
    "Data validation failed in staging; schema mismatch found during UAT.",
    "Waiting on security review sign-off before production deployment.",
    "Dependent ticket {dep_ticket} not yet resolved, blocking integration testing.",
]
PROGRESS_COMMENTS = [
    "SIT passed, moving to regression testing.",
    "Deployment runbook drafted and shared with ops team for review.",
    "Smoke tests green in staging, monitoring for 24 hours before sign-off.",
    "Stakeholder review completed, no blocking feedback.",
    "Rollback plan validated in staging environment.",
]
DONE_COMMENTS = [
    "Deployed to production successfully, no incidents reported.",
    "Post-release review completed, closing ticket.",
    "Verified in production, metrics stable.",
]


def _pick_status(release: str) -> str:
    options, weights = zip(*STATUS_WEIGHTS[release])
    return random.choices(options, weights=weights, k=1)[0]


def _comment_for_status(status: str, dep: str, dep_ticket: str):
    if status == "Blocked":
        text = random.choice(BLOCKER_COMMENTS).format(dep=dep, dep_ticket=dep_ticket)
    elif status in ("In Progress", "Ready for QA"):
        text = random.choice(PROGRESS_COMMENTS)
    elif status == "Done":
        text = random.choice(DONE_COMMENTS)
    else:
        text = "Ticket created, groomed for upcoming sprint."
    return text


def generate_mock_tickets(n: int = 42):
    tickets = []
    start_date = datetime(2026, 5, 1)

    for i in range(1, n + 1):
        release = random.choice(RELEASES)
        sprint = random.choice(SPRINTS[release])
        status = _pick_status(release)
        system = random.choice(SYSTEMS)
        feature = random.choice(FEATURES)
        dependency = random.choice(DEPENDENCIES)
        template = random.choice(SUMMARY_TEMPLATES)
        summary = template.format(system=system, feature=feature, dependency=dependency)

        created = start_date + timedelta(days=random.randint(0, 60))
        updated = created + timedelta(days=random.randint(0, 10))
        dep_ticket = f"OPS-{random.randint(100, 199)}"

        comment_text = _comment_for_status(status, dependency, dep_ticket)
        comments = [
            {
                "author": random.choice(ASSIGNEES),
                "date": (updated).strftime("%Y-%m-%d"),
                "text": comment_text,
            }
        ]
        # occasionally add a second comment for richer threads
        if random.random() < 0.4:
            comments.append(
                {
                    "author": random.choice(ASSIGNEES),
                    "date": (updated + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "text": random.choice(PROGRESS_COMMENTS + BLOCKER_COMMENTS).format(
                        dep=dependency, dep_ticket=dep_ticket
                    ),
                }
            )

        tickets.append(
            {
                "key": f"OPS-{200 + i}",
                "summary": summary,
                "type": random.choice(ISSUE_TYPES),
                "status": status,
                "priority": random.choices(PRIORITIES, weights=[0.1, 0.35, 0.4, 0.15], k=1)[0],
                "assignee": random.choice(ASSIGNEES),
                "release": release,
                "sprint": sprint,
                "story_points": random.choice([1, 2, 3, 5, 8]),
                "created": created.strftime("%Y-%m-%d"),
                "updated": updated.strftime("%Y-%m-%d"),
                "comments": comments,
            }
        )

    return tickets


def write_dataset(path: str = "data/mock_tickets.json", n: int = 42):
    tickets = generate_mock_tickets(n)
    out_path = Path(__file__).resolve().parent.parent / path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(tickets, f, indent=2)
    print(f"Wrote {len(tickets)} mock tickets to {out_path}")


def load_tickets(path: str = "data/mock_tickets.json"):
    file_path = Path(__file__).resolve().parent.parent / path
    with open(file_path) as f:
        return json.load(f)


if __name__ == "__main__":
    write_dataset()
