import datetime
import os
import json
import pandas as pd
from core.utils import get_logger
from playwright.async_api import async_playwright
import asyncio

log = get_logger()


async def scrape_wnba(url: str, output_subfolder: str, user_agent=None) -> list[dict]:
    matches = []

    output_dir = os.path.join("./output", output_subfolder)
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()

        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(5000)

        await page.wait_for_selector('div[data-testid="game-row"]')
        match_blocks = page.locator('div[data-testid="game-row"]')

        count = await match_blocks.count()
        log.info(f"[WNBA] Found {count} match rows")

        now = datetime.datetime.utcnow()
        formatted_date = now.strftime('%Y%m%d')

        for i in range(count):
            try:
                block = match_blocks.nth(i)

                team_links = block.locator("a[title]")
                if await team_links.count() < 2:
                    continue

                team1 = await team_links.nth(0).get_attribute("title")
                team2 = await team_links.nth(1).get_attribute("title")

                odds_tags = block.locator(
                    'p[data-testid="odd-container-default"]')
                odds = []
                for j in range(await odds_tags.count()):
                    val = await odds_tags.nth(j).inner_text()
                    odds.append(val.strip())

                match_datetime = now.replace(
                    hour=0, minute=0, second=0) + datetime.timedelta(minutes=i * 5)

                matches.append({
                    "datetime": match_datetime.isoformat(),
                    "league": "WNBA",
                    "team1": team1,
                    "team2": team2,
                    "odds": odds[:3],
                    "match_url": url
                })

            except Exception as e:
                log.warning(f"[WNBA] Failed to parse match {i}: {e}")
                continue

        await context.close()
        await browser.close()

        if matches:
            df = pd.DataFrame(matches)
            csv_path = os.path.join(
                output_dir, f"wnba_matches_{formatted_date}.csv")
            json_path = os.path.join(
                output_dir, f"wnba_matches_{formatted_date}.json")

            df.to_csv(csv_path, index=False)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(matches, f, indent=4)

            log.info(f"[WNBA] Saved CSV to {csv_path}")
            log.info(f"[WNBA] Saved JSON to {json_path}")
        else:
            log.warning(f"[WNBA] No matches scraped.")

    return matches


async def scrape_ncaa(url: str, output_subfolder: str, user_agent=None) -> list[dict]:
    matches = []

    output_dir = os.path.join("./output", output_subfolder)
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()

        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(5000)

        await page.wait_for_selector('div[data-testid="game-row"]')
        match_blocks = page.locator('div[data-testid="game-row"]')

        count = await match_blocks.count()
        log.info(f"[NCAA] Found {count} match rows")

        now = datetime.datetime.utcnow()
        formatted_date = now.strftime('%Y%m%d')

        for i in range(count):
            try:
                block = match_blocks.nth(i)

                team_links = block.locator("a[title]")
                if await team_links.count() < 2:
                    continue

                team1 = await team_links.nth(0).get_attribute("title")
                team2 = await team_links.nth(1).get_attribute("title")

                odds_tags = block.locator(
                    'p[data-testid="odd-container-default"]')
                odds = []
                for j in range(await odds_tags.count()):
                    val = await odds_tags.nth(j).inner_text()
                    odds.append(val.strip())

                match_datetime = now.replace(
                    hour=0, minute=0, second=0) + datetime.timedelta(minutes=i * 5)

                matches.append({
                    "datetime": match_datetime.isoformat(),
                    "league": "NCAA",
                    "team1": team1,
                    "team2": team2,
                    "odds": odds[:3],
                    "match_url": url
                })

            except Exception as e:
                log.warning(f"[NCAA] Failed to parse match {i}: {e}")
                continue

        await context.close()
        await browser.close()

        if matches:
            df = pd.DataFrame(matches)
            csv_path = os.path.join(
                output_dir, f"ncaa_matches_{formatted_date}.csv")
            json_path = os.path.join(
                output_dir, f"ncaa_matches_{formatted_date}.json")

            df.to_csv(csv_path, index=False)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(matches, f, indent=4)

            log.info(f"[NCAA] Saved CSV to {csv_path}")
            log.info(f"[NCAA] Saved JSON to {json_path}")
        else:
            log.warning(f"[NCAA] No matches scraped.")

    return matches


