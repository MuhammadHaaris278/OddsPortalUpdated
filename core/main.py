import asyncio
import os
import json
import pandas as pd
from datetime import datetime
from core.utils import get_logger
from core.fetch_matches import fetch_matches
from utils.user_agent_pool import get_random_user_agent

logger = get_logger()

def save_results(matches):
    if not matches:
        logger.warning("No matches to save.")
        return

    flat = []
    for match in matches:
        try:
            team1, team2 = match.get("teams", " vs ").split(" vs ", 1)
        except ValueError:
            team1, team2 = match.get("teams", ""), ""

        flat.append({
            "datetime": match.get("datetime", ""),
            "league": match.get("league", ""),
            "team1": team1,
            "team2": team2,
            "odds": json.dumps(match.get("odds", []), ensure_ascii=False),
            "match_url": match.get("match_url", "")
        })

    df = pd.DataFrame(flat)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = os.path.join("output", f"consolidated_matches_{timestamp}.csv")
    df.to_csv(output_path, index=False)
    logger.info(f"[✔] Results saved to: {output_path}")


def main():
    logger.info("[*] Starting OddsPortal Scraper...")
    proxy = None  # Disable for testing
    user_agent = get_random_user_agent()
    logger.info(f"[*] Using UA: {user_agent}")

    try:
        matches = asyncio.run(fetch_matches(proxy=proxy, user_agent=user_agent))
        logger.info(f"[+] Total matches scraped: {len(matches)}")
        save_results(matches)
    except Exception as e:
        logger.error(f"[!] Critical failure: {str(e)}")

    logger.info("[✔] Scraping finished.")


if __name__ == "__main__":
    main()
