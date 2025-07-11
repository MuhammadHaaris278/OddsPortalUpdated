import streamlit as st
import asyncio
import os
import json
import pandas as pd
from datetime import datetime, timedelta
import zipfile
import io
from pathlib import Path
import sys
import concurrent.futures
import threading
import time
import platform
import traceback

# Add the current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your existing modules
try:
    from core.fetch_matches import fetch_matches
    from utils.user_agent_pool import get_random_user_agent
    from core.utils import get_logger
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# Fix for Windows event loop policy
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def run_async_scraping(user_agent, log_container):
    """
    Runs the async scraping function in a way that's compatible with Streamlit's event loop
    """
    def scraping_thread():
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Set Windows-specific event loop policy if needed
        if platform.system() == "Windows":
            asyncio.set_event_loop_policy(
                asyncio.WindowsProactorEventLoopPolicy())

        try:
            return loop.run_until_complete(fetch_matches_with_logs(user_agent=user_agent, log_container=log_container))
        except Exception as e:
            raise Exception(
                f"Scraping failed: {str(e)}\n{traceback.format_exc()}")
        finally:
            loop.close()

    # Run the scraping in a separate thread to avoid event loop conflicts
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(scraping_thread)
        try:
            return future.result(timeout=600)  # 10 minute timeout
        except concurrent.futures.TimeoutError:
            raise TimeoutError("Scraping operation timed out after 10 minutes")
        except Exception as e:
            raise Exception(
                f"Thread execution failed: {str(e)}\n{traceback.format_exc()}")


async def fetch_matches_with_logs(user_agent=None, log_container=None):
    """
    Modified fetch_matches that provides logging updates and fixes league categorization
    """
    def update_log(message):
        if log_container:
            current_time = datetime.now().strftime("%H:%M:%S")
            log_container.append(f"[{current_time}] {message}")

    tomorrow = datetime.utcnow().date() + timedelta(days=1)
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

    # Import the scraping functions
    from core.fetch_matches import scrape_sport, scrape_nfl, scrape_ncaa, scrape_wnba

    update_log("🚀 Starting scraping process...")
    update_log(f"📅 Scraping matches for date: {date_str}")

    # Scrape general sports with proper league names
    sports_config = [
        ("football", football_url, "Football"),
        ("basketball", basketball_url, "Basketball"),
        ("tennis", tennis_url, "Tennis"),
        ("futsal", futsal_url, "Futsal"),
        ("baseball", baseball_url, "Baseball"),
    ]

    for sport, url, display_name in sports_config:
        try:
            update_log(f"🔍 Scraping {display_name} matches...")
            result = await scrape_sport_with_league_fix(sport, url, sport, display_name, user_agent=user_agent)
            all_matches.extend(result)
            update_log(f"✅ {display_name}: Found {len(result)} matches")
            update_log(f"💾 Saved {display_name} data to files")
        except Exception as e:
            update_log(f"❌ {display_name}: Error during scraping - {str(e)}")

    # Scrape specialized sports
    specialized_sports = [
        ("NFL", nfl_url, "nfl", scrape_nfl),
        ("NCAA", ncaa_url, "ncaa", scrape_ncaa),
        ("WNBA", wnba_url, "wnba", scrape_wnba),
    ]

    for name, url, folder, func in specialized_sports:
        try:
            update_log(f"🔍 Scraping {name} matches...")
            result = await func(url, folder, user_agent=user_agent)
            all_matches.extend(result)
            update_log(f"✅ {name}: Found {len(result)} matches")
            update_log(f"💾 Saved {name} data to files")
        except Exception as e:
            update_log(f"❌ {name}: Error during scraping - {str(e)}")

    update_log(
        f"🎉 Scraping completed! Total matches found: {len(all_matches)}")
    return all_matches


