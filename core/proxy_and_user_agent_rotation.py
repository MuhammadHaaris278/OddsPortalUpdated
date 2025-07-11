from playwright.sync_api import sync_playwright
import random


def get_rotating_proxy_and_headers():
    proxies = [
        "http://172.67.174.121:8080",
        "http://51.75.161.178:3128",
        "http://185.62.189.169:1080",
        "http://80.78.73.211:3128",
    ]

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    ]

    proxy = random.choice(proxies)
    user_agent = random.choice(user_agents)

    return proxy, user_agent


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    proxy, user_agent = get_rotating_proxy_and_headers()

    page.set_user_agent(user_agent)

    page.goto('https://www.oddsportal.com/matches/football/20250706/',
              proxy={"server": proxy})

    page.wait_for_selector('.event')
    content = page.content()
    print(content)

    browser.close()
