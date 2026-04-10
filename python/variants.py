"""
Bonvoy member tier variants + token resolver.
Used by the Variant Preview panel to simulate how email renders
across different member profiles.
"""

# ---------------------------------------------------------------------------
# Variant definitions
# ---------------------------------------------------------------------------

COMMON_VARIANTS = [
    {
        "id": "member_points",
        "label": "Member — Has Points Balance",
        "category": "common",
        "persona": "A base-tier member with an active points balance. Tests the standard personalization path with firstName and points present.",
        "data": {
            "FirstName": "Carlos",
            "LastName": "Thornton",
            "Language": "ENG",
            "_RECIPIENT_SERVLEVEL_CODE": "M",
            "_RECIPIENT_SERVLEVEL_LABEL": "Member",
            "_RECIPIENT_TOTAL_POINT_BALANCE": "4200",
            "_RECIPIENT_EMAIL": "carlos.thornton@example.com",
            "@@ObloyaltyLevel@@": "M",
            "@@ObloyaltySummary@@": "4200",
            "@@marriottDeliveryPersonalizedHeader@@": "<!-- personalized header -->",
        },
    },
    {
        "id": "silver_moderate",
        "label": "Silver Elite — Moderate Points",
        "category": "common",
        "persona": "A Silver Elite member with a moderate points balance. Tests mid-tier messaging and the silver-specific content branch.",
        "data": {
            "FirstName": "Maria",
            "LastName": "Santos",
            "Language": "ENG",
            "_RECIPIENT_SERVLEVEL_CODE": "S",
            "_RECIPIENT_SERVLEVEL_LABEL": "Silver Elite",
            "_RECIPIENT_TOTAL_POINT_BALANCE": "12500",
            "_RECIPIENT_EMAIL": "maria.santos@example.com",
            "@@ObloyaltyLevel@@": "S",
            "@@ObloyaltySummary@@": "12500",
            "@@marriottDeliveryPersonalizedHeader@@": "<!-- personalized header -->",
        },
    },
    {
        "id": "gold_high",
        "label": "Gold Elite — High Points Balance",
        "category": "common",
        "persona": "A Gold Elite member with a high points balance. Primary target segment for this campaign — tests the core conversion path.",
        "data": {
            "FirstName": "James",
            "LastName": "Whitfield",
            "Language": "ENG",
            "_RECIPIENT_SERVLEVEL_CODE": "G",
            "_RECIPIENT_SERVLEVEL_LABEL": "Gold Elite",
            "_RECIPIENT_TOTAL_POINT_BALANCE": "38750",
            "_RECIPIENT_EMAIL": "james.whitfield@example.com",
            "@@ObloyaltyLevel@@": "G",
            "@@ObloyaltySummary@@": "38750",
            "@@marriottDeliveryPersonalizedHeader@@": "<!-- personalized header -->",
        },
    },
    {
        "id": "platinum_strong",
        "label": "Platinum Elite — Strong Points",
        "category": "common",
        "persona": "A Platinum Elite member with a strong points balance. Tests whether the luxury tone and offer resonates with high-frequency travelers.",
        "data": {
            "FirstName": "Sarah",
            "LastName": "Chen",
            "Language": "ENG",
            "_RECIPIENT_SERVLEVEL_CODE": "P",
            "_RECIPIENT_SERVLEVEL_LABEL": "Platinum Elite",
            "_RECIPIENT_TOTAL_POINT_BALANCE": "87200",
            "_RECIPIENT_EMAIL": "sarah.chen@example.com",
            "@@ObloyaltyLevel@@": "P",
            "@@ObloyaltySummary@@": "87200",
            "@@marriottDeliveryPersonalizedHeader@@": "<!-- personalized header -->",
        },
    },
    {
        "id": "titanium_no_points",
        "label": "Titanium Elite — No Points Data",
        "category": "common",
        "persona": "A Titanium Elite member whose TOTAL_POINT_BALANCE is not present (loyalty summary row exists but balance field is empty). Exercises the firstName-present branch but the points-balance-absent fallback in the conversion nudge. Realistic because some high-tier members may have recently redeemed all points or have incomplete loyalty summary data.",
        "data": {
            "FirstName": "Carlos",
            "LastName": "Thornton",
            "Language": "ENG",
            "_RECIPIENT_SERVLEVEL_CODE": "A",
            "_RECIPIENT_SERVLEVEL_LABEL": "Titanium Elite",
            "_RECIPIENT_TOTAL_POINT_BALANCE": "",
            "_RECIPIENT_EMAIL": "c.thornton@example.com",
            "@@ObloyaltyLevel@@": "A",
            "@@ObloyaltySummary@@": "",
            "@@marriottDeliveryPersonalizedHeader@@": "<!-- personalized header -->",
        },
    },
    {
        "id": "ambassador_premium",
        "label": "Ambassador Elite — Premium Points",
        "category": "common",
        "persona": "The highest Bonvoy tier. Tests premium messaging branch and whether ultra-high-value members receive appropriate VIP treatment in the copy.",
        "data": {
            "FirstName": "Victoria",
            "LastName": "Harrington",
            "Language": "ENG",
            "_RECIPIENT_SERVLEVEL_CODE": "PP",
            "_RECIPIENT_SERVLEVEL_LABEL": "Ambassador Elite",
            "_RECIPIENT_TOTAL_POINT_BALANCE": "245000",
            "_RECIPIENT_EMAIL": "v.harrington@example.com",
            "@@ObloyaltyLevel@@": "PP",
            "@@ObloyaltySummary@@": "245000",
            "@@marriottDeliveryPersonalizedHeader@@": "<!-- personalized header -->",
        },
    },
]

