"""
ACC Campaign Agent — CLI entry point

Usage:
  python run.py                          # interactive guided brief
  python run.py --brief brief.json       # load brief from JSON file
  python run.py --brief brief.json --auto-approve
  python run.py --demo                   # run a demo campaign (no API key needed for brief)

Example brief JSON:
{
  "campaign_name": "Vail Oktoberfest 2026",
  "brand": "Marriott Bonvoy",
  "property_name": "The Ritz-Carlton, Bachelor Gulch",
  "property_location": "Vail, Colorado",
  "event_name": "Vail Oktoberfest",
  "event_date": "2026-09-18",
  "offer_description": "Earn 8,100 bonus points on a 2-night stay",
  "offer_expiry": "2026-09-30",
  "target_segment": "Gold Elite past guests, Rocky Mountain region",
  "channel": "email",
  "objective": "drive bookings for Oktoberfest weekend",
  "raw_text": "We want to drive bookings for the Vail Oktoberfest weekend..."
}
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure parent directory is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from models.brief import CampaignBrief
import orchestrator


DEMO_BRIEF = CampaignBrief(
    campaign_name="Vail Oktoberfest 2026",
    brand="Marriott Bonvoy",
    property_name="The Ritz-Carlton, Bachelor Gulch",
    property_location="Vail, Colorado",
    event_name="Vail Oktoberfest",
    event_date="2026-09-18",
    offer_description="Earn 8,100 bonus points on a 2-night stay",
    offer_expiry="2026-09-30",
    target_segment="Gold Elite past guests, Rocky Mountain region",
    channel="email",
    objective="drive bookings for Oktoberfest weekend",
    raw_text=(
        "We want to re-engage Gold Elite members who have stayed in the Rocky Mountain "
        "region before. Vail Oktoberfest is a marquee fall event at The Ritz-Carlton, "
        "Bachelor Gulch. Offer: 8,100 bonus points on a 2-night stay. "
        "Email must feel exclusive and aspirational — tie the luxury of the property "
        "to the craft beer/alpine culture of the event. Expiry: Sept 30, 2026."
    ),
)


def load_brief_from_json(path: str) -> CampaignBrief:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CampaignBrief(**data)


def interactive_brief() -> CampaignBrief:
    print("\nACC Campaign Agent — New Campaign Brief")
    print("=" * 45)

    def ask(prompt, default=""):
        val = input(f"  {prompt} [{default}]: ").strip()
        return val if val else default

    name        = ask("Campaign name", "My Campaign")
    brand       = ask("Brand", "Marriott Bonvoy")
    property_n  = ask("Property name", "")
    location    = ask("Property location", "")
    event       = ask("Event name (optional)", "")
    event_date  = ask("Event date (YYYY-MM-DD, optional)", "")
    offer       = ask("Offer description", "")
    expiry      = ask("Offer expiry (YYYY-MM-DD)", "")
    segment     = ask("Target segment hint", "")
    channel     = ask("Channel", "email")
    objective   = ask("Campaign objective", "drive bookings")

    print("\n  Paste the full campaign brief (end with a blank line):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    raw_text = "\n".join(lines) or f"{name} — {objective}"

    return CampaignBrief(
        campaign_name=name,
        brand=brand,
        property_name=property_n,
        property_location=location,
        event_name=event,
        event_date=event_date,
        offer_description=offer,
        offer_expiry=expiry,
        target_segment=segment,
        channel=channel,
        objective=objective,
        raw_text=raw_text,
    )


def main():
    parser = argparse.ArgumentParser(description="ACC Campaign Agent")
    parser.add_argument("--brief",        type=str,  help="Path to brief JSON file")
    parser.add_argument("--auto-approve", action="store_true", help="Skip HITL prompt")
    parser.add_argument("--demo",         action="store_true", help="Run demo campaign")
    parser.add_argument("--angles",       type=int,  default=4,  help="Number of angles to generate (default 4)")
    args = parser.parse_args()

    # Load or build brief
    if args.demo:
        print("Running DEMO campaign...")
        brief = DEMO_BRIEF
    elif args.brief:
        brief = load_brief_from_json(args.brief)
    else:
        brief = interactive_brief()

    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\nError: ANTHROPIC_API_KEY environment variable not set.")
        print("Set it with: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    # Run pipeline
    package = orchestrator.run(
        brief=brief,
        auto_approve=args.auto_approve,
        n_angles=args.angles,
    )

    # Final status
    print("\n" + "=" * 50)
    if package.hitl_approved and package.output_path:
        print(f"  Campaign compiled successfully.")
        print(f"  Output: {package.output_path}")
    elif not package.hitl_approved:
        print("  Campaign rejected. No output generated.")
    else:
        print("  Pipeline halted.")
        if package.errors:
            for e in package.errors:
                print(f"  ! {e}")


if __name__ == "__main__":
    main()
