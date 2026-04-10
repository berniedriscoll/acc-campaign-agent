"""
Targeting contract validation — deterministic truth enforcement.
Checks that the brief's signals are feasible given available data fields.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import TARGETING_SIGNALS, REQUIRED_SIGNALS
from .retrieval import load_profiles


class ContractViolation(Exception):
    pass


def validate_signals(signals: list, available_fields: list = None) -> dict:
    """
    Returns:
        {
            "passed": bool,
            "valid_signals": [...],
            "unknown_signals": [...],
            "missing_fields": [...],
            "enforced_signals": [...],
        }
    """
    if available_fields is None:
        profiles = load_profiles(limit=1)
        available_fields = list(profiles.columns) if not profiles.empty else []

    available_fields_upper = [f.upper() for f in available_fields]
    # If no profile data is available, skip field-presence checks (demo / dev mode)
    skip_field_check = len(available_fields_upper) == 0

    valid, unknown, missing = [], [], []

    for sig in signals:
        if sig not in TARGETING_SIGNALS:
            unknown.append(sig)
            continue
        field = TARGETING_SIGNALS[sig]["field"]
        if not skip_field_check and field.upper() not in available_fields_upper:
            missing.append({"signal": sig, "field": field})
        else:
            valid.append(sig)

    # Always enforce required signals
    enforced = []
    for sig in REQUIRED_SIGNALS:
        if sig not in valid and sig not in signals:
            enforced.append(sig)

    return {
        "passed":           len(unknown) == 0 and len(missing) == 0,
        "valid_signals":    valid,
        "unknown_signals":  unknown,
        "missing_fields":   missing,
        "enforced_signals": enforced,
        "all_signals":      list(set(valid + enforced)),
    }


def build_targeting_sql(signals: list, geo: str = None, property_code: str = None) -> str:
    """
    Build a WHERE clause from validated signals.
    Deterministic — no LLM involved.
    """
    clauses = []

    for sig in signals:
        if sig not in TARGETING_SIGNALS:
            continue
        cfg = TARGETING_SIGNALS[sig]
        field = cfg["field"]
        condition = cfg["condition"]
        if "{value}" in condition:
            value = geo or property_code or "UNKNOWN"
            condition = condition.replace("{value}", value)
        clauses.append(f"{field} {condition}")

    if not clauses:
        return "1=1"

    return "\nAND ".join(clauses)


def assert_contract(signals: list, available_fields: list = None):
    """Raise ContractViolation if the contract fails hard."""
    result = validate_signals(signals, available_fields)
    if result["unknown_signals"]:
        raise ContractViolation(
            f"Unknown signals: {result['unknown_signals']}. "
            f"Valid options: {list(TARGETING_SIGNALS.keys())}"
        )
    if result["missing_fields"]:
        raise ContractViolation(
            f"Required data fields not available: {result['missing_fields']}"
        )
    return result