EDGE_CASES = [
    {
        "id": "no_first_name",
        "label": "Member — No First Name (Edge Case)",
        "category": "edge",
        "persona": "A member record where FirstName is missing. Tests the fallback greeting path — email should not render '{{first_name}}' as a raw token.",
        "data": {
            "FirstName": "",
            "LastName": "Williams",
            "Language": "ENG",
            "_RECIPIENT_SERVLEVEL_CODE": "M",
            "_RECIPIENT_SERVLEVEL_LABEL": "Member",
            "_RECIPIENT_TOTAL_POINT_BALANCE": "3100",
            "_RECIPIENT_EMAIL": "williams@example.com",
            "@@ObloyaltyLevel@@": "M",
            "@@ObloyaltySummary@@": "3100",
            "@@marriottDeliveryPersonalizedHeader@@": "<!-- personalized header -->",
        },
    },
    {
        "id": "no_name_no_points",
        "label": "Silver — No Name, No Points (Edge Case)",
        "category": "edge",
        "persona": "A Silver Elite member with neither FirstName nor points balance populated. Worst-case fallback test — both personalization branches should degrade gracefully.",
        "data": {
            "FirstName": "",
            "LastName": "",
            "Language": "ENG",
            "_RECIPIENT_SERVLEVEL_CODE": "S",
            "_RECIPIENT_SERVLEVEL_LABEL": "Silver Elite",
            "_RECIPIENT_TOTAL_POINT_BALANCE": "",
            "_RECIPIENT_EMAIL": "member@example.com",
            "@@ObloyaltyLevel@@": "S",
            "@@ObloyaltySummary@@": "",
            "@@marriottDeliveryPersonalizedHeader@@": "<!-- personalized header -->",
        },
    },
]

ALL_VARIANTS = COMMON_VARIANTS + EDGE_CASES


def get_variant(variant_id: str) -> dict:
    return next((v for v in ALL_VARIANTS if v["id"] == variant_id), COMMON_VARIANTS[2])


# ---------------------------------------------------------------------------
# Token resolver
# ---------------------------------------------------------------------------

TOKEN_MAP = {
    # Handlebars style
    "{{first_name}}":         lambda d: d.get("FirstName") or "Valued Member",
    "{{last_name}}":          lambda d: d.get("LastName") or "",
    "{{points_balance}}":     lambda d: _fmt_points(d.get("_RECIPIENT_TOTAL_POINT_BALANCE")),
    "{{tier}}":               lambda d: d.get("_RECIPIENT_SERVLEVEL_LABEL") or "Member",
    "{{bonvoy_number}}":      lambda d: "XXXXXXXX",  # masked in preview

    # ACC/Obloyalty style
    "@@ObloyaltyLevel@@":          lambda d: d.get("@@ObloyaltyLevel@@") or "M",
    "@@ObloyaltySummary@@":        lambda d: _fmt_points(d.get("@@ObloyaltySummary@@")),
    "@@marriottDeliveryPersonalizedHeader@@": lambda d: "",  # strip include tags in preview

    # ACC recipient fields
    "_RECIPIENT_TOTAL_POINT_BALANCE": lambda d: _fmt_points(d.get("_RECIPIENT_TOTAL_POINT_BALANCE")),
    "_RECIPIENT_SERVLEVEL_LABEL":     lambda d: d.get("_RECIPIENT_SERVLEVEL_LABEL") or "Member",
}

FALLBACKS = {
    "first_name":     "Valued Member",
    "points_balance": "your points",
    "tier":           "Member",
}


def _fmt_points(val) -> str:
    if not val:
        return "your points"
    try:
        return f"{int(val):,}"
    except (ValueError, TypeError):
        return str(val)


def resolve_tokens(html: str, variant_data: dict) -> str:
    """Replace all known tokens in html with variant values."""
    result = html
    for token, resolver in TOKEN_MAP.items():
        try:
            result = result.replace(token, resolver(variant_data))
        except Exception:
            pass
    # Fallback: strip any remaining {{ }} tokens gracefully
    import re
    def _fallback(m):
        key = m.group(1).strip()
        return FALLBACKS.get(key, f"[{key}]")
    result = re.sub(r'\{\{([^}]+)\}\}', _fallback, result)
    return result


def get_raw_tokens_html(html: str) -> str:
    """Highlight raw ACC tokens in HTML for the Raw Tokens tab."""
    import re
    highlighted = html
    # Highlight {{ }} tokens
    highlighted = re.sub(
        r'(\{\{[^}]+\}\})',
        r'<mark style="background:#fff176;color:#333;font-weight:bold">\1</mark>',
        highlighted,
    )
    # Highlight @@ @@ tokens
    highlighted = re.sub(
        r'(@@[^@]+@@)',
        r'<mark style="background:#ffe0b2;color:#333;font-weight:bold">\1</mark>',
        highlighted,
    )
    return highlighted
