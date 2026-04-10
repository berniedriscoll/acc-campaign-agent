"""
Workflow Critic — QA pass on the AccWorkflow after lint.
Scores and provides actionable feedback.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.brief import StructuredBrief
from models.workflow import AccWorkflow
from config import GATE_THRESHOLDS
from .base import call_llm_json

SYSTEM_PROMPT = """You are a senior ACC campaign QA specialist reviewing a workflow design.
Evaluate the workflow against the campaign brief.

Score the workflow from 0–100 across these dimensions:
- Targeting accuracy (does it reach the right audience?)
- Step logic (is the flow sensible and complete?)
- Channel appropriateness
- Risk / compliance (any suppression or frequency concerns?)
- Brief alignment (does it deliver on the campaign intent?)

Return JSON:
{{
  "score": 0,
  "pass": true,
  "strengths": ["..."],
  "issues": ["..."],
  "feedback": "2-3 sentences of actionable feedback"
}}

Pass threshold: {threshold}/100
"""


def run(brief: StructuredBrief, workflow: AccWorkflow) -> AccWorkflow:
    system = SYSTEM_PROMPT.format(
        threshold=GATE_THRESHOLDS["min_workflow_critic_score"]
    )

    steps_desc = "\n".join(
        f"  {s.step_id} [{s.step_type}]: {s.label} | channel={s.channel} | wait={s.wait_days}d | condition={s.condition}"
        for s in workflow.steps
    )

    user = f"""Campaign Brief:
Intent: {brief.business_intent}
Audience: {brief.audience_description}
Signals: {brief.targeting_signals}
Constraints: {brief.constraints}

Workflow: {workflow.workflow_id}
Description: {workflow.description}
Entry signal: {workflow.entry_signal}
Targeting SQL:
  {workflow.targeting_sql}

Steps:
{steps_desc}

Lint passed: {workflow.lint_passed}
Lint issues: {workflow.lint_issues}

Evaluate this workflow now."""

    result = call_llm_json(system, user)

    workflow.critic_score    = int(result.get("score", 0))
    workflow.critic_feedback = result.get("feedback", "")

    # Append critic issues to lint_issues for visibility
    critic_issues = result.get("issues", [])
    if critic_issues:
        workflow.lint_issues.extend([f"[critic] {i}" for i in critic_issues])

    return workflow
