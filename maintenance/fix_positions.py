#!/usr/bin/env python3
"""
Fix position data in scraped JSON files.

Recalculates position fields from positionsByMatch data:
- position: Category (GK/DEF/MID/FOR)
- primaryPosition: Most frequent specific position (CB, ST, etc.)
- secondaryPosition: Second most frequent specific position

Usage:
    python3 fix_positions.py              # Dry run - show what would change
    python3 fix_positions.py --apply      # Apply fixes to files
    python3 fix_positions.py --club nyrb  # Fix specific club only
"""

import json
import os
import sys
from pathlib import Path
from collections import Counter

# Position classification (same as scraper3.py)
POSITION_CATEGORIES = {
    "GK": "GK",
    # Defenders
    "CB": "DEF", "LB": "DEF", "RB": "DEF", "LWB": "DEF", "RWB": "DEF", "SW": "DEF", "SWP": "DEF",
    # Midfielders
    "DM": "MID", "CM": "MID", "AM": "MID", "LM": "MID", "RM": "MID", "CDM": "MID", "CAM": "MID",
    # Forwards
    "LW": "FOR", "RW": "FOR", "CF": "FOR", "ST": "FOR", "SS": "FOR", "WF": "FOR", "FW": "FOR",
    # Unknown
    "Oth": ""
}


def classify_position(position_code):
    """Map specific position to category (GK/DEF/MID/FOR)."""
    if not position_code:
        return ""
    return POSITION_CATEGORIES.get(position_code.upper(), "")


def calculate_position_category(positions_by_match):
    """Calculate primary position category from match history."""
    if not positions_by_match:
        return ""

    category_counts = {"GK": 0, "DEF": 0, "MID": 0, "FOR": 0}

    for match in positions_by_match:
        category = classify_position(match.get("position", ""))
        if category in category_counts:
            category_counts[category] += 1

    max_category = max(category_counts, key=category_counts.get)
    return max_category if category_counts[max_category] > 0 else ""


def calculate_specific_positions(positions_by_match):
    """Calculate primary and secondary specific positions."""
    if not positions_by_match:
        return "", ""

    # Count specific positions (excluding "Oth" and empty)
    counts = Counter()
    for match in positions_by_match:
        pos = match.get("position", "")
        if pos and pos != "Oth":
            counts[pos] += 1

    if not counts:
        return "", ""

    most_common = counts.most_common(2)
    primary = most_common[0][0] if len(most_common) > 0 else ""
    secondary = most_common[1][0] if len(most_common) > 1 else ""

    return primary, secondary


def fix_player_positions(player):
    """Fix position fields for a single player. Returns (fixed_player, changes)."""
    changes = []
    fixed = player.copy()

    positions_by_match = player.get("positionsByMatch", [])

    if not positions_by_match:
        return fixed, []

    # Calculate correct values
    correct_category = calculate_position_category(positions_by_match)
    correct_primary, correct_secondary = calculate_specific_positions(positions_by_match)

    # Check and fix position (category)
    current_position = player.get("position", "")
    if current_position != correct_category:
        changes.append(f"position: {current_position!r} → {correct_category!r}")
        fixed["position"] = correct_category

    # Check and fix primaryPosition
    current_primary = player.get("primaryPosition", "")
    if current_primary != correct_primary:
        changes.append(f"primaryPosition: {current_primary!r} → {correct_primary!r}")
        fixed["primaryPosition"] = correct_primary

    # Check and fix secondaryPosition
    current_secondary = player.get("secondaryPosition", "")
    if current_secondary != correct_secondary:
        changes.append(f"secondaryPosition: {current_secondary!r} → {correct_secondary!r}")
        fixed["secondaryPosition"] = correct_secondary

    return fixed, changes


def process_json_file(filepath, apply_changes=False):
    """Process a single JSON file. Returns (num_fixes, details)."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    players = data.get("players", [])
    if not players:
        return 0, []

    total_fixes = 0
    details = []
    fixed_players = []

    for player in players:
        fixed_player, changes = fix_player_positions(player)
        fixed_players.append(fixed_player)

        if changes:
            total_fixes += 1
            details.append({
                "name": player.get("name", "Unknown"),
                "changes": changes
            })

    if apply_changes and total_fixes > 0:
        data["players"] = fixed_players
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    return total_fixes, details


def find_json_files(base_dir, club_filter=None):
    """Find all squad JSON files."""
    files = []
    base = Path(base_dir)

    for club_dir in base.iterdir():
        if not club_dir.is_dir():
            continue
        if club_dir.name.startswith(('.', '_')):
            continue
        if club_dir.name in ['audit_logs', 'batch_configs', 'scouting-map', 'venv']:
            continue

        # Apply club filter if specified
        if club_filter and club_filter.lower() not in club_dir.name.lower():
            continue

        for json_file in club_dir.glob("U*.json"):
            files.append(json_file)

    return sorted(files)


def main():
    apply_changes = "--apply" in sys.argv

    # Check for club filter
    club_filter = None
    for i, arg in enumerate(sys.argv):
        if arg == "--club" and i + 1 < len(sys.argv):
            club_filter = sys.argv[i + 1]

    base_dir = Path(__file__).parent
    json_files = find_json_files(base_dir, club_filter)

    if not json_files:
        print("No JSON files found.")
        return

    print(f"{'=' * 60}")
    print(f"Position Fix Script")
    print(f"{'=' * 60}")
    print(f"Mode: {'APPLY CHANGES' if apply_changes else 'DRY RUN (use --apply to save)'}")
    if club_filter:
        print(f"Filter: {club_filter}")
    print(f"Files to process: {len(json_files)}")
    print(f"{'=' * 60}\n")

    total_files_fixed = 0
    total_players_fixed = 0

    for filepath in json_files:
        num_fixes, details = process_json_file(filepath, apply_changes)

        if num_fixes > 0:
            total_files_fixed += 1
            total_players_fixed += num_fixes

            relative_path = filepath.relative_to(base_dir)
            print(f"📁 {relative_path}")
            print(f"   {num_fixes} player(s) to fix:")

            for d in details[:5]:  # Show first 5 players
                print(f"   • {d['name']}")
                for change in d['changes']:
                    print(f"     - {change}")

            if len(details) > 5:
                print(f"   ... and {len(details) - 5} more")
            print()

    print(f"{'=' * 60}")
    print(f"Summary:")
    print(f"  Files with fixes needed: {total_files_fixed}")
    print(f"  Players to fix: {total_players_fixed}")

    if apply_changes:
        print(f"\n✅ Changes applied to {total_files_fixed} files.")
    else:
        print(f"\n⚠️  This was a dry run. Use --apply to save changes.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
