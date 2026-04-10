"""
Central configuration for the ACC Campaign Agent System.
All targeting signals, content rules, and cap definitions live here.
"""

# ---------------------------------------------------------------------------
# Signal-based targeting map
# Each signal maps to the ACC field that drives eligibility
# ---------------------------------------------------------------------------
TARGETING_SIGNALS = {
    "new_account":        {"field": "ACCOUNT_STATUS",  "condition": "= 'NEW'"},
    "app_download":       {"field": "HAS_APP",         "condition": "= 1"},
    "first_stay":         {"field": "FIRST_STAY_DATE", "condition": "IS NOT NULL"},
    "profile_complete":   {"field": "ADDRESS_PRESENT", "condition": "= 1"},
    "past_guest":         {"field": "STAY_COUNT",      "condition": "> 0"},
    "upcoming_res":       {"field": "NEXT_CHECKIN_DATE","condition": "IS NOT NULL"},
    "lapsed":             {"field": "LAST_STAY_DATE",  "condition": "< DATEADD(day, -365, GETDATE())"},
    "gold_elite":         {"field": "TIER",            "condition": "= 'GOLD'"},
    "platinum_elite":     {"field": "TIER",            "condition": "IN ('PLATINUM','TITANIUM','AMBASSADOR')"},
    "email_eligible":     {"field": "EMAIL_OPT_IN",    "condition": "= 1"},
    "geo_filter":         {"field": "HOME_MARKET",     "condition": "= '{value}'"},
    "clv_high":           {"field": "CLV_SEGMENT",     "condition": "= 'HIGH'"},
}

REQUIRED_SIGNALS = ["email_eligible"]   # always enforced

# ---------------------------------------------------------------------------
# Frequency cap rules (mirrors frequency_cap.py)
# ---------------------------------------------------------------------------
CAP_RULES = {
    "email": {"7d": 3,  "30d": 8},
    "sms":   {"7d": 2,  "30d": 5},
    "push":  {"7d": 5,  "30d": 15},
}

# ---------------------------------------------------------------------------
# Content rules
# ---------------------------------------------------------------------------
CONTENT_RULES = {
    "subject_max_chars":    60,
    "preheader_max_chars":  90,
    "cta_max_chars":        35,
    "min_modules":          3,         # hero + body + cta at minimum
    "required_modules":     ["hero", "cta"],
    "max_word_count":       350,
    "required_tokens":      [],        # e.g. ["{{first_name}}"] — add to enforce
}

# ---------------------------------------------------------------------------
# Workflow rules
# ---------------------------------------------------------------------------
WORKFLOW_RULES = {
    "required_step_types":  ["query", "delivery", "end"],
    "max_steps":            12,
    "min_steps":            3,
    "allowed_step_types":   ["query", "enrichment", "split", "delivery", "wait", "end"],
}

# ---------------------------------------------------------------------------
# Gate thresholds
# ---------------------------------------------------------------------------
GATE_THRESHOLDS = {
    "min_workflow_critic_score":  70,   # out of 100
    "min_content_critic_score":   70,
}

# ---------------------------------------------------------------------------
# LLM settings
# ---------------------------------------------------------------------------
LLM_MODEL = "claude-opus-4-6"
LLM_MAX_TOKENS = 4096

# ---------------------------------------------------------------------------
# Recovery campaign options
# ---------------------------------------------------------------------------
RECOVERY_OPTIONS = {
    "A": "past_guests",
    "B": "all_members",
    "C": "upcoming_reservations",
}

# ---------------------------------------------------------------------------
# Brand voice
# ---------------------------------------------------------------------------
BRAND_VOICE = {
    "Marriott Bonvoy": {
        "tone":      "aspirational, warm, rewarding",
        "avoid":     ["pushy", "salesy", "cheap", "discount"],
        "prefer":    ["exclusive", "curated", "earned", "experience", "points"],
        "sign_off":  "The Marriott Bonvoy Team",
    }
}
