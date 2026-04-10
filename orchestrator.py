"""
ACC Campaign Agent — Orchestrator

Full pipeline:
  Brief Strategist
    → Python: Retrieval + Contract
      → Content Strategist (angles)
        → Angle Jury (3 parallel votes)
          → [PARALLEL]
             Workflow Architect → Workflow Lint → Workflow Critic
             Content Author     → Content Lint  → Content Critic
          → Gate Aggregator
            → HITL Approval
              → Compiler + Validator
"""

import concurrent.futures
import uuid
import logging

from models.brief import CampaignBrief
from models.campaign import CampaignPackage

import agents.brief_strategist  as brief_strategist
import agents.content_strategist as content_strategist
import agents.angle_jury         as angle_jury
import agents.workflow_architect as workflow_architect
import agents.content_author     as content_author
import agents.workflow_critic    as workflow_critic
import agents.content_critic     as content_critic

from python.retrieval      import get_audience_context
from python.contract       import validate_signals, build_targeting_sql
from python.workflow_lint  import apply_lint as workflow_lint
from python.content_lint   import apply_lint as content_lint
from python.gate_aggregator import apply_gate
from python.compiler       import compile_and_save

from hitl.approval import prompt_approval

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def run(
    brief: CampaignBrief,
    auto_approve: bool = False,
    n_angles: int = 4,
) -> CampaignPackage:
    """
    Execute the full pipeline. Returns the compiled CampaignPackage.
    Raises if gate fails and is not overridden by HITL.
    """
    campaign_id = f"camp_{uuid.uuid4().hex[:8]}"
    logger.info(f"[{campaign_id}] Pipeline start: {brief.campaign_name}")

    # ─────────────────────────────────────────────────────
    # Stage 1: Brief Strategist
    # ─────────────────────────────────────────────────────
    logger.info("Stage 1: Brief Strategist")
    structured = brief_strategist.run(brief)
    logger.info(f"  Intent: {structured.business_intent}")
    logger.info(f"  Signals: {structured.targeting_signals}")

    # ─────────────────────────────────────────────────────
    # Stage 2: Python — Retrieval + Contract validation
    # ─────────────────────────────────────────────────────
    logger.info("Stage 2: Retrieval + Contract")
    audience_ctx = get_audience_context(structured)
    contract = validate_signals(
        structured.targeting_signals,
        available_fields=audience_ctx.get("available_fields", []),
    )
    if contract["unknown_signals"]:
        # Hard error: agent hallucinated a signal name — remove unknowns only
        logger.warning(f"  Unknown signals removed: {contract['unknown_signals']}")
        structured.targeting_signals = contract["all_signals"]
    elif not contract["passed"]:
        # Field-name mismatch (data schema differs) — warn but keep signals
        logger.warning(f"  Contract field mismatch (env/schema): {contract['missing_fields']}")
        logger.warning("  Keeping signals — data schema may differ from ACC target schema.")

    # Build targeting SQL
    targeting_sql = build_targeting_sql(
        structured.targeting_signals,
        geo=brief.property_location,
    )
    logger.info(f"  Targeting SQL built ({len(targeting_sql)} chars)")

    # ─────────────────────────────────────────────────────
    # Stage 3: Content Strategist → angles
    # ─────────────────────────────────────────────────────
    logger.info("Stage 3: Content Strategist")
    angles = content_strategist.run(structured, n_angles=n_angles)
    logger.info(f"  Generated {len(angles)} angles: {[a.name for a in angles]}")

    # ─────────────────────────────────────────────────────
    # Stage 4: Angle Jury (3 parallel votes)
    # ─────────────────────────────────────────────────────
    logger.info("Stage 4: Angle Jury")
    jury_result = angle_jury.run(structured, angles)
    winning_angle = jury_result["winning_angle"]
    logger.info(f"  Winning angle: [{winning_angle.name}]")
    logger.info(f"  Tally: {jury_result['vote_tally']}")

    # ─────────────────────────────────────────────────────
    # Stage 5: Parallel — Workflow Architect + Content Author
    # ─────────────────────────────────────────────────────
    logger.info("Stage 5: Parallel — Workflow Architect + Content Author")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        wf_future = executor.submit(workflow_architect.run, structured, winning_angle)
        ct_future = executor.submit(content_author.run,     structured, winning_angle)
        workflow = wf_future.result()
        content  = ct_future.result()

    workflow.targeting_sql = targeting_sql
    logger.info(f"  Workflow: {workflow.workflow_id} ({len(workflow.steps)} steps)")
    logger.info(f"  Content: subject='{content.subject_line}'")

    # ─────────────────────────────────────────────────────
    # Stage 6: Lint (both tracks)
    # ─────────────────────────────────────────────────────
    logger.info("Stage 6: Lint")
    workflow = workflow_lint(workflow)
    content  = content_lint(content)
    logger.info(f"  Workflow lint: {'PASS' if workflow.lint_passed else 'FAIL'}")
    logger.info(f"  Content lint:  {'PASS' if content.lint_passed else 'FAIL'}")

    # ─────────────────────────────────────────────────────
    # Stage 7: Parallel — Critics
    # ─────────────────────────────────────────────────────
    logger.info("Stage 7: Parallel — Critics")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        wf_crit_f = executor.submit(workflow_critic.run, structured, workflow)
        ct_crit_f = executor.submit(content_critic.run,  structured, winning_angle, content)
        workflow = wf_crit_f.result()
        content  = ct_crit_f.result()

    logger.info(f"  Workflow critic: {workflow.critic_score}/100")
    logger.info(f"  Content critic:  {content.critic_score}/100")

    # ─────────────────────────────────────────────────────
    # Stage 8: Gate Aggregator
    # ─────────────────────────────────────────────────────
    logger.info("Stage 8: Gate Aggregator")
    package = CampaignPackage(
        campaign_id=campaign_id,
        brief=structured,
        selected_angle=winning_angle,
        workflow=workflow,
        content=content,
    )
    package = apply_gate(package)
    logger.info(f"  Gate: {'PASSED' if package.gate_passed else 'FAILED'}")
    if package.gate_report.get("blocking_issues"):
        for issue in package.gate_report["blocking_issues"]:
            logger.warning(f"  ! {issue}")

    # ─────────────────────────────────────────────────────
    # Stage 9: HITL Approval
    # ─────────────────────────────────────────────────────
    logger.info("Stage 9: HITL Approval")
    package = prompt_approval(package, auto_approve=auto_approve)

    if not package.hitl_approved:
        logger.warning("Campaign rejected by reviewer. Pipeline halted.")
        return package

    # ─────────────────────────────────────────────────────
    # Stage 10: Compile + Validate
    # ─────────────────────────────────────────────────────
    logger.info("Stage 10: Compile + Validate")
    package = compile_and_save(package)
    logger.info(f"  Output: {package.output_path}")
    logger.info(f"[{campaign_id}] Pipeline complete.")

    return package
