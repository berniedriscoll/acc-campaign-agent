"""
Content Strategist — generates 3–5 messaging angles from the structured brief.
Stage 2 of the pipeline.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.brief import StructuredBrief
from models.campaign import MessagingAngle
from config import BRAND_VOICE
from .base import call_llm_json

SYSTEM_PROMPT = """You are a messaging strategist for Marriott Bonvoy luxury hotel campaigns.
Your job is to generate 3–5 distinct messaging angles for a campaign.

Each angle must be meaningfully different — different emotion, hook, or audience lens.
Avoid overlap. Think: urgency vs aspiration vs social proof vs scarcity vs reward.

Return a JSON array of angle objects:
[
  {
    "name": "short angle name (3-4 words)",
    "hook": "one sentence — the central positioning idea",
    "rationale": "why this angle works for this audience and brief",
    "expected_lift": "estimated impact on open rate or engagement, e.g. +8% open rate"
  },
  ...
]
"""


def run(brief: StructuredBrief, n_angles: int = 4) -> list[MessagingAngle]:
    brand_ctx = BRAND_VOICE.get(brief.raw.brand, {})
    raw = brief.raw

    user = f"""Structured Brief:
Business intent: {brief.business_intent}
Audience: {brief.audience_description}
Key value props: {brief.key_value_propositions}
Tone: {brief.tone}
Priority: Tier {brief.priority_tier}
Property: {raw.property_name}, {raw.property_location}
Event: {raw.event_name} ({raw.event_date})
Offer: {raw.offer_description}

Brand voice: {brand_ctx.get('tone', 'aspirational')}
Prefer words like: {brand_ctx.get('prefer', [])}
Avoid: {brand_ctx.get('avoid', [])}

Generate {n_angles} distinct messaging angles."""

    parsed = call_llm_json(SYSTEM_PROMPT, user)

    angles = []
    for item in parsed:
        angles.append(MessagingAngle(
            name=item.get("name", "Unnamed"),
            hook=item.get("hook", ""),
            rationale=item.get("rationale", ""),
            expected_lift=item.get("expected_lift", ""),
        ))
    return angles
