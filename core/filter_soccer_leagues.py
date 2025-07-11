# core/filter_soccer_leagues.py

import json

# Load allowed soccer leagues (Tier 1 & 2) from config
def load_whitelist():
    try:
        with open("config/league_whitelist.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Failed to load whitelist: {e}")
        return []

def filter_soccer(matches):
    whitelist = load_whitelist()
    filtered = []

    for match in matches:
        if match["sport"] != "Soccer":
            filtered.append(match)
            continue

        # Check if match belongs to an allowed league
        if any(league.lower() in match["teams"].lower() for league in whitelist):
            filtered.append(match)

    return filtered
