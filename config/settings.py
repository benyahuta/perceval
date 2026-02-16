"""
OpenClaw Duke - Configuration Settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM Configuration ---
# Set LLM_PROVIDER to "openai" or "anthropic"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# --- Telegram Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# --- Scraping Schedule (in minutes) ---
SCRAPE_INTERVAL_MINUTES = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "60"))

# --- Database ---
DB_PATH = os.getenv("DB_PATH", "data/openclaw_duke.db")

# --- Instagram Accounts to Monitor ---
INSTAGRAM_ACCOUNTS = [
    "dukeinnovation",         # Duke Innovation & Entrepreneurship (Duke I&E)
    "dukeventure",            # Duke Venture Group (DVG)
    "dukeappliedml",          # Duke Applied Machine Learning (DAML)
    "dukecapitalpartners",    # Duke Capital Partners
    "hackduke",               # HackDuke
]

# --- Websites to Scrape ---
DUKE_WEBSITES = [
    {
        "name": "Duke I&E Events",
        "url": "https://cie.duke.edu/events",
        "type": "events_page",
    },
    {
        "name": "Duke Innovation & Entrepreneurship",
        "url": "https://entrepreneurship.duke.edu/events/",
        "type": "events_page",
    },
    {
        "name": "Fuqua Events",
        "url": "https://www.fuqua.duke.edu/events",
        "type": "events_page",
    },
    {
        "name": "Duke Engineering Events",
        "url": "https://pratt.duke.edu/events/",
        "type": "events_page",
    },
]

# --- External Competition Sources ---
EXTERNAL_SOURCES = [
    {
        "name": "Devpost Hackathons",
        "url": "https://devpost.com/hackathons?status[]=upcoming&status[]=open",
        "type": "hackathons",
    },
    {
        "name": "Major League Hacking",
        "url": "https://mlh.io/seasons/2026/events",
        "type": "hackathons",
    },
    {
        "name": "Eventbrite Pitch Competitions",
        "url": "https://www.eventbrite.com/d/online/pitch-competition/",
        "type": "pitch_competitions",
    },
]

# --- Event Categories to Track ---
RELEVANT_KEYWORDS = [
    "startup", "pitch", "venture", "entrepreneurship", "entrepreneur",
    "innovation", "hackathon", "case competition", "trading", "finance",
    "business", "investing", "investor", "VC", "venture capital",
    "founder", "accelerator", "incubator", "demo day", "speaker",
    "networking", "career", "tech", "AI", "machine learning",
    "competition", "challenge", "fellowship", "grant", "funding",
]

# --- Phone number (for reference, Telegram is primary) ---
USER_PHONE = "+12489151065"
