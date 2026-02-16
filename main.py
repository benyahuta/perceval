"""
OpenClaw Duke - Main Orchestrator
Coordinates scraping, processing, and notification pipeline.
"""
import time
import logging
import schedule
from datetime import datetime

from config.settings import (
    INSTAGRAM_ACCOUNTS,
    SCRAPE_INTERVAL_MINUTES,
    LLM_PROVIDER,
)
from scrapers.instagram_scraper import scrape_instagram_account, generate_post_id
from scrapers.website_scraper import (
    scrape_duke_websites,
    scrape_external_sources,
    scrape_devpost,
    scrape_mlh,
)
from processors.event_processor import process_raw_content
from data.database import save_event, log_scrape, event_exists
from notifiers.telegram_notifier import send_event_notification, send_status_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("openclaw_duke.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("openclaw-duke")


def run_pipeline():
    """Run the full scraping -> processing -> notification pipeline."""
    logger.info("=" * 60)
    logger.info(f"Starting OpenClaw Duke pipeline at {datetime.now()}")
    logger.info(f"Using LLM provider: {LLM_PROVIDER}")
    logger.info("=" * 60)

    new_events = []

    # --- Phase 1: Scrape Instagram accounts ---
    logger.info("Phase 1: Scraping Instagram accounts...")
    for account in INSTAGRAM_ACCOUNTS:
        try:
            posts = scrape_instagram_account(account)
            logger.info(f"  @{account}: found {len(posts)} posts")
            log_scrape(f"instagram:{account}", "success", f"{len(posts)} posts")

            for post in posts:
                post_id = post.get("id") or generate_post_id(account, post.get("caption", ""))

                if event_exists(f"instagram:{account}", post_id):
                    continue

                raw_item = {
                    "source": f"Instagram @{account}",
                    "source_id": post_id,
                    "raw_text": post.get("caption", ""),
                    "url": post.get("url", ""),
                    "type": "instagram",
                }

                event = process_raw_content(raw_item)
                if event:
                    event["source_id"] = post_id
                    event["source"] = f"instagram:{account}"
                    if save_event(event):
                        new_events.append(event)
                        logger.info(f"  ✓ New event: {event['title']}")

        except Exception as e:
            logger.error(f"  ✗ Error scraping @{account}: {e}")
            log_scrape(f"instagram:{account}", "error", str(e))

    # --- Phase 2: Scrape Duke websites ---
    logger.info("Phase 2: Scraping Duke websites...")
    try:
        website_items = scrape_duke_websites()
        logger.info(f"  Found {len(website_items)} raw items from Duke websites")
        log_scrape("duke_websites", "success", f"{len(website_items)} items")

        for item in website_items:
            if event_exists(item["source"], item["source_id"]):
                continue

            event = process_raw_content(item)
            if event:
                if save_event(event):
                    new_events.append(event)
                    logger.info(f"  ✓ New event: {event['title']}")

    except Exception as e:
        logger.error(f"  ✗ Error scraping Duke websites: {e}")
        log_scrape("duke_websites", "error", str(e))

    # --- Phase 3: Scrape external sources ---
    logger.info("Phase 3: Scraping external competition sources...")

    # Devpost
    try:
        devpost_items = scrape_devpost()
        logger.info(f"  Devpost: {len(devpost_items)} hackathons")
        for item in devpost_items:
            if event_exists(item["source"], item["source_id"]):
                continue
            event = process_raw_content(item)
            if event:
                if save_event(event):
                    new_events.append(event)
                    logger.info(f"  ✓ New hackathon: {event['title']}")
    except Exception as e:
        logger.error(f"  ✗ Devpost error: {e}")

    # MLH
    try:
        mlh_items = scrape_mlh()
        logger.info(f"  MLH: {len(mlh_items)} events")
        for item in mlh_items:
            if event_exists(item["source"], item["source_id"]):
                continue
            event = process_raw_content(item)
            if event:
                if save_event(event):
                    new_events.append(event)
                    logger.info(f"  ✓ New hackathon: {event['title']}")
    except Exception as e:
        logger.error(f"  ✗ MLH error: {e}")

    # General external sources
    try:
        external_items = scrape_external_sources()
        logger.info(f"  External: {len(external_items)} raw items")
        for item in external_items:
            if event_exists(item["source"], item["source_id"]):
                continue
            event = process_raw_content(item)
            if event:
                if save_event(event):
                    new_events.append(event)
                    logger.info(f"  ✓ New competition: {event['title']}")
    except Exception as e:
        logger.error(f"  ✗ External sources error: {e}")

    # --- Phase 4: Send notifications ---
    logger.info(f"Phase 4: Sending {len(new_events)} notifications...")
    for event in new_events:
        try:
            send_event_notification(event)
            time.sleep(1)  # Rate limit Telegram
        except Exception as e:
            logger.error(f"  ✗ Failed to notify about {event['title']}: {e}")

    logger.info(f"Pipeline complete. {len(new_events)} new events found and notified.")
    logger.info("=" * 60)

    return new_events


def run_scheduled():
    """Run the pipeline on a schedule."""
    logger.info(f"OpenClaw Duke starting with {SCRAPE_INTERVAL_MINUTES}-minute interval")
    send_status_message(f"OpenClaw Duke is online\\! Checking every {SCRAPE_INTERVAL_MINUTES} minutes\\.")

    # Run immediately on start
    run_pipeline()

    # Schedule recurring runs
    schedule.every(SCRAPE_INTERVAL_MINUTES).minutes.do(run_pipeline)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run once and exit (useful for testing)
        run_pipeline()
    else:
        # Run on schedule
        run_scheduled()
