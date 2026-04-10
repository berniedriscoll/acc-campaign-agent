from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EmailModule:
    module_type: str        # hero | greeting | body | tile | cta | footer
    headline: str = ""
    body_copy: str = ""
    cta_label: str = ""
    cta_url: str = ""
    personalization_token: str = ""
    image_hint: str = ""    # description for creative team


@dataclass
class CampaignContent:
    """Email content package produced by Content Author."""
    angle_name: str
    subject_line: str
    preheader: str
    modules: list = field(default_factory=list)   # list of EmailModule
    tone: str = "aspirational"
    personalization_fields: list = field(default_factory=list)
    word_count: int = 0
    lint_passed: bool = False
    lint_issues: list = field(default_factory=list)
    critic_score: int = 0
    critic_feedback: str = ""
