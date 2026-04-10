"""
Content lint — deterministic rule enforcement for CampaignContent objects.
No LLM involvement.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import CONTENT_RULES
from models.content import CampaignContent


def lint_content(content: CampaignContent) -> dict:
    """
    Returns:
        {
            "passed": bool,
            "issues": [str, ...],
            "warnings": [str, ...],
        }
    """
    issues = []
    warnings = []
    rules = CONTENT_RULES

    # Subject line
    if not content.subject_line:
        issues.append("subject_line is empty.")
    elif len(content.subject_line) > rules["subject_max_chars"]:
        issues.append(
            f"subject_line is {len(content.subject_line)} chars; "
            f"max is {rules['subject_max_chars']}."
        )

    # Preheader
    if not content.preheader:
        warnings.append("preheader is empty.")
    elif len(content.preheader) > rules["preheader_max_chars"]:
        issues.append(
            f"preheader is {len(content.preheader)} chars; "
            f"max is {rules['preheader_max_chars']}."
        )

    # Module count
    module_count = len(content.modules)
    if module_count < rules["min_modules"]:
        issues.append(
            f"Content has {module_count} modules; minimum is {rules['min_modules']}."
        )

    # Required modules
    module_types = [m.module_type for m in content.modules]
    for req in rules["required_modules"]:
        if req not in module_types:
            issues.append(f"Missing required module type: '{req}'.")

    # CTA label length
    for m in content.modules:
        if m.module_type == "cta" and m.cta_label:
            if len(m.cta_label) > rules["cta_max_chars"]:
                issues.append(
                    f"CTA label '{m.cta_label}' is {len(m.cta_label)} chars; "
                    f"max is {rules['cta_max_chars']}."
                )

    # Word count
    if content.word_count > rules["max_word_count"]:
        warnings.append(
            f"Word count {content.word_count} exceeds recommended max of {rules['max_word_count']}."
        )

    # Required personalization tokens
    all_copy = " ".join(
        f"{m.headline} {m.body_copy}" for m in content.modules
    ) + f" {content.subject_line}"
    for token in rules["required_tokens"]:
        if token not in all_copy:
            issues.append(f"Required personalization token missing: {token}")

    passed = len(issues) == 0
    return {"passed": passed, "issues": issues, "warnings": warnings}


def compute_word_count(content: CampaignContent) -> int:
    text = f"{content.subject_line} {content.preheader} " + " ".join(
        f"{m.headline} {m.body_copy} {m.cta_label}" for m in content.modules
    )
    return len(text.split())


def apply_lint(content: CampaignContent) -> CampaignContent:
    """Mutates content in-place with lint results."""
    content.word_count = compute_word_count(content)
    result = lint_content(content)
    content.lint_passed = result["passed"]
    content.lint_issues = result["issues"] + result["warnings"]
    return content
