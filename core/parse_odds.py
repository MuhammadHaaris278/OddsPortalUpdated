# core/parse_odds.py

from playwright.sync_api import sync_playwright
import time


def extract_markets(match_url, proxy=None, user_agent=None):
    result_market = None
    result_odds = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=user_agent,
                proxy={"server": proxy} if proxy else None,
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            page.goto(match_url, timeout=30000)
            page.wait_for_timeout(3000)

            # Click "Show more markets" if it exists
            try:
                more_button = page.query_selector(
                    "button:has-text('Show more')")
                if more_button:
                    more_button.click()
                    page.wait_for_timeout(1000)
            except:
                pass

            tables = page.query_selector_all("div#odds-data-table")

            for table in tables:
                header = table.query_selector("h2")
                if not header:
                    continue
                market_name = header.inner_text().strip().lower()

                if "moneyline" in market_name or "1x2" in market_name:
                    result_market = "Moneyline"
                    result_odds["Moneyline"] = extract_odds_from_table(table)

                elif "draw no bet" in market_name:
                    result_odds["Draw No Bet"] = extract_odds_from_table(table)

                elif "double chance" in market_name:
                    result_odds["Double Chance"] = extract_odds_from_table(
                        table)

                elif "spread" in market_name or "handicap" in market_name:
                    result_odds["Spread"] = extract_odds_from_table(table)

            browser.close()

    except Exception as e:
        print(f"[!] Failed to extract odds: {str(e)}")

    return result_market, result_odds


def extract_odds_from_table(table):
    try:
        odds_data = {}
        rows = table.query_selector_all("tr")
        for row in rows:
            try:
                cells = row.query_selector_all("td")
                if len(cells) >= 3:
                    team = cells[0].inner_text().strip()
                    odd = cells[1].inner_text().strip()
                    odds_data[team] = odd
            except:
                continue
        return odds_data
    except Exception as e:
        return {}
