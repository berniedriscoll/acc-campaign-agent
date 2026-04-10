"""
Workflow lint — deterministic schema validation for AccWorkflow objects.
No LLM involvement.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import WORKFLOW_RULES
from models.workflow import AccWorkflow, WorkflowStep


def lint_workflow(workflow: AccWorkflow) -> dict:
    """
    Returns:
        {
            "passed": bool,
            "issues": [str, ...],
            "warnings": [str, ...],
        }
    """
    issues = []
    warnings = []
    rules = WORKFLOW_RULES

    steps = workflow.steps or []
    step_count = len(steps)

    # Step count
    if step_count < rules["min_steps"]:
        issues.append(
            f"Workflow has {step_count} steps; minimum is {rules['min_steps']}."
        )
    if step_count > rules["max_steps"]:
        issues.append(
            f"Workflow has {step_count} steps; maximum is {rules['max_steps']}."
        )

    # Required step types
    step_types = [s.step_type for s in steps]
    for required in rules["required_step_types"]:
        if required not in step_types:
            issues.append(f"Missing required step type: '{required}'.")

    # Unknown step types
    for s in steps:
        if s.step_type not in rules["allowed_step_types"]:
            issues.append(
                f"Step '{s.step_id}' has unknown type '{s.step_type}'. "
                f"Allowed: {rules['allowed_step_types']}"
            )

    # Step IDs must be unique
    ids = [s.step_id for s in steps]
    duplicates = [sid for sid in ids if ids.count(sid) > 1]
    if duplicates:
        issues.append(f"Duplicate step IDs: {list(set(duplicates))}.")

    # Targeting SQL present
    if not workflow.targeting_sql or workflow.targeting_sql.strip() == "":
        warnings.append("No targeting SQL defined. Audience will be unconstrained.")

    # Entry signal
    if not workflow.entry_signal:
        warnings.append("No entry_signal defined.")

    # Delivery step must have a channel
    for s in steps:
        if s.step_type == "delivery" and not s.channel:
            issues.append(f"Delivery step '{s.step_id}' has no channel defined.")

    passed = len(issues) == 0
    return {"passed": passed, "issues": issues, "warnings": warnings}


def apply_lint(workflow: AccWorkflow) -> AccWorkflow:
    """Mutates workflow in-place with lint results."""
    result = lint_workflow(workflow)
    workflow.lint_passed = result["passed"]
    workflow.lint_issues = result["issues"] + result["warnings"]
    return workflow
