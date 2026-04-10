"""
Content Author — writes the full email content package for the winning angle.
Runs in parallel with Workflow Architect.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.brief import StructuredBrief
from models.campaign import MessagingAngle
from models.content import CampaignContent, EmailModule
from config import BRAND_VOICE, CONTENT_RULES
from .base import call_llm_json

SYSTEM_PROMPT = """You are a luxury email copywriter for Marriott Bonvoy.
Write a complete email content package for the given campaign angle.

Tone: {tone}
Brand: {brand}
Prefer words like: {prefer}
Avoid: {avoid}

Required modules: hero, greeting (or body), cta. Add tile modules for key benefits.
Max subject: {subject_max} chars. Max preheader: {preheader_max} chars.

Return JSON:
{{
  "subject_line": "...",
  "preheader": "...",
  "personalization_fields": ["{{{{first_name}}}}", "..."],
  "modules": [
    {{
      "module_type": "hero|greeting|body|tile|cta",
      "headline": "...",
      "body_copy": "...",
      "cta_label": "... (for cta type only)",
      "cta_url": "%%campaign_url%% (for cta type)",
      "personalization_token": "{{{{first_name}}}} etc or empty",
      "image_hint": "description for creative team or empty"
    }}
  ]
}}
"""


def run(brief: StructuredBrief, angle: MessagingAngle) -> CampaignContent:
    raw = brief.raw
    brand_ctx = BRAND_VOICE.get(raw.brand, {})

    system = SYSTEM_PROMPT.format(
        tone=brief.tone,
        brand=raw.brand,
        prefer=brand_ctx.get("prefer", []),
        avoid=brand_ctx.get("avoid", []),
        subject_max=CONTENT_RULES["subject_max_chars"],
        preheader_max=CONTENT_RULES["preheader_max_chars"],
    )

    user = f"""Campaign:
Intent: {brief.business_intent}
Audience: {brief.audience_description}
Value props: {brief.key_value_propositions}

Selected Angle: [{angle.name}]
Hook: {angle.hook}
Rationale: {angle.rationale}

Property: {raw.property_name}, {raw.property_location}
Event: {raw.event_name} on {raw.event_date}
Offer: {raw.offer_description} (expires {raw.offer_expiry})

Write the complete email content package now."""

    parsed = call_llm_json(system, user)

    modules = []
    for m in parsed.get("modules", []):
        modules.append(EmailModule(
            module_type=m.get("module_type", "body"),
            headline=m.get("headline", ""),
            body_copy=m.get("body_copy", ""),
            cta_label=m.get("cta_label", ""),
            cta_url=m.get("cta_url", ""),
            personalization_token=m.get("personalization_token", ""),
            image_hint=m.get("image_hint", ""),
        ))

    return CampaignContent(
        angle_name=angle.name,
        subject_line=parsed.get("subject_line", ""),
        preheader=parsed.get("preheader", ""),
        modules=modules,
        tone=brief.tone,
        personalization_fields=parsed.get("personalization_fields", []),
    )
