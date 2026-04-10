"""
ACC Campaign Agent — Streamlit UI

Run with:
  streamlit run app.py
from inside acc-campaign-agent/
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import streamlit.components.v1 as components
import concurrent.futures, uuid, json, datetime
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

from models.brief   import CampaignBrief
from models.campaign import CampaignPackage
from config         import TARGETING_SIGNALS
from python.variants import (
    COMMON_VARIANTS, EDGE_CASES, ALL_VARIANTS,
    get_variant, resolve_tokens, get_raw_tokens_html,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="ACC Campaign Agent", page_icon="🎯", layout="wide")

st.markdown("""
<style>
  body, .stApp { background-color: #f8f7f4; color: #1a1a2e; }
  .stage-box  { background:#fff; border-left:4px solid #c9a84c; padding:10px 14px; margin:4px 0; border-radius:4px; font-size:13px; }
  .stage-pass { border-left-color:#2e7d32; }
  .stage-fail { border-left-color:#c62828; }
  .stage-warn { border-left-color:#e65100; }
  .stage-run  { border-left-color:#1565c0; }
  .angle-card   { background:#fffde7; border:1px solid #f9a825; border-radius:6px; padding:10px 14px; margin:4px 0; }
  .angle-winner { background:#e8f5e9; border:2px solid #2e7d32; }
  .variant-card { background:#fff; border:1px solid #e0e0e0; border-radius:6px; padding:10px 14px; margin:6px 0; font-size:13px; }
  .verdict-box  { background:#f1f8e9; border:1px solid #7cb342; border-radius:6px; padding:12px 16px; font-family:monospace; font-size:13px; }
  .subhead { color:#777; font-size:12px; letter-spacing:1px; text-transform:uppercase; }
  code { background:#f0f0f0; padding:1px 5px; border-radius:3px; font-size:12px; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("## 🎯  ACC Campaign Agent")
st.markdown('<p class="subhead">Adobe Campaign Classic · Multi-Agent Pipeline · Powered by Claude</p>', unsafe_allow_html=True)
st.divider()

# ── Session state ─────────────────────────────────────────────────────────────
if "package"      not in st.session_state: st.session_state.package      = None
if "stages_html"  not in st.session_state: st.session_state.stages_html  = []
if "variant_id"   not in st.session_state: st.session_state.variant_id   = "gold_high"
if "verdict"      not in st.session_state: st.session_state.verdict      = {"verdict": "pending", "notes": ""}

# ── Presets ───────────────────────────────────────────────────────────────────
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

# ════════════════════════════════════════════════════════════════════════════
# ROW 1: Brief form (left) | Pipeline log (right)
# ════════════════════════════════════════════════════════════════════════════
col_brief, col_pipeline = st.columns([2, 3], gap="large")

with col_brief:
    st.markdown("### Campaign Brief")
    preset = st.selectbox("Quick-load a preset", ["Custom brief"] + list(PRESETS.keys()))
    defaults = PRESETS.get(preset, {})

    with st.form("brief_form"):
        campaign_name     = st.text_input("Campaign name",           value=defaults.get("campaign_name", ""))
        property_name     = st.text_input("Property name",           value=defaults.get("property_name", ""))
        property_location = st.text_input("Property location",       value=defaults.get("property_location", ""))
        c1, c2 = st.columns(2)
        with c1:
            event_name = st.text_input("Event name",                 value=defaults.get("event_name", ""))
            event_date = st.text_input("Event date (YYYY-MM-DD)",    value=defaults.get("event_date", ""))
        with c2:
            offer      = st.text_input("Offer",                      value=defaults.get("offer_description", ""))
            expiry     = st.text_input("Offer expiry (YYYY-MM-DD)",  value=defaults.get("offer_expiry", ""))
        segment   = st.text_input("Target segment hint",             value=defaults.get("target_segment", ""))
        objective = st.text_input("Campaign objective",              value=defaults.get("objective", "drive bookings"))
        raw_text  = st.text_area("Full brief",                       value=defaults.get("raw_text", ""), height=130)
        n_angles  = st.slider("Messaging angles", 2, 6, 4)
        submitted = st.form_submit_button("🚀  Run Pipeline", use_container_width=True)

with col_pipeline:
    st.markdown("### Pipeline")
    pipeline_area = st.empty()

    if not st.session_state.stages_html:
        pipeline_area.markdown(
            '<div class="stage-box">Fill in the brief and click <strong>Run Pipeline</strong>.</div>',
            unsafe_allow_html=True,
        )

# ── Run pipeline ──────────────────────────────────────────────────────────────
if submitted:
    if not raw_text.strip():
        with col_brief:
            st.error("Please enter a brief.")
        st.stop()

    brief = CampaignBrief(
        campaign_name=campaign_name or "Untitled",
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

    import agents.brief_strategist   as brief_strategist
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

    stages = []

    def push_stage(name, status="run", detail=""):
        icon = {"run":"⏳","pass":"✅","fail":"❌","warn":"⚠️"}.get(status,"•")
        css  = f"stage-box stage-{status}"
        detail_html = f"<br><span style='color:#555;font-size:12px'>{detail}</span>" if detail else ""
        stages.append(f'<div class="{css}">{icon} <strong>{name}</strong>{detail_html}</div>')
        pipeline_area.markdown("\n".join(stages), unsafe_allow_html=True)

    campaign_id = f"camp_{uuid.uuid4().hex[:8]}"

    push_stage("Stage 1 · Brief Strategist", "run")
    structured = brief_strategist.run(brief)
    push_stage("Stage 1 · Brief Strategist", "pass",
               f"Intent: {structured.business_intent} &nbsp;|&nbsp; Signals: {', '.join(structured.targeting_signals)}")

    push_stage("Stage 2 · Retrieval + Contract", "run")
    audience_ctx = get_audience_context(structured)
    contract = validate_signals(structured.targeting_signals, available_fields=audience_ctx.get("available_fields", []))
    if contract["unknown_signals"]:
        structured.targeting_signals = contract["all_signals"]
    targeting_sql = build_targeting_sql(structured.targeting_signals, geo=brief.property_location)
    push_stage("Stage 2 · Retrieval + Contract",
               "warn" if contract["missing_fields"] else "pass",
               f"SQL built &nbsp;|&nbsp; {len(structured.targeting_signals)} signals active")

    push_stage("Stage 3 · Content Strategist", "run")
    angles = content_strategist.run(structured, n_angles=n_angles)
    push_stage("Stage 3 · Content Strategist", "pass",
               " &nbsp;·&nbsp; ".join(f"[{a.name}]" for a in angles))

    push_stage("Stage 4 · Angle Jury (3 parallel votes)", "run")
    jury = angle_jury.run(structured, angles)
    winning = jury["winning_angle"]
    tally_str = " | ".join(f"{k}: {v}" for k, v in jury["vote_tally"].items())
    push_stage("Stage 4 · Angle Jury", "pass",
               f"Winner: <strong>[{winning.name}]</strong> — {winning.hook} &nbsp;|&nbsp; {tally_str}")

    push_stage("Stage 5 · Workflow Architect + Content Author (parallel)", "run")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        wf_f = ex.submit(workflow_architect.run, structured, winning)
        ct_f = ex.submit(content_author.run, structured, winning)
        workflow = wf_f.result()
        content  = ct_f.result()
    workflow.targeting_sql = targeting_sql
    push_stage("Stage 5 · Workflow + Content", "pass",
               f"Workflow: {workflow.workflow_id} ({len(workflow.steps)} steps) &nbsp;|&nbsp; Subject: <em>{content.subject_line}</em>")

    push_stage("Stage 6 · Lint", "run")
    workflow = wf_lint(workflow)
    content  = ct_lint(content)
    push_stage("Stage 6 · Lint",
               "pass" if workflow.lint_passed and content.lint_passed else "warn",
               f"Workflow: {'PASS' if workflow.lint_passed else 'FAIL'} &nbsp;|&nbsp; Content: {'PASS' if content.lint_passed else 'FAIL'}"
               + (f" — {content.lint_issues[0]}" if content.lint_issues else ""))

    push_stage("Stage 7 · Critics (parallel)", "run")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        wf_cf = ex.submit(workflow_critic.run, structured, workflow)
        ct_cf = ex.submit(content_critic.run, structured, winning, content)
        workflow = wf_cf.result()
        content  = ct_cf.result()
    push_stage("Stage 7 · Critics", "pass",
               f"Workflow critic: {workflow.critic_score}/100 &nbsp;|&nbsp; Content critic: {content.critic_score}/100")

    push_stage("Stage 8 · Gate Aggregator", "run")
    package = CampaignPackage(
        campaign_id=campaign_id, brief=structured,
        selected_angle=winning, workflow=workflow, content=content,
    )
    package = apply_gate(package)
    push_stage("Stage 8 · Gate Aggregator",
               "pass" if package.gate_passed else "warn",
               "Gate PASSED" if package.gate_passed else
               f"Gate FAILED — {len(package.gate_report.get('blocking_issues', []))} blocking issue(s) — awaiting HITL override")

    push_stage("Stage 9 · HITL Approval", "warn", "Awaiting reviewer decision below ↓")

    package = compile_and_save(package)
    push_stage("Stage 10 · Compile + Validate", "pass",
               f"XML + HTML compiled &nbsp;|&nbsp; {os.path.basename(package.output_path)}")

    st.session_state.package      = package
    st.session_state.stages_html  = stages
    st.session_state.verdict      = {"verdict": "pending", "notes": ""}
    st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# ROW 2: Results (only shown after pipeline runs)
# ════════════════════════════════════════════════════════════════════════════
package = st.session_state.package
if package is None:
    st.stop()

st.divider()

# ── Restore pipeline log ─────────────────────────────────────────────────────
if st.session_state.stages_html:
    pipeline_area.markdown("\n".join(st.session_state.stages_html), unsafe_allow_html=True)

# ── Metrics row ──────────────────────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Campaign",       package.brief.raw.campaign_name)
m2.metric("Winning Angle",  package.selected_angle.name)
m3.metric("Workflow Steps", len(package.workflow.steps))
m4.metric("Workflow Score", f"{package.workflow.critic_score}/100")
m5.metric("Content Score",  f"{package.content.critic_score}/100")

st.divider()

# ════════════════════════════════════════════════════════════════════════════
# THREE-PANEL ROW: HITL | Variant Selector | Email Preview
# ════════════════════════════════════════════════════════════════════════════
p_hitl, p_variant, p_preview = st.columns([1, 1, 2], gap="medium")

content  = package.content
workflow = package.workflow

# ── Panel 1: HITL Approval ───────────────────────────────────────────────────
with p_hitl:
    st.markdown("#### Approve")
    st.markdown(f'<p class="subhead">{package.brief.raw.campaign_name}</p>', unsafe_allow_html=True)

    gate = package.gate_report
    wt   = gate.get("workflow_track", {})
    ct   = gate.get("content_track", {})

    # Scores
    wf_color = "#2e7d32" if wt.get("critic_score", 0) >= 70 else "#e65100"
    ct_color = "#2e7d32" if ct.get("critic_score", 0) >= 70 else "#e65100"
    st.markdown(f"""
    <div class="variant-card">
      <strong>Workflow lint:</strong> {'✅ PASS' if wt.get('lint_passed') else '❌ FAIL'} &nbsp;
      <span style="color:{wf_color}"><strong>Score: {wt.get('critic_score',0)}/100</strong></span><br>
      <strong>Content lint:</strong> {'✅ PASS' if ct.get('lint_passed') else '⚠️ FAIL'} &nbsp;
      <span style="color:{ct_color}"><strong>Score: {ct.get('critic_score',0)}/100</strong></span>
    </div>
    """, unsafe_allow_html=True)

    if gate.get("blocking_issues"):
        with st.expander(f"⚠️ {len(gate['blocking_issues'])} blocking issue(s)", expanded=False):
            for issue in gate["blocking_issues"]:
                st.markdown(f"- {issue}")

    st.markdown("**Critic feedback**")
    st.caption(f"✏️ Workflow: {workflow.critic_feedback[:200] if workflow.critic_feedback else '—'}")
    st.caption(f"✏️ Content: {content.critic_feedback[:200] if content.critic_feedback else '—'}")

    st.divider()
    st.markdown("**Decision**")

    verdict_choice = st.radio("Verdict", ["approved", "rejected", "needs_revision"],
                               index=0 if st.session_state.verdict.get("verdict") != "rejected" else 1,
                               horizontal=False)
    notes = st.text_area("Notes", value=st.session_state.verdict.get("notes", ""), height=80,
                          placeholder="Optional reviewer notes…")

    if st.button("Submit Verdict", use_container_width=True, type="primary"):
        reviewer = "UI Reviewer"
        verdict_obj = {
            "verdict":     verdict_choice,
            "notes":       notes,
            "approved_by": reviewer,
            "approved_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "campaign_id": package.campaign_id,
        }
        st.session_state.verdict = verdict_obj
        package.hitl_approved = (verdict_choice == "approved")
        package.approved_by   = reviewer
        package.approved_at   = verdict_obj["approved_at"]
        package.hitl_notes    = notes
        # Update compiled JSON
        from python.compiler import compile_and_save
        package = compile_and_save(package)
        st.session_state.package = package
        st.rerun()

    verdict = st.session_state.verdict
    if verdict.get("verdict") != "pending":
        color = {"approved": "#e8f5e9", "rejected": "#ffebee", "needs_revision": "#fff3e0"}.get(verdict["verdict"], "#fff")
        border = {"approved": "#2e7d32", "rejected": "#c62828", "needs_revision": "#e65100"}.get(verdict["verdict"], "#ccc")
        st.markdown(f"""
        <div class="verdict-box" style="background:{color};border-color:{border};">
          {json.dumps(verdict, indent=2)}
        </div>
        """, unsafe_allow_html=True)


# ── Panel 2: Variant Selector ────────────────────────────────────────────────
with p_variant:
    st.markdown("#### Variant Preview")
    st.markdown(f'<p class="subhead">{package.brief.raw.campaign_name}</p>', unsafe_allow_html=True)

    st.markdown('<p class="subhead" style="margin-top:8px">Common Variants</p>', unsafe_allow_html=True)
    for v in COMMON_VARIANTS:
        if st.button(v["label"], key=f"v_{v['id']}",
                     use_container_width=True,
                     type="primary" if st.session_state.variant_id == v["id"] else "secondary"):
            st.session_state.variant_id = v["id"]
            st.rerun()

    st.markdown('<p class="subhead" style="margin-top:12px">Edge Cases</p>', unsafe_allow_html=True)
    for v in EDGE_CASES:
        if st.button(v["label"], key=f"v_{v['id']}",
                     use_container_width=True,
                     type="primary" if st.session_state.variant_id == v["id"] else "secondary"):
            st.session_state.variant_id = v["id"]
            st.rerun()

    # Persona data
    selected_variant = get_variant(st.session_state.variant_id)
    st.divider()
    st.markdown("**Persona Data**")
    st.caption(selected_variant["persona"])

    data = selected_variant["data"]
    rows = [(k, v if v else "*(empty)*") for k, v in data.items()
            if not k.startswith("@@marriott")]
    if rows:
        import pandas as pd
        df = pd.DataFrame(rows, columns=["Field", "Sample Value"])
        st.dataframe(df, hide_index=True, use_container_width=True, height=220)


# ── Panel 3: Email Preview ───────────────────────────────────────────────────
with p_preview:
    st.markdown("#### Email Preview")

    variant_data  = get_variant(st.session_state.variant_id)["data"]
    resolved_html = resolve_tokens(package.compiled_html, variant_data)
    raw_token_html = get_raw_tokens_html(package.compiled_html)

    # Subject / preheader resolved
    resolved_subject    = resolve_tokens(content.subject_line, variant_data)
    resolved_preheader  = resolve_tokens(content.preheader, variant_data)

    st.markdown(f"**SUBJECT** &nbsp; {resolved_subject}")
    st.markdown(f"**PREHEADER** &nbsp; {resolved_preheader}")
    if "@@" in package.compiled_html or "{{" in package.compiled_html:
        st.caption("`@@marriottDeliveryPersonalizedHeader@@`")

    tab_sim, tab_raw, tab_angles, tab_workflow = st.tabs([
        "Simulated Preview", "Raw Tokens (ACC)", "Angles & Jury", "Workflow"
    ])

    with tab_sim:
        components.html(resolved_html, height=550, scrolling=True)

    with tab_raw:
        st.caption("Tokens highlighted: `{{handlebars}}` in yellow · `@@ACC tokens@@` in orange")
        components.html(raw_token_html, height=550, scrolling=True)

    with tab_angles:
        for a in package.brief.__class__.__mro__:
            pass  # just need angles from jury — stored on package
        # Re-surface angles from content strategist via brief metadata
        st.markdown(f"**Winning Angle: [{package.selected_angle.name}]**")
        st.markdown(f"*{package.selected_angle.hook}*")
        st.markdown(f"{package.selected_angle.rationale}")
        st.markdown(f"Expected lift: `{package.selected_angle.expected_lift}`")
        st.divider()
        st.markdown("**Jury Summary**")
        wt2 = gate.get("workflow_track", {})
        ct2 = gate.get("content_track", {})
        st.markdown(f"- Workflow lint: {'PASS' if wt2.get('lint_passed') else 'FAIL'} | Score: {wt2.get('critic_score',0)}/100")
        st.markdown(f"- Content lint: {'PASS' if ct2.get('lint_passed') else 'FAIL'} | Score: {ct2.get('critic_score',0)}/100")
        if gate.get("blocking_issues"):
            st.warning("Blocking issues:\n" + "\n".join(f"- {i}" for i in gate["blocking_issues"]))

    with tab_workflow:
        st.markdown(f"**`{workflow.workflow_id}`** — {workflow.description}")
        st.markdown(f"Entry: `{workflow.entry_signal}` &nbsp;|&nbsp; Exit: `{workflow.exit_signal}`")
        st.divider()
        for s in workflow.steps:
            icon = {"query":"🔍","delivery":"📧","wait":"⏱️","enrichment":"🔗","split":"🔀","end":"🏁"}.get(s.step_type, "•")
            wait = f" — wait {s.wait_days}d" if s.wait_days else ""
            ch   = f" — `{s.channel}`" if s.step_type == "delivery" else ""
            st.markdown(f"{icon} **[{s.step_type}]** {s.label}{wait}{ch}")
        st.divider()
        st.code(workflow.targeting_sql, language="sql")
