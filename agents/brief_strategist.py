"""
Brief Strategist — parses free-text brief, extracts structured intent.
Stage 1 of the pipeline.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.brief import CampaignBrief, StructuredBrief
from config import TARGETING_SIGNALS, BRAND_VOICE
from .base import call_llm_json

SYSTEM_PROMPT = """You are a senior campaign strategist for Marriott Bonvoy.
Your job is to parse a campaign brief and extract structured intent.

You must return a valid JSON object with these exact keys:
{
  "business_intent": "one sentence describing the business goal",
  "targeting_signals": ["signal1", "signal2"],
  "audience_description": "plain-english description of the target audience",
  "key_value_propositions": ["prop1", "prop2", "prop3"],
  "constraints": ["constraint1"],
  "tone": "one of: aspirational | urgent | warm | celebratory | reactivation",
  "priority_tier": 1 or 2 or 3,
  "feasibility_notes": "any data or targeting concerns"
}

Available targeting signals: {signals}
Priority tiers: 1=urgent/event-driven, 2=standard, 3=nurture/long-cycle
"""


def run(brief: CampaignBrief) -> StructuredBrief:
    signal_list = ", ".join(TARGETING_SIGNALS.keys())
    brand_ctx = BRAND_VOICE.get(brief.brand, {})

    system = SYSTEM_PROMPT.replace("{signals}", signal_list)

    user = f"""Campaign Brief:
---
{brief.raw_text}
---
Brand: {brief.brand}
Property: {brief.property_name} ({brief.property_location})
Event: {brief.event_name} on {brief.event_date}
Offer: {brief.offer_description} (expires {brief.offer_expiry})
Channel: {brief.channel}
Segment hint: {brief.target_segment}
Objective: {brief.objective}
Brand voice: {brand_ctx.get('tone', 'aspirational')}
Avoid: {brand_ctx.get('avoid', [])}

Extract the structured brief now."""

    parsed = call_llm_json(system, user)

    return StructuredBrief(
        raw=brief,
        business_intent=parsed.get("business_intent", ""),
        targeting_signals=parsed.get("targeting_signals", []),
        audience_description=parsed.get("audience_description", ""),
        key_value_propositions=parsed.get("key_value_propositions", []),
        constraints=parsed.get("constraints", []),
        tone=parsed.get("tone", "aspirational"),
        priority_tier=int(parsed.get("priority_tier", 2)),
        feasibility_notes=parsed.get("feasibility_notes", ""),
    )
