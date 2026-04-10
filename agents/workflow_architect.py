"""
Workflow Architect — designs the ACC workflow for the campaign.
Runs in parallel with Content Author.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.brief import StructuredBrief
from models.campaign import MessagingAngle
from models.workflow import AccWorkflow, WorkflowStep
from config import WORKFLOW_RULES, TARGETING_SIGNALS
from .base import call_llm_json

SYSTEM_PROMPT_TMPL = """You are an Adobe Campaign Classic (ACC) workflow architect.
Design an ACC campaign workflow based on the brief and targeting strategy provided.

Rules:
- Use only these step types: query, enrichment, split, delivery, wait, end
- Required step types: query, delivery, end
- Min steps: {min_steps}, Max steps: {max_steps}
- Step IDs must be unique strings like "step_01", "step_02"
- Delivery steps must specify a channel

Return JSON:
{{
  "workflow_id": "wf_<campaign_slug>",
  "description": "one sentence describing what this workflow does",
  "entry_signal": "signal name that triggers entry",
  "exit_signal": "signal that marks workflow completion",
  "estimated_audience_size": 0,
  "steps": [
    {{
      "step_id": "step_01",
      "step_type": "query",
      "label": "human-readable label",
      "condition": null,
      "wait_days": 0,
      "channel": null,
      "targeting_filter": "description of filter",
      "notes": ""
    }}
  ]
}}
"""


def run(brief: StructuredBrief, angle: MessagingAngle) -> AccWorkflow:
    raw = brief.raw
    system = SYSTEM_PROMPT_TMPL.format(
        min_steps=WORKFLOW_RULES["min_steps"],
        max_steps=WORKFLOW_RULES["max_steps"],
    )

    signal_details = "\n".join(
        f"  - {sig}: {TARGETING_SIGNALS[sig]['field']} {TARGETING_SIGNALS[sig]['condition']}"
        for sig in brief.targeting_signals
        if sig in TARGETING_SIGNALS
    )

    user = f"""Campaign Brief:
Intent: {brief.business_intent}
Audience: {brief.audience_description}
Signals to use:
{signal_details}
Constraints: {brief.constraints}
Priority tier: {brief.priority_tier}
Channel: {raw.channel}

Selected Angle: [{angle.name}]
Hook: {angle.hook}

Property: {raw.property_name}, {raw.property_location}
Event: {raw.event_name} — {raw.event_date}
Offer: {raw.offer_description} (expires {raw.offer_expiry})

Design the ACC workflow now."""

    parsed = call_llm_json(system, user)

    steps = []
    for s in parsed.get("steps", []):
        steps.append(WorkflowStep(
            step_id=s.get("step_id", ""),
            step_type=s.get("step_type", ""),
            label=s.get("label", ""),
            condition=s.get("condition"),
            wait_days=int(s.get("wait_days", 0)),
            channel=s.get("channel", "") or "",
            targeting_filter=s.get("targeting_filter", ""),
            notes=s.get("notes", ""),
        ))

    return AccWorkflow(
        workflow_id=parsed.get("workflow_id", f"wf_{raw.campaign_name.lower().replace(' ','_')}"),
        campaign_name=raw.campaign_name,
        steps=steps,
        entry_signal=parsed.get("entry_signal", ""),
        exit_signal=parsed.get("exit_signal", ""),
        estimated_audience_size=int(parsed.get("estimated_audience_size", 0)),
        description=parsed.get("description", ""),
    )
