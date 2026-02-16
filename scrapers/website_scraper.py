"""
Website scraper for Duke event pages and external competition sources.
"""
import hashlib
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from config.settings import DUKE_WEBSITES, EXTERNAL_SOURCES

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def scrape_duke_websites() -> List[Dict]:
    """Scrape all configured Duke event websites."""
    all_events = []
    for site in DUKE_WEBSITES:
        try:
            events = _scrape_website(site)
            all_events.extend(events)
            logger.info(f"Scraped {len(events)} items from {site['name']}")
        except Exception as e:
            logger.error(f"Failed to scrape {site['name']}: {e}")
    return all_events


def scrape_external_sources() -> List[Dict]:
    """Scrape external competition sources."""
    all_events = []
    for site in EXTERNAL_SOURCES:
        try:
            events = _scrape_website(site)
            all_events.extend(events)
            logger.info(f"Scraped {len(events)} items from {site['name']}")
        except Exception as e:
            logger.error(f"Failed to scrape {site['name']}: {e}")
    return all_events


def _scrape_website(site: Dict) -> List[Dict]:
    """Scrape a single website and return raw content items."""
    resp = requests.get(site["url"], headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    items = []

    # Strategy 1: Look for event-like containers
    # Common patterns: articles, event cards, list items with dates
    event_containers = _find_event_containers(soup)

    if event_containers:
        for container in event_containers:
            text = container.get_text(separator=" ", strip=True)
            if len(text) < 20:
                continue

            # Try to find a link
            link = container.find("a", href=True)
            url = ""
            if link:
                href = link["href"]
                if href.startswith("/"):
                    # Make absolute URL
                    from urllib.parse import urljoin
                    url = urljoin(site["url"], href)
                elif href.startswith("http"):
                    url = href

            items.append({
                "source": site["name"],
                "source_id": _generate_id(site["name"], text),
                "raw_text": text[:2000],
                "url": url or site["url"],
                "type": site.get("type", "events_page"),
            })
    else:
        # Fallback: get the main content as one block
        main = soup.find("main") or soup.find("article") or soup.find("body")
        if main:
            text = main.get_text(separator="\n", strip=True)
            # Split into chunks around event-like boundaries
            chunks = _split_into_chunks(text)
            for chunk in chunks:
                if len(chunk.strip()) < 30:
                    continue
                items.append({
                    "source": site["name"],
                    "source_id": _generate_id(site["name"], chunk),
                    "raw_text": chunk[:2000],
                    "url": site["url"],
                    "type": site.get("type", "events_page"),
                })

    return items


def _find_event_containers(soup: BeautifulSoup) -> list:
    """Find likely event containers in the HTML."""
    containers = []

    # Look for common event listing patterns
    selectors = [
        "article",
        "[class*='event']",
        "[class*='Event']",
        "[class*='card']",
        "[class*='Card']",
        "[class*='listing']",
        ".views-row",
        ".event-item",
        ".event-listing",
        "li[class*='event']",
        "[data-event]",
        ".node--type-event",
    ]

    for selector in selectors:
        found = soup.select(selector)
        if found and len(found) >= 2:
            containers.extend(found)
            break

    # Deduplicate by checking if containers are nested
    if not containers:
        # Try looking for repeated structures
        for tag in ["div", "li", "article", "section"]:
            elements = soup.find_all(tag, recursive=True)
            # Group by class
            class_groups = {}
            for el in elements:
                classes = " ".join(el.get("class", []))
                if classes and len(el.get_text(strip=True)) > 30:
                    class_groups.setdefault(classes, []).append(el)

            for cls, group in class_groups.items():
                if 3 <= len(group) <= 50:
                    containers = group
                    break
            if containers:
                break

    return containers[:30]


def _split_into_chunks(text: str, max_chunk: int = 500) -> List[str]:
    """Split text into reasonable chunks for event detection."""
    lines = text.split("\n")
    chunks = []
    current = []
    current_len = 0

    for line in lines:
        line = line.strip()
        if not line:
            if current:
                chunks.append("\n".join(current))
                current = []
                current_len = 0
            continue

        current.append(line)
        current_len += len(line)

        if current_len >= max_chunk:
            chunks.append("\n".join(current))
            current = []
            current_len = 0

    if current:
        chunks.append("\n".join(current))

    return chunks


def _generate_id(source: str, text: str) -> str:
    """Generate a stable ID for dedup."""
    content = f"{source}:{text[:200]}"
    return hashlib.md5(content.encode()).hexdigest()


def scrape_devpost() -> List[Dict]:
    """Specialized scraper for Devpost hackathons."""
    url = "https://devpost.com/api/hackathons?status[]=upcoming&status[]=open"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            hackathons = data.get("hackathons", [])
            items = []
            for h in hackathons[:20]:
                items.append({
                    "source": "Devpost",
                    "source_id": f"devpost_{h.get('id', '')}",
                    "raw_text": f"{h.get('title', '')} - {h.get('tagline', '')}. "
                               f"Submission period: {h.get('submission_period_dates', '')}. "
                               f"Prizes: {h.get('prize_amount', 'N/A')}",
                    "url": h.get("url", ""),
                    "type": "hackathons",
                    "title": h.get("title", ""),
                    "event_date": h.get("submission_period_dates", ""),
                })
            return items
    except Exception as e:
        logger.error(f"Devpost scrape failed: {e}")
    return []


def scrape_mlh() -> List[Dict]:
    """Specialized scraper for MLH hackathons."""
    url = "https://mlh.io/seasons/2026/events"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        events = soup.select(".event-wrapper") or soup.select("[class*='event']")
        items = []
        for event in events[:20]:
            text = event.get_text(separator=" ", strip=True)
            link = event.find("a", href=True)
            url_str = link["href"] if link else ""
            items.append({
                "source": "MLH",
                "source_id": _generate_id("MLH", text),
                "raw_text": text[:1000],
                "url": url_str,
                "type": "hackathons",
            })
        return items
    except Exception as e:
        logger.error(f"MLH scrape failed: {e}")
    return []
