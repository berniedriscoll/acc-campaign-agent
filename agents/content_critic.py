"""
Content Critic — QA pass on CampaignContent after lint.
Scores and provides actionable feedback.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.brief import StructuredBrief
from models.content import CampaignContent
from models.campaign import MessagingAngle
from config import GATE_THRESHOLDS, BRAND_VOICE
from .base import call_llm_json

SYSTEM_PROMPT = """You are a senior email content QA reviewer for a luxury hotel brand.
Evaluate the campaign content against the brief and brand standards.

Score from 0–100 across:
- Subject line effectiveness (curiosity, personalization, relevance)
- Brand voice alignment (luxury, aspirational, correct tone)
- Module flow (hero → body → CTA narrative arc)
- Personalization quality
- CTA clarity and urgency
- Brief alignment (does it deliver on the angle and intent?)

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


def run(brief: StructuredBrief, angle: MessagingAngle, content: CampaignContent) -> CampaignContent:
    system = SYSTEM_PROMPT.format(
        threshold=GATE_THRESHOLDS["min_content_critic_score"]
    )
    brand_ctx = BRAND_VOICE.get(brief.raw.brand, {})

    modules_desc = "\n".join(
        f"  [{m.module_type}] Headline: {m.headline} | Copy: {m.body_copy[:120]}... | CTA: {m.cta_label}"
        for m in content.modules
    )

    user = f"""Campaign Brief:
Intent: {brief.business_intent}
Audience: {brief.audience_description}
Tone: {brief.tone}
Brand voice: {brand_ctx.get('tone', 'aspirational')}
Avoid: {brand_ctx.get('avoid', [])}

Winning Angle: [{angle.name}] — {angle.hook}

Content:
Subject: {content.subject_line}
Preheader: {content.preheader}
Modules:
{modules_desc}

Personalization fields: {content.personalization_fields}
Word count: {content.word_count}
Lint passed: {content.lint_passed}
Lint issues: {content.lint_issues}

Evaluate this content now."""

    result = call_llm_json(system, user)

    content.critic_score    = int(result.get("score", 0))
    content.critic_feedback = result.get("feedback", "")

    critic_issues = result.get("issues", [])
    if critic_issues:
        content.lint_issues.extend([f"[critic] {i}" for i in critic_issues])

    return content
