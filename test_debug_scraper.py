import asyncio
from playwright.async_api import async_playwright

async def test_scraper():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0")
        page = await context.new_page()

        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined })")

        await page.goto("https://www.oddsportal.com/matches/football/", timeout=60000)
        await page.wait_for_timeout(7000)

        print("[DEBUG] Taking screenshot")
        await page.screenshot(path="oddsportal_tomorrow.png", full_page=True)

        match_blocks = page.locator("a:has(div.participant-name)")
        print("[DEBUG] Match block count:", await match_blocks.count())

        await browser.close()

asyncio.run(test_scraper())
