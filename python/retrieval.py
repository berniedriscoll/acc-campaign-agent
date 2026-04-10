"""
Data retrieval layer — loads profile context and targeting data.
Deterministic. No LLM involvement.
"""

import os
import json
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"


def load_profiles(limit: int = None) -> pd.DataFrame:
    """Load member profiles from the central data directory."""
    candidates = [
        DATA_DIR / "profiles.csv",
        DATA_DIR / "members.csv",
        DATA_DIR / "6_next_best_action.csv",
    ]
    for path in candidates:
        if path.exists():
            df = pd.read_csv(path)
            return df.head(limit) if limit else df
    return pd.DataFrame()


def load_stay_history() -> pd.DataFrame:
    candidates = [
        DATA_DIR / "stay_history.csv",
        DATA_DIR / "stays.csv",
    ]
    for path in candidates:
        if path.exists():
            return pd.read_csv(path)
    return pd.DataFrame()


def load_reservations() -> pd.DataFrame:
    candidates = [
        DATA_DIR / "reservations.csv",
        DATA_DIR / "upcoming_stays.csv",
    ]
    for path in candidates:
        if path.exists():
            return pd.read_csv(path)
    return pd.DataFrame()


def load_suppression_list() -> pd.DataFrame:
    candidates = [
        DATA_DIR / "suppression_list.csv",
        Path(__file__).resolve().parents[2] / "output" / "suppression_list.csv",
    ]
    for path in candidates:
        if path.exists():
            return pd.read_csv(path)
    return pd.DataFrame(columns=["profile_id"])


def get_audience_context(brief) -> dict:
    """
    Build a context dict for LLM agents from a StructuredBrief.
    Returns counts and sample rows — never raw PII in prod.
    """
    profiles = load_profiles()
    stays = load_stay_history()
    context = {
        "total_profiles":       len(profiles),
        "has_stay_history":     not stays.empty,
        "available_fields":     list(profiles.columns) if not profiles.empty else [],
        "signals_detected":     brief.targeting_signals if hasattr(brief, "targeting_signals") else [],
    }

    # Audience size estimate per signal
    if not profiles.empty:
        signal_counts = {}
        for sig in context["signals_detected"]:
            if sig == "email_eligible" and "EMAIL_OPT_IN" in profiles.columns:
                signal_counts[sig] = int(profiles["EMAIL_OPT_IN"].sum())
            elif sig == "past_guest" and "STAY_COUNT" in profiles.columns:
                signal_counts[sig] = int((profiles["STAY_COUNT"] > 0).sum())
            elif sig == "app_download" and "HAS_APP" in profiles.columns:
                signal_counts[sig] = int(profiles["HAS_APP"].sum())
        context["estimated_counts"] = signal_counts

    return context


def get_property_context(property_name: str, location: str) -> dict:
    """Return structured property context for content generation."""
    return {
        "property_name": property_name,
        "location":      location,
        "amenities":     [],    # would pull from property API / data layer
        "room_types":    [],
        "avg_nightly":   None,
    }
