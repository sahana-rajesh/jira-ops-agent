"""
Jira/Confluence Ops Agent — Streamlit dashboard

An AI agent that reads release/sprint ticket data and automates the tasks a
release/program manager does manually: summarizing release health, making a
go/no-go call, and drafting the stakeholder status update that would
otherwise get posted to Confluence.

Run:
    streamlit run app.py
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import os

sys.path.append(str(Path(__file__).resolve().parent))
from src.data import load_tickets
from src.agent import JiraOpsAgent

load_dotenv()

st.set_page_config(page_title="Jira/Confluence Ops Agent", page_icon="🛠️", layout="wide")

# --------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------- #
st.sidebar.title("🛠️ Ops Agent Controls")

env_key = os.environ.get("ANTHROPIC_API_KEY", "")
api_key_input = st.sidebar.text_input(
    "Anthropic API key",
    value=env_key,
    type="password",
    help="Optional. Leave blank to use Demo Mode with pre-generated sample AI output.",
)
demo_mode = st.sidebar.checkbox(
    "Force Demo Mode (no live API calls)",
    value=(env_key == "" and api_key_input == ""),
)

tickets = load_tickets()
releases = sorted({t["release"] for t in tickets})
selected_release = st.sidebar.selectbox("Release", releases)

st.sidebar.markdown("---")
st.sidebar.caption(
    "This dashboard runs on synthetic sample data so it works instantly with "
    "no Jira account required. See README for how to point it at a real "
    "Jira instance via the REST API."
)

agent = JiraOpsAgent(api_key=api_key_input or None, demo_mode=demo_mode)
if agent.demo_mode:
    st.sidebar.info("Running in **Demo Mode** — showing pre-generated sample AI output.")
else:
    st.sidebar.success("Connected to Claude API — live AI generation enabled.")

release_tickets = [t for t in tickets if t["release"] == selected_release]
df = pd.DataFrame(release_tickets)

st.title("Jira / Confluence Ops Agent")
st.caption(
    "AI-assisted release governance: automated health summaries, go/no-go "
    "recommendations, and stakeholder status updates from ticket data."
)

tab_dashboard, tab_summary, tab_gonogo, tab_update, tab_ticket = st.tabs(
    ["📊 Release Dashboard", "🧠 AI Release Summary", "🚦 Go/No-Go Assessment",
     "📝 Stakeholder Update", "🔍 Ticket Explorer"]
)

# --------------------------------------------------------------------- #
# Tab 1: Release Dashboard
# --------------------------------------------------------------------- #
with tab_dashboard:
    col1, col2, col3, col4 = st.columns(4)
    total = len(df)
    blocked = int((df["status"] == "Blocked").sum()) if total else 0
    done = int((df["status"] == "Done").sum()) if total else 0
    done_pct = round(100 * done / total) if total else 0

    col1.metric("Total Tickets", total)
    col2.metric("Blocked", blocked)
    col3.metric("Done", f"{done_pct}%")
    col4.metric("Story Points", int(df["story_points"].sum()) if total else 0)

    st.subheader("Status Breakdown")
    if total:
        st.bar_chart(df["status"].value_counts())

    st.subheader("Priority Breakdown")
    if total:
        st.bar_chart(df["priority"].value_counts())

    st.subheader("Tickets")
    st.dataframe(
        df[["key", "summary", "status", "priority", "type", "assignee", "sprint", "story_points"]],
        use_container_width=True,
        hide_index=True,
    )

# --------------------------------------------------------------------- #
# Tab 2: AI Release Summary
# --------------------------------------------------------------------- #
with tab_summary:
    st.subheader(f"AI Release Health Summary — {selected_release}")
    if st.button("Generate Summary", key="summary_btn"):
        with st.spinner("Analyzing release tickets..."):
            summary = agent.summarize_release(release_tickets, selected_release)
        st.write(summary)

# --------------------------------------------------------------------- #
# Tab 3: Go/No-Go Assessment
# --------------------------------------------------------------------- #
with tab_gonogo:
    st.subheader(f"Go/No-Go Recommendation — {selected_release}")
    if st.button("Generate Recommendation", key="gonogo_btn"):
        with st.spinner("Evaluating release readiness..."):
            recommendation = agent.go_no_go_recommendation(release_tickets, selected_release)

        text_upper = recommendation.upper()
        if "NO-GO" in text_upper:
            st.error("Recommendation: NO-GO")
        elif "CONDITIONAL" in text_upper:
            st.warning("Recommendation: CONDITIONAL GO")
        elif "GO" in text_upper:
            st.success("Recommendation: GO")

        st.write(recommendation)

# --------------------------------------------------------------------- #
# Tab 4: Stakeholder Update Draft
# --------------------------------------------------------------------- #
with tab_update:
    st.subheader(f"Draft Stakeholder Status Update — {selected_release}")
    st.caption("Formatted for direct copy/paste into a Confluence page.")
    if st.button("Draft Update", key="update_btn"):
        with st.spinner("Drafting status update..."):
            update_text = agent.draft_status_update(release_tickets, selected_release)
        st.session_state["update_text"] = update_text

    if "update_text" in st.session_state:
        st.markdown(st.session_state["update_text"])
        st.download_button(
            "Download as Markdown",
            data=st.session_state["update_text"],
            file_name=f"{selected_release.replace(' ', '_')}_status_update.md",
            mime="text/markdown",
        )

# --------------------------------------------------------------------- #
# Tab 5: Ticket Explorer
# --------------------------------------------------------------------- #
with tab_ticket:
    st.subheader("Single Ticket Summary")
    if release_tickets:
        ticket_keys = [t["key"] for t in release_tickets]
        selected_key = st.selectbox("Select a ticket", ticket_keys)
        ticket = next(t for t in release_tickets if t["key"] == selected_key)

        st.write(f"**{ticket['key']}** — {ticket['summary']}")
        st.write(f"Status: `{ticket['status']}` | Priority: `{ticket['priority']}` | Assignee: {ticket['assignee']}")
        st.write("**Comment thread:**")
        for c in ticket["comments"]:
            st.markdown(f"- *{c['date']}* — **{c['author']}**: {c['text']}")

        if st.button("Summarize Ticket + Suggest Next Action"):
            with st.spinner("Reading comment thread..."):
                ticket_summary = agent.summarize_ticket(ticket)
            st.info(ticket_summary)
    else:
        st.write("No tickets in this release.")
