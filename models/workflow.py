from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WorkflowStep:
    step_id: str
    step_type: str          # query | enrichment | split | delivery | wait | end
    label: str
    condition: Optional[str] = None
    wait_days: int = 0
    channel: str = "email"
    targeting_filter: str = ""
    notes: str = ""


@dataclass
class AccWorkflow:
    """ACC workflow definition produced by Workflow Architect."""
    workflow_id: str
    campaign_name: str
    steps: list = field(default_factory=list)   # list of WorkflowStep
    targeting_sql: str = ""
    estimated_audience_size: int = 0
    entry_signal: str = ""
    exit_signal: str = ""
    description: str = ""
    lint_passed: bool = False
    lint_issues: list = field(default_factory=list)
    critic_score: int = 0             # 0–100
    critic_feedback: str = ""
