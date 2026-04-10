"""
Base LLM agent — shared Claude API wrapper.
"""

import json
import anthropic
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import LLM_MODEL, LLM_MAX_TOKENS

_client = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    return _client


def call_llm(system: str, user: str, model: str = None, max_tokens: int = None) -> str:
    """Simple single-turn call. Returns the text content."""
    client = get_client()
    response = client.messages.create(
        model=model or LLM_MODEL,
        max_tokens=max_tokens or LLM_MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def call_llm_json(system: str, user: str, model: str = None, max_tokens: int = None) -> dict:
    """Call LLM and parse JSON response. Strips markdown fences if present."""
    raw = call_llm(system, user, model, max_tokens)
    # Strip markdown code fences
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text)