async def scrape_nfl(url: str, output_subfolder: str, user_agent=None) -> list[dict]:
    matches = []

    output_dir = os.path.join("./output", output_subfolder)
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()

        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(5000)

        await page.wait_for_selector('div[data-testid="game-row"]')
        match_blocks = page.locator('div[data-testid="game-row"]')

        count = await match_blocks.count()
        log.info(f"[NFL] Found {count} match rows")

        now = datetime.datetime.utcnow()
        formatted_date = now.strftime('%Y%m%d')

        for i in range(count):
            try:
                block = match_blocks.nth(i)

                team_links = block.locator("a[title]")
                if await team_links.count() < 2:
                    continue

                team1 = await team_links.nth(0).get_attribute("title")
                team2 = await team_links.nth(1).get_attribute("title")

                odds_tags = block.locator(
                    'p[data-testid="odd-container-default"]')
                odds = []
                for j in range(await odds_tags.count()):
                    val = await odds_tags.nth(j).inner_text()
                    odds.append(val.strip())

                match_datetime = now.replace(
                    hour=0, minute=0, second=0) + datetime.timedelta(minutes=i * 5)

                matches.append({
                    "datetime": match_datetime.isoformat(),
                    "league": "NFL",
                    "team1": team1,
                    "team2": team2,
                    "odds": odds[:3],
                    "match_url": url
                })

            except Exception as e:
                log.warning(f"[NFL] Failed to parse match {i}: {e}")
                continue

        await context.close()
        await browser.close()

        if matches:
            df = pd.DataFrame(matches)
            csv_path = os.path.join(
                output_dir, f"nfl_matches_{formatted_date}.csv")
            json_path = os.path.join(
                output_dir, f"nfl_matches_{formatted_date}.json")

            df.to_csv(csv_path, index=False)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(matches, f, indent=4)

            log.info(f"[NFL] Saved CSV to {csv_path}")
            log.info(f"[NFL] Saved JSON to {json_path}")
        else:
            log.warning(f"[NFL] No matches scraped.")

    return matches


async def scrape_sport(sport: str, url: str, output_subfolder: str, user_agent=None) -> list[dict]:
    matches = []

    output_dir = os.path.join("./output", output_subfolder)
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()

        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(5000)

        await page.wait_for_selector('div[data-testid="game-row"]')
        match_blocks = page.locator('div[data-testid="game-row"]')

        count = await match_blocks.count()
        log.info(f"[{sport.upper()}] Found {count} match rows")

        now = datetime.datetime.utcnow()
        formatted_date = now.strftime('%Y%m%d')

        for i in range(count):
            try:
                block = match_blocks.nth(i)

                team_links = block.locator("a[title]")
                if await team_links.count() < 2:
                    continue

                team1 = await team_links.nth(0).get_attribute("title")
                team2 = await team_links.nth(1).get_attribute("title")

                odds_tags = block.locator(
                    'p[data-testid="odd-container-default"]')
                odds = []
                for j in range(await odds_tags.count()):
                    val = await odds_tags.nth(j).inner_text()
                    odds.append(val.strip())

                match_datetime = now.replace(
                    hour=0, minute=0, second=0) + datetime.timedelta(minutes=i * 5)

                matches.append({
                    "datetime": match_datetime.isoformat(),
                    "league": "Unknown",
                    "team1": team1,
                    "team2": team2,
                    "odds": odds[:3],
                    "match_url": url
                })

            except Exception as e:
                log.warning(
                    f"[{sport.upper()}] Failed to parse match {i}: {e}")
                continue

        await context.close()
        await browser.close()

        if matches:
            df = pd.DataFrame(matches)
            csv_path = os.path.join(
                output_dir, f"{sport}_matches_{formatted_date}.csv")
            json_path = os.path.join(
                output_dir, f"{sport}_matches_{formatted_date}.json")

            df.to_csv(csv_path, index=False)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(matches, f, indent=4)

            log.info(f"[{sport.upper()}] Saved CSV to {csv_path}")
            log.info(f"[{sport.upper()}] Saved JSON to {json_path}")
        else:
            log.warning(f"[{sport.upper()}] No matches scraped.")

    return matches


async def fetch_matches(proxy=None, user_agent=None) -> list[dict]:
    tomorrow = datetime.datetime.utcnow().date() + datetime.timedelta(days=1)
    date_str = tomorrow.strftime('%Y%m%d')

    football_url = f"https://www.oddsportal.com/matches/football/{date_str}/"
    basketball_url = f"https://www.oddsportal.com/matches/basketball/{date_str}/"
    tennis_url = f"https://www.oddsportal.com/matches/tennis/{date_str}/"
    futsal_url = f"https://www.oddsportal.com/matches/futsal/{date_str}/"
    baseball_url = f"https://www.oddsportal.com/matches/baseball/{date_str}/"
    nfl_url = "https://www.oddsportal.com/american-football/usa/nfl/"
    ncaa_url = "https://www.oddsportal.com/american-football/usa/ncaa/"
    wnba_url = "https://www.oddsportal.com/basketball/usa/wnba/"

    all_matches = []

    # FOR scrape_sport: provide 3 args: sport, url, output_subfolder
    for sport, url in [
        ("football", football_url),
        ("basketball", basketball_url),
        ("tennis", tennis_url),
        ("futsal", futsal_url),
        ("baseball", baseball_url),
    ]:
        try:
            result = await scrape_sport(sport, url, sport, user_agent=user_agent)
            all_matches.extend(result)
        except Exception as e:
            log.error(f"[{sport.upper()}] Error during scraping: {e}")

    # For unique scrapers (nfl, ncaa, wnba)
    for name, url, folder, func in [
        ("nfl", nfl_url, "nfl", scrape_nfl),
        ("ncaa", ncaa_url, "ncaa", scrape_ncaa),
        ("wnba", wnba_url, "wnba", scrape_wnba),
    ]:
        try:
            result = await func(url, folder, user_agent=user_agent)
            all_matches.extend(result)
        except Exception as e:
            log.error(f"[{name.upper()}] Error during scraping: {e}")

    return all_matches
