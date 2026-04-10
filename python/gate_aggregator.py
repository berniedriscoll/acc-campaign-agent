"""
Gate Aggregator — merges parallel workflow + content tracks.
Deterministic pass/fail. No LLM involvement.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import GATE_THRESHOLDS
from models.workflow import AccWorkflow
from models.content import CampaignContent
from models.campaign import CampaignPackage


def aggregate(workflow: AccWorkflow, content: CampaignContent) -> dict:
    """
    Evaluates both parallel tracks and returns a unified gate report.

    Returns:
        {
            "passed": bool,
            "workflow_track": { ... },
            "content_track": { ... },
            "blocking_issues": [str, ...],
            "warnings": [str, ...],
        }
    """
    thresholds = GATE_THRESHOLDS
    blocking = []
    warnings = []

    # --- Workflow track ---
    workflow_ok = workflow.lint_passed
    workflow_score_ok = workflow.critic_score >= thresholds["min_workflow_critic_score"]
    if not workflow_ok:
        blocking.append(f"Workflow lint FAILED: {workflow.lint_issues}")
    if not workflow_score_ok:
        blocking.append(
            f"Workflow critic score {workflow.critic_score} < "
            f"threshold {thresholds['min_workflow_critic_score']}. "
            f"Feedback: {workflow.critic_feedback}"
        )

    # --- Content track ---
    content_ok = content.lint_passed
    content_score_ok = content.critic_score >= thresholds["min_content_critic_score"]
    if not content_ok:
        blocking.append(f"Content lint FAILED: {content.lint_issues}")
    if not content_score_ok:
        blocking.append(
            f"Content critic score {content.critic_score} < "
            f"threshold {thresholds['min_content_critic_score']}. "
            f"Feedback: {content.critic_feedback}"
        )

    # Lint warnings (non-blocking)
    for issue in workflow.lint_issues:
        if not workflow.lint_passed and issue not in str(blocking):
            warnings.append(f"[workflow] {issue}")
    for issue in content.lint_issues:
        if not content.lint_passed and issue not in str(blocking):
            warnings.append(f"[content] {issue}")

    passed = len(blocking) == 0

    return {
        "passed": passed,
        "workflow_track": {
            "lint_passed":   workflow_ok,
            "critic_score":  workflow.critic_score,
            "score_passed":  workflow_score_ok,
            "issues":        workflow.lint_issues,
        },
        "content_track": {
            "lint_passed":  content_ok,
            "critic_score": content.critic_score,
            "score_passed": content_score_ok,
            "issues":       content.lint_issues,
        },
        "blocking_issues": blocking,
        "warnings":        warnings,
    }


def apply_gate(package: CampaignPackage) -> CampaignPackage:
    """Mutates package in-place with gate results."""
    report = aggregate(package.workflow, package.content)
    package.gate_passed = report["passed"]
    package.gate_report = report
    return package
