"""
Telegram notification system for Perceval.
Sends formatted event notifications via Telegram bot.
"""
import logging
import requests
from typing import Dict
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

CATEGORY_EMOJI = {
    "speaker": "🎤",
    "pitch_competition": "🚀",
    "hackathon": "💻",
    "case_competition": "📊",
    "trading_competition": "📈",
    "networking": "🤝",
    "workshop": "🔧",
    "career_fair": "💼",
    "info_session": "ℹ️",
    "other": "📌",
}


def send_event_notification(event: Dict) -> bool:
    """Send a formatted event notification via Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram bot token or chat ID not configured!")
        return False

    emoji = CATEGORY_EMOJI.get(event.get("category", "other"), "📌")
    category_display = event.get("category", "other").replace("_", " ").title()

    message = f"""{emoji} *New Event Alert\\!*

*{_escape_md(event.get('title', 'Unknown Event'))}*

📂 {category_display}
📍 {_escape_md(event.get('location', 'TBD'))}
📅 {_escape_md(event.get('event_date', 'TBD'))}
🔗 Source: {_escape_md(event.get('source', 'Unknown'))}

{_escape_md(event.get('description', ''))}

{event.get('url', '')}"""

    return _send_telegram_message(message)


def send_daily_digest(events: list) -> bool:
    """Send a daily digest of events."""
    if not events:
        return True

    message = f"📋 *Daily Event Digest* — {len(events)} new events found\\!\n\n"

    for i, event in enumerate(events, 1):
        emoji = CATEGORY_EMOJI.get(event.get("category", "other"), "📌")
        message += (
            f"{i}\\. {emoji} *{_escape_md(event.get('title', 'Unknown'))}*\n"
            f"   📅 {_escape_md(event.get('event_date', 'TBD'))} "
            f"| 📍 {_escape_md(event.get('location', 'TBD'))}\n\n"
        )

    return _send_telegram_message(message)


def send_status_message(message: str) -> bool:
    """Send a plain status message."""
    return _send_telegram_message(f"🤖 Perceval: {_escape_md(message)}")


def _send_telegram_message(text: str) -> bool:
    """Send a message via the Telegram Bot API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": False,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info("Telegram message sent successfully")
            return True
        else:
            # Retry without markdown if formatting fails
            logger.warning(f"Telegram send failed with markdown: {resp.text}")
            payload["parse_mode"] = ""
            payload["text"] = text.replace("*", "").replace("\\", "")
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                return True
            logger.error(f"Telegram send failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Telegram send error: {e}")
        return False


def _escape_md(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    if not text:
        return ""
    special_chars = ['_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text


def get_chat_id_helper():
    """
    Helper to find your Telegram chat ID.
    Run this after messaging your bot, and it'll print the chat ID.
    """
    if not TELEGRAM_BOT_TOKEN:
        print("Set TELEGRAM_BOT_TOKEN first!")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    resp = requests.get(url, timeout=10)
    data = resp.json()

    if data.get("result"):
        for update in data["result"]:
            chat = update.get("message", {}).get("chat", {})
            if chat:
                print(f"Chat ID: {chat['id']}")
                print(f"Name: {chat.get('first_name', '')} {chat.get('last_name', '')}")
                print(f"Username: {chat.get('username', '')}")
    else:
        print("No messages found. Send a message to your bot first!")


if __name__ == "__main__":
    get_chat_id_helper()