async def scrape_sport_with_league_fix(sport: str, url: str, output_subfolder: str, league_name: str, user_agent=None) -> list[dict]:
    """
    Modified scrape_sport function that sets the correct league name
    """
    matches = []

    # Import required modules
    from playwright.async_api import async_playwright
    from core.utils import get_logger

    log = get_logger()
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

        now = datetime.utcnow()
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
                    hour=0, minute=0, second=0) + timedelta(minutes=i * 5)

                matches.append({
                    "datetime": match_datetime.isoformat(),
                    "league": league_name,  # Use the correct league name instead of "Unknown"
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


def generate_sample_data():
    """Generate sample data when scraping fails"""
    sample_matches = []
    sports = ["NFL", "NBA", "WNBA", "NCAA", "Tennis",
              "Football", "Basketball", "Baseball", "Futsal"]
    teams = {
        "NFL": [("Kansas City Chiefs", "Buffalo Bills"), ("Green Bay Packers", "Dallas Cowboys")],
        "NBA": [("Los Angeles Lakers", "Boston Celtics"), ("Golden State Warriors", "Miami Heat")],
        "WNBA": [("Las Vegas Aces", "New York Liberty"), ("Seattle Storm", "Phoenix Mercury")],
        "NCAA": [("Duke Blue Devils", "North Carolina Tar Heels"), ("UCLA Bruins", "USC Trojans")],
        "Tennis": [("Novak Djokovic", "Rafael Nadal"), ("Serena Williams", "Venus Williams")],
        "Football": [("Manchester United", "Liverpool"), ("Barcelona", "Real Madrid")],
        "Basketball": [("Team Phoenix", "Team Thunder"), ("Team Lightning", "Team Storm")],
        "Baseball": [("New York Yankees", "Boston Red Sox"), ("Los Angeles Dodgers", "San Francisco Giants")],
        "Futsal": [("Team Alpha", "Team Beta"), ("Team Gamma", "Team Delta")]
    }

    for sport in sports:
        for i, (team1, team2) in enumerate(teams[sport]):
            sample_matches.append({
                "datetime": (datetime.now() + timedelta(hours=i+1)).isoformat(),
                "league": sport,
                "team1": team1,
                "team2": team2,
                "odds": ["+150", "-110", "+200"],
                "match_url": f"https://www.oddsportal.com/sample/{sport.lower()}"
            })

    return sample_matches


# Page configuration
st.set_page_config(
    page_title="OddsPortal Scraper",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    
    .navbar {
        background-color: #1e3d59;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .navbar h3 {
        color: white;
        margin: 0;
        text-align: center;
    }
    
    .sport-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin: 2rem 0;
    }
    
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        min-width: 150px;
    }
    
    .footer {
        background-color: #1e3d59;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-top: 3rem;
    }
    
    .download-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-top: 2rem;
    }
    
    .stButton > button {
        background-color: #667eea;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #5a6fd8;
        transform: translateY(-2px);
    }
    
    .error-section {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin-bottom: 1rem;
    }
    
    .success-section {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin-bottom: 1rem;
    }
    
    .terminal-container {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #333;
    }
    
    .terminal-header {
        background-color: #2d2d2d;
        padding: 0.5rem;
        border-radius: 5px 5px 0 0;
        color: #fff;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .terminal-content {
        background-color: #000;
        color: #00ff00;
        padding: 1rem;
        border-radius: 0 0 5px 5px;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        max-height: 300px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = None
if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False
if 'last_scrape_time' not in st.session_state:
    st.session_state.last_scrape_time = None
if 'last_error' not in st.session_state:
    st.session_state.last_error = None
if 'terminal_logs' not in st.session_state:
    st.session_state.terminal_logs = []

# Navbar
st.markdown("""
<div class="navbar">
    <h3>🏆 OddsPortal Scraper Dashboard</h3>
</div>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="main-header">
    <h1>🎯 OddsPortal Data Scraper</h1>
    <p>Automated sports betting odds scraper with stealth capabilities</p>
    <p>Scrapes matches from multiple sports leagues for the next 24 hours</p>
</div>
""", unsafe_allow_html=True)

# Show system information and warnings
st.markdown("## 🖥️ System Information")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Operating System", platform.system())
with col2:
    st.metric("Python Version",
              f"{sys.version_info.major}.{sys.version_info.minor}")
with col3:
    st.metric("Streamlit Version", st.__version__)

# Windows-specific warnings
if platform.system() == "Windows":
    st.warning("""
    ⚠️ **Windows Detected**: If you encounter Playwright browser errors, please run these commands:
    
    ```bash
    pip install playwright
    playwright install
    playwright install-deps
    ```
    
    For development and testing, use **Test Mode** to avoid browser automation issues.
    """)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("## 📊 Scraping Control Panel")

    # Test mode toggle
    test_mode = st.checkbox("🧪 Test Mode (Generate Sample Data)",
                            value=True,  # Default to True for Windows users
                            help="Use this to test the UI without running actual scraping. Recommended for Windows users experiencing browser issues.")

    # Scraping controls
    button_text = "🧪 Generate Sample Data" if test_mode else "🚀 Start Scraping"
    button_help = "Generate sample data for testing" if test_mode else "Start live scraping from OddsPortal"

    if st.button(button_text, disabled=st.session_state.scraping_in_progress, help=button_help):
        st.session_state.scraping_in_progress = True
        st.session_state.last_error = None
        st.session_state.terminal_logs = []

        spinner_text = "🔄 Generating sample data..." if test_mode else "🔄 Scraping odds data with stealth mode..."

        with st.spinner(spinner_text):
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Create terminal log container
            terminal_container = st.container()
            with terminal_container:
                st.markdown("### 🖥️ Terminal Logs")
                log_display = st.empty()

            try:
                if test_mode:
                    # Generate sample data for testing
                    status_text.text("Generating sample sports data...")
                    st.session_state.terminal_logs.append(
                        "[12:34:56] 🚀 Starting sample data generation...")
                    log_display.code(
                        '\n'.join(st.session_state.terminal_logs[-10:]))
                    progress_bar.progress(30)
                    time.sleep(1)  # Simulate processing time

                    status_text.text("Creating mock matches...")
                    st.session_state.terminal_logs.append(
                        "[12:34:57] 📊 Creating mock matches for all sports...")
                    log_display.code(
                        '\n'.join(st.session_state.terminal_logs[-10:]))
                    progress_bar.progress(60)
                    time.sleep(1)

                    matches = generate_sample_data()
                    progress_bar.progress(100)
                    status_text.text("✅ Sample data generated successfully!")
                    st.session_state.terminal_logs.append(
                        f"[12:34:58] ✅ Sample data generation completed! Generated {len(matches)} matches")
                    log_display.code(
                        '\n'.join(st.session_state.terminal_logs[-10:]))

                else:
                    # Initialize logger
                    logger = get_logger()

                    # Get random user agent for stealth
                    user_agent = get_random_user_agent()
                    status_text.text(
                        f"Using stealth user agent: {user_agent[:50]}...")
                    st.session_state.terminal_logs.append(
                        f"[{datetime.now().strftime('%H:%M:%S')}] 🔒 Using stealth user agent: {user_agent[:50]}...")
                    log_display.code(
                        '\n'.join(st.session_state.terminal_logs[-10:]))
                    progress_bar.progress(10)

                    # Check Playwright installation
                    try:
                        from playwright.async_api import async_playwright
                        status_text.text(
                            "Playwright detected, initializing...")
                        st.session_state.terminal_logs.append(
                            f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Playwright detected, initializing browser...")
                        log_display.code(
                            '\n'.join(st.session_state.terminal_logs[-10:]))
                        progress_bar.progress(20)
                    except ImportError:
                        raise ImportError(
                            "Playwright is not installed. Please run: pip install playwright && playwright install")

                    # Run the scraping with proper event loop handling
                    status_text.text("Initializing browser and scraping...")
                    st.session_state.terminal_logs.append(
                        f"[{datetime.now().strftime('%H:%M:%S')}] 🌐 Initializing browser and starting scraping process...")
                    log_display.code(
                        '\n'.join(st.session_state.terminal_logs[-10:]))
                    progress_bar.progress(40)

                    # Create a container for live log updates
                    class LogContainer:
                        def __init__(self):
                            self.logs = st.session_state.terminal_logs

                        def append(self, message):
                            self.logs.append(message)

                    log_container = LogContainer()
                    matches = run_async_scraping(user_agent, log_container)
                    progress_bar.progress(80)

                    status_text.text("Processing scraped data...")
                    st.session_state.terminal_logs.append(
                        f"[{datetime.now().strftime('%H:%M:%S')}] 📋 Processing and organizing scraped data...")
                    log_display.code(
                        '\n'.join(st.session_state.terminal_logs[-10:]))

                # Store results
                st.session_state.scraped_data = matches
                st.session_state.last_scrape_time = datetime.now()

                progress_bar.progress(100)
                completion_text = "✅ Sample data ready!" if test_mode else "✅ Scraping completed successfully!"
                status_text.text(completion_text)

                success_text = f"🎉 Successfully generated {len(matches)} sample matches!" if test_mode else f"🎉 Successfully scraped {len(matches)} matches!"
                st.success(success_text)

            except Exception as e:
                st.session_state.last_error = f"{str(e)}\n\nFull traceback:\n{traceback.format_exc()}"
                error_msg = f"❌ Error during {'sample data generation' if test_mode else 'scraping'}: {str(e)}"
                st.error(error_msg)
                st.session_state.terminal_logs.append(
                    f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {str(e)}\n{traceback.format_exc()}")
                log_display.code(
                    '\n'.join(st.session_state.terminal_logs[-10:]))

                # Show detailed error for debugging
                with st.expander("🔍 Error Details"):
                    st.code(f"{str(e)}\n\n{traceback.format_exc()}")

                    # Windows-specific help
                    if platform.system() == "Windows" and "NotImplementedError" in str(e):
                        st.markdown("""
                        **Windows Playwright Fix:**
                        
                        This error is common on Windows. Try these solutions:
                        
                        1. **Install Playwright properly:**
                           ```bash
                           pip uninstall playwright
                           pip install playwright
                           playwright install
                           ```
                        
                        2. **Use Test Mode** for development and testing
                        
                        3. **Check your Windows version** - some older versions have issues with subprocess
                        
                        4. **Try running as Administrator** if the issue persists
                        """)

                # Offer fallback option
                if not test_mode:
                    st.info(
                        "💡 You can enable 'Test Mode' to generate sample data and test the UI functionality.")

            finally:
                st.session_state.scraping_in_progress = False
                progress_bar.empty()
                status_text.empty()

with col2:
    st.markdown("## 📈 Stats")

    if st.session_state.scraped_data:
        total_matches = len(st.session_state.scraped_data)

        # Group by league
        leagues = {}
        for match in st.session_state.scraped_data:
            league = match.get('league', 'Unknown')
            leagues[league] = leagues.get(league, 0) + 1

        # Display stats
        st.metric("Total Matches", total_matches)
        st.metric("Sports Covered", len(leagues))

        if st.session_state.last_scrape_time:
            st.metric("Last Scrape",
                      st.session_state.last_scrape_time.strftime("%H:%M:%S"))

        # League breakdown
        st.markdown("### League Breakdown")
        for league, count in leagues.items():
            st.write(f"**{league}**: {count} matches")
    else:
        st.info("No data available. Run scraping first.")

    # Show last error if any
    if st.session_state.last_error:
        st.markdown("### ⚠️ Last Error")
        st.error(st.session_state.last_error[:100] + "..." if len(
            st.session_state.last_error) > 100 else st.session_state.last_error)

# Data Display and Download Section
if st.session_state.scraped_data:
    st.markdown("---")
    st.markdown("## 📁 Scraped Data & Downloads")

    # Group matches by sport/league
    sports_data = {}
    for match in st.session_state.scraped_data:
        sport = match.get('league', 'Unknown').lower()
        if sport not in sports_data:
            sports_data[sport] = []
        sports_data[sport].append(match)

    # Create tabs for different sports
    if sports_data:
        tabs = st.tabs(list(sports_data.keys()))

        for i, (sport, matches) in enumerate(sports_data.items()):
            with tabs[i]:
                st.markdown(
                    f"### {sport.upper()} Matches ({len(matches)} total)")

                # Convert to DataFrame for display
                df_data = []
                for match in matches:
                    df_data.append({
                        'DateTime': match.get('datetime', ''),
                        'Team 1': match.get('team1', ''),
                        'Team 2': match.get('team2', ''),
                        'Odds': ', '.join(match.get('odds', [])),
                        'URL': match.get('match_url', '')
                    })

                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)

                # Download buttons for individual sports
                col1, col2 = st.columns(2)

                with col1:
                    # CSV download
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    st.download_button(
                        label=f"📊 Download {sport.upper()} CSV",
                        data=csv_buffer.getvalue(),
                        file_name=f"{sport}_matches_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )

                with col2:
                    # JSON download
                    json_data = json.dumps(
                        matches, indent=2, ensure_ascii=False)
                    st.download_button(
                        label=f"📋 Download {sport.upper()} JSON",
                        data=json_data,
                        file_name=f"{sport}_matches_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json"
                    )

    # Download All Files Section
    st.markdown("---")
    st.markdown("## 📦 Download All Files")

    def create_zip_file():
        """Create a zip file containing all CSV and JSON files"""
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')

            for sport, matches in sports_data.items():
                # Create CSV
                df_data = []
                for match in matches:
                    df_data.append({
                        'DateTime': match.get('datetime', ''),
                        'Team 1': match.get('team1', ''),
                        'Team 2': match.get('team2', ''),
                        'Odds': ', '.join(match.get('odds', [])),
                        'URL': match.get('match_url', '')
                    })

                df = pd.DataFrame(df_data)

                # Add CSV to zip
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                zip_file.writestr(
                    f"{sport}_matches_{timestamp}.csv", csv_buffer.getvalue())

                # Add JSON to zip
                json_data = json.dumps(matches, indent=2, ensure_ascii=False)
                zip_file.writestr(
                    f"{sport}_matches_{timestamp}.json", json_data)

            # Add consolidated file
            all_matches_df = pd.DataFrame([
                {
                    'DateTime': match.get('datetime', ''),
                    'League': match.get('league', ''),
                    'Team 1': match.get('team1', ''),
                    'Team 2': match.get('team2', ''),
                    'Odds': ', '.join(match.get('odds', [])),
                    'URL': match.get('match_url', '')
                }
                for match in st.session_state.scraped_data
            ])

            consolidated_csv = io.StringIO()
            all_matches_df.to_csv(consolidated_csv, index=False)
            zip_file.writestr(
                f"consolidated_matches_{timestamp}.csv", consolidated_csv.getvalue())

            consolidated_json = json.dumps(
                st.session_state.scraped_data, indent=2, ensure_ascii=False)
            zip_file.writestr(
                f"consolidated_matches_{timestamp}.json", consolidated_json)

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    if st.button("📥 Prepare Download Package"):
        with st.spinner("Creating download package..."):
            zip_data = create_zip_file()

            st.download_button(
                label="⬇️ Download All Files (ZIP)",
                data=zip_data,
                file_name=f"oddsportal_scraper_data_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip"
            )

            st.success("📦 Download package ready!")

# Information Section
st.markdown("---")
st.markdown("## ℹ️ About This Scraper")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **🛡️ Stealth Features:**
    - Randomized user agents
    - Request delays and timing
    - Headless browser automation
    - Anti-detection measures
    """)

with col2:
    st.markdown("""
    **📊 Supported Sports:**
    - Football (Soccer)
    - Basketball (NBA, WNBA, NCAA)
    - American Football (NFL, NCAA)
    - Tennis
    - Baseball
    - Futsal
    """)

st.markdown("""
**⏰ Data Coverage:**
- Scrapes matches for the next 24 hours
- Updates odds and team information
- Exports in both CSV and JSON formats
- Consolidated and sport-specific files
""")

# Troubleshooting Section
st.markdown("---")
st.markdown("## 🔧 Troubleshooting")

with st.expander("💡 Common Issues & Solutions"):
    st.markdown("""
    **Issue: Playwright/Browser Errors (Windows)**
    - **Solution 1**: Use Test Mode for development
    - **Solution 2**: Reinstall Playwright:
      ```bash
      pip uninstall playwright
      pip install playwright
      playwright install
      playwright install-deps
      ```
    - **Solution 3**: Run as Administrator
    - **Solution 4**: Check Windows version compatibility
    
    **Issue: NotImplementedError on Windows**
    - This is a known issue with Playwright on some Windows systems
    - Use Test Mode to bypass browser automation
    - Consider using WSL (Windows Subsystem for Linux) for better compatibility
    
    **Issue: Event Loop Errors**
    - The app now handles Windows event loop policy automatically
    - Use Test Mode to verify UI functionality
    - Check if all dependencies are correctly installed
    
    **Issue: Module Import Errors**
    - Verify all project files are in the correct directories
    - Check that `core/` and `utils/` folders exist
    - Ensure all `__init__.py` files are present
    
    **Issue: Scraping Fails**
    - Website might be blocking requests
    - Check internet connection
    - Try enabling Test Mode for development
    - Verify the target website is accessible
    """)

with st.expander("🐛 Debug Information"):
    st.markdown("**Environment Information:**")
    st.code(f"""
Python Version: {sys.version}
Streamlit Version: {st.__version__}
Platform: {platform.system()} {platform.release()}
Architecture: {platform.machine()}
Current Directory: {os.getcwd()}
Event Loop Policy: {type(asyncio.get_event_loop_policy()).__name__}
""")

    if st.button("🔍 Check Dependencies"):
        dependency_checks = []

        # Check Playwright
        try:
            import playwright
            from playwright.async_api import async_playwright
            dependency_checks.append(
                ("✅ Playwright", "Installed and importable"))
        except ImportError as e:
            dependency_checks.append(
                ("❌ Playwright", f"Not installed: {str(e)}"))

        # Check core modules
        try:
            from core.fetch_matches import fetch_matches
            dependency_checks.append(("✅ Core modules", "Accessible"))
        except ImportError as e:
            dependency_checks.append(
                ("❌ Core modules", f"Not accessible: {str(e)}"))

        # Check utils modules
        try:
            from utils.user_agent_pool import get_random_user_agent
            dependency_checks.append(("✅ Utils modules", "Accessible"))
        except ImportError as e:
            dependency_checks.append(
                ("❌ Utils modules", f"Not accessible: {str(e)}"))

        # Check pandas
        try:
            import pandas as pd
            dependency_checks.append(("✅ Pandas", f"Version {pd.__version__}"))
        except ImportError as e:
            dependency_checks.append(("❌ Pandas", f"Not installed: {str(e)}"))

        # Display results
        for status, message in dependency_checks:
            if "✅" in status:
                st.success(f"{status}: {message}")
            else:
                st.error(f"{status}: {message}")

# Footer
st.markdown("""
<div class="footer">
    <h3>🏆 OddsPortal Scraper</h3>
    <p>Dynamic data scraping with stealth capabilities</p>
    <p>Built with ❤️ using Streamlit, Playwright, and Python</p>
    <p>© 2024 - Automated Sports Data Collection</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with additional info
with st.sidebar:
    st.markdown("## 🔧 Settings")

    # Auto-refresh option
    auto_refresh = st.checkbox("Auto-refresh every 30 minutes")

    if auto_refresh:
        st.info("⏰ Auto-refresh enabled")

    st.markdown("---")
    st.markdown("## 📋 Quick Info")
    st.markdown(f"""
    - **Platform**: {platform.system()}
    - **Next scrape**: Next 24 hours
    - **Stealth mode**: Always active
    - **Output formats**: CSV & JSON
    - **Sports covered**: 6+ leagues
    """)

    if st.session_state.last_scrape_time:
        st.markdown(
            f"**Last run**: {st.session_state.last_scrape_time.strftime('%Y-%m-%d %H:%M:%S')}")

    st.markdown("---")
    st.markdown("## 🚀 Quick Actions")

    if st.button("🔄 Refresh Page"):
        st.rerun()

    if st.button("🗑️ Clear Data"):
        st.session_state.scraped_data = None
        st.session_state.last_scrape_time = None
        st.session_state.last_error = None
        st.success("Data cleared!")
        st.rerun()

    if st.button("🧪 Force Test Mode"):
        st.session_state.scraped_data = generate_sample_data()
        st.session_state.last_scrape_time = datetime.now()
        st.success("Sample data generated!")
        st.rerun()

# Auto-refresh logic
if auto_refresh and st.session_state.last_scrape_time:
    time_diff = datetime.now() - st.session_state.last_scrape_time
    if time_diff.total_seconds() > 1800:  # 30 minutes
        st.rerun()