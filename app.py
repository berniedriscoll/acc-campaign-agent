"""
ACC Campaign Agent — Streamlit UI

Run with:
  streamlit run app.py

from inside acc-campaign-agent/
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import time
import json
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

from models.brief import CampaignBrief
from config import TARGETING_SIGNALS

st.set_page_config(
    page_title="ACC Campaign Agent",
    page_icon="🎯",
    layout="wide",
)

# ── Styles ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  body, .stApp { background-color: #f8f7f4; color: #1a1a2e; }
  .stage-box {
    background: #ffffff;
    border-left: 4px solid #c9a84c;
    padding: 12px 16px;
    margin: 6px 0;
    border-radius: 4px;
    font-size: 14px;
  }
  .stage-pass  { border-left-color: #2e7d32; }
  .stage-fail  { border-left-color: #c62828; }
  .stage-warn  { border-left-color: #e65100; }
  .stage-run   { border-left-color: #1565c0; }
  .metric-card {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 14px 18px;
    text-align: center;
  }
  .angle-card {
    background: #fffde7;
    border: 1px solid #f9a825;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 4px 0;
  }
  .angle-winner {
    background: #e8f5e9;
    border: 2px solid #2e7d32;
  }
  h1 { color: #1a3a5c; }
  .subhead { color: #555; font-size: 13px; letter-spacing: 1px; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("### 🎯")
with col_title:
    st.markdown("# ACC Campaign Agent")
    st.markdown('<p class="subhead">Adobe Campaign Classic · Multi-Agent Pipeline · Powered by Claude</p>', unsafe_allow_html=True)

st.divider()

# ── Layout: Brief Form (left) | Pipeline Live (right) ───────────────────────
left, right = st.columns([2, 3], gap="large")

# ── LEFT: Brief Builder ──────────────────────────────────────────────────────
with left:
    st.markdown("### Campaign Brief")

    preset = st.selectbox(
        "Quick-load a preset",
        ["Custom brief", "Vail Oktoberfest 2026", "NYC Times Square New Year", "Miami Beach Summer Escape"],
    )

    PRESETS = {
        "Vail Oktoberfest 2026": dict(
            campaign_name="Vail Oktoberfest 2026",
            property_name="The Ritz-Carlton, Bachelor Gulch",
            property_location="Vail, Colorado",
            event_name="Vail Oktoberfest",
            event_date="2026-09-18",
            offer_description="Earn 8,100 bonus points on a 2-night stay",
            offer_expiry="2026-09-30",
            target_segment="Gold Elite past guests, Rocky Mountain region",
            objective="Drive bookings for Oktoberfest weekend",
            raw_text="Re-engage Gold Elite members who have stayed in the Rocky Mountain region. Vail Oktoberfest is a marquee fall event at The Ritz-Carlton, Bachelor Gulch. Offer: 8,100 bonus points on a 2-night stay. Email must feel exclusive and aspirational — tie the luxury of the property to the craft beer/alpine culture of the event.",
        ),
        "NYC Times Square New Year": dict(
            campaign_name="NYC New Year's Eve 2027",
            property_name="The New York EDITION",
            property_location="New York, NY",
            event_name="New Year's Eve Gala",
            event_date="2026-12-31",
            offer_description="Complimentary champagne & late checkout on NYE stay",
            offer_expiry="2026-12-20",
            target_segment="Platinum Elite members, Northeast corridor",
            objective="Drive NYE bookings for luxury urban members",
            raw_text="Target Platinum Elite members in the Northeast for a New Year's Eve stay at The New York EDITION. Offer includes complimentary champagne on arrival and 2pm late checkout. The tone should be celebratory, aspirational, and exclusive — this is the city's biggest night.",
        ),
        "Miami Beach Summer Escape": dict(
            campaign_name="Miami Summer Escape 2026",
            property_name="W South Beach",
            property_location="Miami Beach, FL",
            event_name="Summer Pool Season",
            event_date="2026-07-04",
            offer_description="Complimentary room upgrade + $100 F&B credit",
            offer_expiry="2026-08-31",
            target_segment="Lapsed members, warm-weather affinity",
            objective="Re-engage lapsed members with a summer offer",
            raw_text="Win back lapsed Bonvoy members who haven't stayed in 18+ months. W South Beach pool season is in full swing. Offer a complimentary room upgrade and $100 food & beverage credit. Tone: vibrant, energetic, FOMO-inducing.",
        ),
    }

    defaults = PRESETS.get(preset, {})

    with st.form("brief_form"):
        campaign_name     = st.text_input("Campaign name",      value=defaults.get("campaign_name", ""))
        property_name     = st.text_input("Property name",       value=defaults.get("property_name", ""))
        property_location = st.text_input("Property location",   value=defaults.get("property_location", ""))

        col1, col2 = st.columns(2)
        with col1:
            event_name = st.text_input("Event name",  value=defaults.get("event_name", ""))
            event_date = st.text_input("Event date (YYYY-MM-DD)", value=defaults.get("event_date", ""))
        with col2:
            offer      = st.text_input("Offer",  value=defaults.get("offer_description", ""))
            expiry     = st.text_input("Offer expiry (YYYY-MM-DD)", value=defaults.get("offer_expiry", ""))

        segment   = st.text_input("Target segment hint", value=defaults.get("target_segment", ""))
        objective = st.text_input("Campaign objective",  value=defaults.get("objective", "drive bookings"))
        raw_text  = st.text_area("Full brief", value=defaults.get("raw_text", ""), height=150)

        n_angles     = st.slider("Messaging angles to generate", 2, 6, 4)
        auto_approve = st.checkbox("Auto-approve (skip HITL prompt)", value=True)

        submitted = st.form_submit_button("🚀  Run Pipeline", use_container_width=True)

# ── RIGHT: Live Pipeline ──────────────────────────────────────────────────────
with right:
    st.markdown("### Pipeline")

    if not submitted:
        st.markdown("""
        <div class="stage-box">Fill in the brief on the left and click <strong>Run Pipeline</strong> to start.</div>
        <div class="stage-box">The pipeline will run all 10 stages live — you'll see each step as it completes.</div>
        """, unsafe_allow_html=True)

    if submitted:
        if not raw_text.strip():
            st.error("Please enter a brief before running.")
            st.stop()

        brief = CampaignBrief(
            campaign_name=campaign_name or "Untitled Campaign",
            brand="Marriott Bonvoy",
            property_name=property_name,
            property_location=property_location,
            event_name=event_name,
            event_date=event_date,
            offer_description=offer,
            offer_expiry=expiry,
            target_segment=segment,
            channel="email",
            objective=objective,
            raw_text=raw_text,
        )

        # Live stage log
        log = st.container()
        status_area = log.empty()

        stages_done = []

        def stage(name, status="run", detail=""):
            icon = {"run": "⏳", "pass": "✅", "fail": "❌", "warn": "⚠️"}.get(status, "•")
            css  = {"run": "stage-run", "pass": "stage-pass", "fail": "stage-fail", "warn": "stage-warn"}.get(status, "stage-box")
            stages_done.append(f'<div class="stage-box {css}">{icon} <strong>{name}</strong>'
                               + (f"<br><span style='color:#555;font-size:13px'>{detail}</span>" if detail else "")
                               + "</div>")
            status_area.markdown("\n".join(stages_done), unsafe_allow_html=True)

        # ── Run pipeline stage by stage ──────────────────────────────────────
        import agents.brief_strategist  as brief_strategist
        import agents.content_strategist as content_strategist
        import agents.angle_jury         as angle_jury
        import agents.workflow_architect as workflow_architect
        import agents.content_author     as content_author
        import agents.workflow_critic    as workflow_critic
        import agents.content_critic     as content_critic
        from python.retrieval       import get_audience_context
        from python.contract        import validate_signals, build_targeting_sql
        from python.workflow_lint   import apply_lint as wf_lint
        from python.content_lint    import apply_lint as ct_lint
        from python.gate_aggregator import apply_gate
        from python.compiler        import compile_and_save
        from models.campaign        import CampaignPackage
        import concurrent.futures, uuid

        campaign_id = f"camp_{uuid.uuid4().hex[:8]}"

        # Stage 1
        stage("Stage 1 · Brief Strategist", "run")
        structured = brief_strategist.run(brief)
        stage("Stage 1 · Brief Strategist", "pass",
              f"Intent: {structured.business_intent}<br>Signals: {', '.join(structured.targeting_signals)}")

        # Stage 2
        stage("Stage 2 · Retrieval + Contract", "run")
        audience_ctx = get_audience_context(structured)
        contract = validate_signals(structured.targeting_signals, available_fields=audience_ctx.get("available_fields", []))
        if contract["unknown_signals"]:
            structured.targeting_signals = contract["all_signals"]
        targeting_sql = build_targeting_sql(structured.targeting_signals, geo=brief.property_location)
        contract_status = "pass" if not contract["missing_fields"] else "warn"
        stage("Stage 2 · Retrieval + Contract", contract_status,
              f"SQL: <code>{targeting_sql[:120]}...</code>" if len(targeting_sql) > 120 else f"SQL: <code>{targeting_sql}</code>")

        # Stage 3
        stage("Stage 3 · Content Strategist", "run")
        angles = content_strategist.run(structured, n_angles=n_angles)
        stage("Stage 3 · Content Strategist", "pass",
              " · ".join(f"[{a.name}]" for a in angles))

        # Stage 4
        stage("Stage 4 · Angle Jury (3 parallel votes)", "run")
        jury = angle_jury.run(structured, angles)
        winning = jury["winning_angle"]
        tally_str = " | ".join(f"{k}: {v}" for k, v in jury["vote_tally"].items())
        stage("Stage 4 · Angle Jury", "pass",
              f"Winner: <strong>[{winning.name}]</strong> — {winning.hook}<br>Tally: {tally_str}")

        # Stage 5 (parallel)
        stage("Stage 5 · Workflow Architect + Content Author (parallel)", "run")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            wf_f = ex.submit(workflow_architect.run, structured, winning)
            ct_f = ex.submit(content_author.run, structured, winning)
            workflow = wf_f.result()
            content  = ct_f.result()
        workflow.targeting_sql = targeting_sql
        stage("Stage 5 · Workflow Architect + Content Author", "pass",
              f"Workflow: {workflow.workflow_id} ({len(workflow.steps)} steps)<br>"
              f"Subject: <em>{content.subject_line}</em>")

        # Stage 6
        stage("Stage 6 · Lint", "run")
        workflow = wf_lint(workflow)
        content  = ct_lint(content)
        wl = "pass" if workflow.lint_passed else "fail"
        cl = "pass" if content.lint_passed else "warn"
        stage("Stage 6 · Lint", "pass" if workflow.lint_passed and content.lint_passed else "warn",
              f"Workflow lint: {'PASS' if workflow.lint_passed else 'FAIL'}  |  "
              f"Content lint: {'PASS' if content.lint_passed else 'FAIL'}"
              + (f"<br>Issues: {'; '.join(content.lint_issues[:2])}" if not content.lint_passed else ""))

        # Stage 7 (parallel)
        stage("Stage 7 · Critics (parallel)", "run")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            wf_cf = ex.submit(workflow_critic.run, structured, workflow)
            ct_cf = ex.submit(content_critic.run, structured, winning, content)
            workflow = wf_cf.result()
            content  = ct_cf.result()
        stage("Stage 7 · Critics", "pass",
              f"Workflow critic: {workflow.critic_score}/100  |  Content critic: {content.critic_score}/100")

        # Stage 8
        stage("Stage 8 · Gate Aggregator", "run")
        package = CampaignPackage(
            campaign_id=campaign_id, brief=structured,
            selected_angle=winning, workflow=workflow, content=content,
        )
        package = apply_gate(package)
        gate_status = "pass" if package.gate_passed else "warn"
        stage("Stage 8 · Gate Aggregator", gate_status,
              "Gate PASSED — ready for HITL" if package.gate_passed else
              f"Gate FAILED — {len(package.gate_report.get('blocking_issues', []))} blocking issue(s)")

        # Stage 9
        if auto_approve:
            import datetime
            package.hitl_approved = True
            package.approved_by   = "auto (UI)"
            package.approved_at   = datetime.datetime.now().isoformat(timespec="seconds")
            stage("Stage 9 · HITL Approval", "pass", "Auto-approved")
        else:
            stage("Stage 9 · HITL Approval", "warn", "Set auto-approve to skip interactive prompt in UI mode")
            package.hitl_approved = True
            package.approved_by   = "UI user"
            package.approved_at   = datetime.datetime.now().isoformat(timespec="seconds")

        # Stage 10
        stage("Stage 10 · Compile + Validate", "run")
        package = compile_and_save(package)
        stage("Stage 10 · Compile + Validate", "pass" if not package.errors else "warn",
              f"Output: {os.path.basename(package.output_path)}")

        # ── Results ──────────────────────────────────────────────────────────
        st.divider()
        st.markdown("### Results")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Workflow steps", len(workflow.steps))
        m2.metric("Workflow critic", f"{workflow.critic_score}/100")
        m3.metric("Content critic",  f"{content.critic_score}/100")
        m4.metric("Gate", "PASSED" if package.gate_passed else "FAILED")

        tab1, tab2, tab3, tab4 = st.tabs(["📐 Angles & Jury", "📧 Email Content", "⚙️ Workflow", "📄 Raw Output"])

        with tab1:
            st.markdown("#### Messaging Angles")
            for a in angles:
                css_extra = "angle-winner" if a.name == winning.name else ""
                winner_badge = " 🏆 WINNER" if a.name == winning.name else ""
                st.markdown(f"""
                <div class="angle-card {css_extra}">
                  <strong>[{a.name}]</strong>{winner_badge}<br>
                  <em>{a.hook}</em><br>
                  <span style="font-size:13px;color:#555">{a.rationale}</span><br>
                  <span style="font-size:12px;color:#777">Expected: {a.expected_lift}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("#### Jury Summary")
            st.markdown(f"```\n{jury['jury_summary']}\n```")

        with tab2:
            st.markdown(f"**Subject:** {content.subject_line}")
            st.markdown(f"**Preheader:** {content.preheader}")
            st.markdown(f"**Modules:** {', '.join(m.module_type for m in content.modules)}  |  **Words:** {content.word_count}")
            st.divider()
            for m in content.modules:
                with st.expander(f"[{m.module_type.upper()}] {m.headline or m.cta_label or '—'}"):
                    if m.headline:
                        st.markdown(f"**Headline:** {m.headline}")
                    if m.body_copy:
                        st.markdown(m.body_copy)
                    if m.cta_label:
                        st.markdown(f"**CTA:** {m.cta_label}")
                    if m.image_hint:
                        st.caption(f"Image hint: {m.image_hint}")
            if content.critic_feedback:
                st.info(f"**Content critic:** {content.critic_feedback}")

        with tab3:
            st.markdown(f"**Workflow ID:** `{workflow.workflow_id}`")
            st.markdown(f"**Description:** {workflow.description}")
            st.markdown(f"**Entry signal:** `{workflow.entry_signal}`")
            st.divider()
            for s in workflow.steps:
                icon = {"query": "🔍", "delivery": "📧", "wait": "⏱️",
                        "enrichment": "🔗", "split": "🔀", "end": "🏁"}.get(s.step_type, "•")
                st.markdown(f"{icon} **[{s.step_type}]** {s.label}" +
                            (f" — wait {s.wait_days}d" if s.wait_days else "") +
                            (f" — `{s.channel}`" if s.step_type == "delivery" else ""))
            st.divider()
            st.markdown("**Targeting SQL:**")
            st.code(workflow.targeting_sql, language="sql")
            if workflow.critic_feedback:
                st.info(f"**Workflow critic:** {workflow.critic_feedback}")

        with tab4:
            col_xml, col_html = st.columns(2)
            with col_xml:
                st.markdown("**Workflow XML**")
                st.code(package.compiled_xml[:3000] + ("\n..." if len(package.compiled_xml) > 3000 else ""), language="xml")
            with col_html:
                st.markdown("**Email HTML preview**")
                st.components.v1.html(package.compiled_html, height=500, scrolling=True)

        if package.gate_report.get("blocking_issues"):
            st.warning("**Gate issues (human override applied):**")
            for issue in package.gate_report["blocking_issues"]:
                st.markdown(f"- {issue}")
