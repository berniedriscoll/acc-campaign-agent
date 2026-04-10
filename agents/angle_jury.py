"""
Angle Jury — 3 parallel voters select the best messaging angle.
Majority vote wins. Tie broken by highest avg confidence.
"""

import concurrent.futures
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.brief import StructuredBrief
from models.campaign import MessagingAngle
from .base import call_llm_json

VOTER_PERSONAS = [
    {
        "id": "brand_guardian",
        "description": "Brand & tone guardian. Prioritizes on-brand messaging, luxury positioning, and audience fit.",
    },
    {
        "id": "data_analyst",
        "description": "Data-driven analyst. Prioritizes predicted lift, engagement signals, and measurable impact.",
    },
    {
        "id": "customer_advocate",
        "description": "Customer advocate. Prioritizes relevance to the member's journey stage and emotional resonance.",
    },
]

SYSTEM_PROMPT = """You are a campaign jury voter for Marriott Bonvoy.
Your persona: {persona_description}

You will review a list of messaging angles and vote for the single best one.
Consider: relevance to brief, on-brand fit, predicted performance, and distinctiveness.

Return JSON:
{
  "vote": "exact angle name you choose",
  "confidence": 0.0 to 1.0,
  "reasoning": "1-2 sentences explaining your vote"
}
"""


def _cast_vote(voter: dict, brief: StructuredBrief, angles: list[MessagingAngle]) -> dict:
    system = SYSTEM_PROMPT.replace("{persona_description}", voter["description"])

    angles_text = "\n".join(
        f"{i+1}. [{a.name}]\n   Hook: {a.hook}\n   Rationale: {a.rationale}\n   Expected lift: {a.expected_lift}"
        for i, a in enumerate(angles)
    )

    user = f"""Campaign Brief Summary:
Intent: {brief.business_intent}
Audience: {brief.audience_description}
Tone: {brief.tone}

Candidate Angles:
{angles_text}

Cast your vote now."""

    result = call_llm_json(system, user)
    result["voter_id"] = voter["id"]
    return result


def run(brief: StructuredBrief, angles: list[MessagingAngle]) -> dict:
    """
    Returns:
        {
            "winning_angle": MessagingAngle,
            "vote_tally": {angle_name: count},
            "votes": [list of individual vote dicts],
            "jury_summary": str,
        }
    """
    votes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(_cast_vote, voter, brief, angles): voter
            for voter in VOTER_PERSONAS
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                votes.append(future.result())
            except Exception as e:
                votes.append({"vote": None, "confidence": 0.0, "reasoning": str(e)})

    # Tally votes
    tally = {}
    for v in votes:
        name = v.get("vote")
        if name:
            tally[name] = tally.get(name, 0) + 1

    # Winner by majority; tie-break by avg confidence
    if not tally:
        return {
            "winning_angle": angles[0],
            "vote_tally": tally,
            "votes": votes,
            "jury_summary": "No valid votes cast; defaulting to first angle.",
        }

    max_count = max(tally.values())
    candidates = [name for name, count in tally.items() if count == max_count]

    if len(candidates) == 1:
        winner_name = candidates[0]
    else:
        # Tie-break: highest average confidence among tied candidates
        avg_conf = {}
        for cand in candidates:
            cand_votes = [v["confidence"] for v in votes if v.get("vote") == cand]
            avg_conf[cand] = sum(cand_votes) / len(cand_votes) if cand_votes else 0
        winner_name = max(avg_conf, key=avg_conf.get)

    # Find the angle object
    angle_map = {a.name: a for a in angles}
    winning_angle = angle_map.get(winner_name, angles[0])

    summary_lines = [f"{v['voter_id']}: '{v.get('vote')}' (conf {v.get('confidence', 0):.2f}) — {v.get('reasoning', '')}" for v in votes]
    jury_summary = f"Winner: {winner_name} ({tally.get(winner_name, 0)}/3 votes)\n" + "\n".join(summary_lines)

    return {
        "winning_angle": winning_angle,
        "vote_tally":    tally,
        "votes":         votes,
        "jury_summary":  jury_summary,
    }
