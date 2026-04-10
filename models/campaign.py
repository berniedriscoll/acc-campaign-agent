from dataclasses import dataclass, field
from typing import Optional
from .brief import StructuredBrief
from .workflow import AccWorkflow
from .content import CampaignContent


@dataclass
class MessagingAngle:
    name: str
    hook: str           # one-sentence positioning
    rationale: str
    expected_lift: str  # e.g. "+12% open rate"


@dataclass
class CampaignPackage:
    """Final compiled campaign, ready for ACC execution."""
    campaign_id: str
    brief: StructuredBrief
    selected_angle: MessagingAngle
    workflow: AccWorkflow
    content: CampaignContent

    # Gate results
    gate_passed: bool = False
    gate_report: dict = field(default_factory=dict)

    # HITL
    hitl_approved: bool = False
    hitl_notes: str = ""
    approved_by: str = ""
    approved_at: str = ""

    # Compile
    compiled_xml: str = ""          # ACC workflow XML
    compiled_html: str = ""         # Email HTML
    output_path: str = ""
    errors: list = field(default_factory=list)
