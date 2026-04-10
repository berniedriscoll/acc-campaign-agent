"""
Human-in-the-Loop (HITL) approval gate.
Presents the campaign package to a human reviewer and captures their decision.
Supports: interactive CLI, auto-approve (CI/test mode), and webhook callback (future).
"""

import datetime
import json
import sys
from models.campaign import CampaignPackage


def present_package(package: CampaignPackage) -> None:
    """Print a human-readable review summary."""
    wf = package.workflow
    ct = package.content
    gate = package.gate_report

    print("\n" + "=" * 70)
    print("  CAMPAIGN REVIEW — HUMAN APPROVAL REQUIRED")
    print("=" * 70)
    print(f"  Campaign:  {package.brief.raw.campaign_name}")
    print(f"  Brand:     {package.brief.raw.brand}")
    print(f"  Intent:    {package.brief.business_intent}")
    print(f"  Audience:  {package.brief.audience_description}")
    print(f"  Angle:     [{package.selected_angle.name}] — {package.selected_angle.hook}")
    print()
    print("  CONTENT PREVIEW")
    print(f"  Subject:   {ct.subject_line}")
    print(f"  Preheader: {ct.preheader}")
    print(f"  Modules:   {', '.join(m.module_type for m in ct.modules)}")
    print(f"  Words:     {ct.word_count}")
    print()
    print("  WORKFLOW PREVIEW")
    print(f"  ID:        {wf.workflow_id}")
    print(f"  Steps:     {len(wf.steps)}")
    for s in wf.steps:
        print(f"    -> [{s.step_type}] {s.label}")
    print()
    print("  GATE RESULTS")
    wt = gate.get("workflow_track", {})
    ct_gate = gate.get("content_track", {})
    print(f"  Workflow lint: {'PASS' if wt.get('lint_passed') else 'FAIL'}  "
          f"| Critic score: {wt.get('critic_score', 0)}/100")
    print(f"  Content lint:  {'PASS' if ct_gate.get('lint_passed') else 'FAIL'}  "
          f"| Critic score: {ct_gate.get('critic_score', 0)}/100")
    if gate.get("blocking_issues"):
        print()
        print("  BLOCKING ISSUES:")
        for issue in gate["blocking_issues"]:
            print(f"    ! {issue}")
    if gate.get("warnings"):
        print()
        print("  WARNINGS:")
        for w in gate["warnings"]:
            print(f"    ~ {w}")
    print()
    print("  Workflow critic feedback:")
    print(f"    {wf.critic_feedback}")
    print()
    print("  Content critic feedback:")
    print(f"    {ct.critic_feedback}")
    print("=" * 70)


def prompt_approval(package: CampaignPackage, auto_approve: bool = False) -> CampaignPackage:
    """
    Interactive HITL prompt.
    Returns the package with hitl_approved set.
    """
    present_package(package)

    if auto_approve:
        print("  [AUTO-APPROVE MODE] Approving automatically.")
        package.hitl_approved = True
        package.approved_by   = "auto"
        package.approved_at   = _now()
        return package

    if not package.gate_report.get("passed", False):
        print("\n  Gate did not pass. You may still approve with override.\n")

    while True:
        choice = input("  Approve this campaign? [y/n/notes]: ").strip().lower()
        if choice in ("y", "yes"):
            reviewer = input("  Your name / ID: ").strip() or "reviewer"
            package.hitl_approved = True
            package.approved_by   = reviewer
            package.approved_at   = _now()
            print(f"\n  Approved by {reviewer} at {package.approved_at}")
            break
        elif choice in ("n", "no"):
            notes = input("  Rejection reason (optional): ").strip()
            package.hitl_approved = False
            package.hitl_notes    = notes
            package.approved_at   = _now()
            print("\n  Campaign rejected. Pipeline will halt.")
            break
        elif choice == "notes":
            notes = input("  Add notes: ").strip()
            package.hitl_notes += f"\n{notes}"
        else:
            print("  Enter y (approve), n (reject), or 'notes' to add notes.")

    return package


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")
