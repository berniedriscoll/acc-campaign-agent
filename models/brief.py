from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CampaignBrief:
    """Raw brief submitted by a marketer."""
    raw_text: str
    campaign_name: str = ""
    brand: str = "Marriott Bonvoy"
    property_name: str = ""
    property_location: str = ""
    event_name: str = ""
    event_date: str = ""
    offer_description: str = ""
    offer_expiry: str = ""
    target_segment: str = ""          # e.g. "Gold Elite past guests"
    channel: str = "email"
    objective: str = ""               # e.g. "drive bookings", "re-engage lapsed"
    from_date: str = ""               # targeting window start
    to_date: str = ""                 # targeting window end
    metadata: dict = field(default_factory=dict)


@dataclass
class StructuredBrief:
    """Parsed + enriched brief produced by Brief Strategist."""
    raw: CampaignBrief
    business_intent: str = ""
    targeting_signals: list = field(default_factory=list)   # list of signal names
    audience_description: str = ""
    key_value_propositions: list = field(default_factory=list)
    constraints: list = field(default_factory=list)
    tone: str = "aspirational"
    priority_tier: int = 2            # 1=urgent, 2=standard, 3=nurture
    feasibility_notes: str = ""
