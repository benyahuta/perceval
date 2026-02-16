"""
Instagram scraper for OpenClaw Duke.
Uses multiple fallback methods to get recent posts from public Instagram accounts.
"""
import re
import json
import hashlib
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Common headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


def scrape_instagram_account(username: str) -> List[Dict]:
    """
    Attempt to scrape recent posts from an Instagram account.
    Tries multiple methods with fallbacks.
    """
    posts = []

    # Method 1: Try fetching via the public JSON endpoint
    posts = _try_public_json(username)
    if posts:
        return posts

    # Method 2: Try fetching via the embed endpoint
    posts = _try_embed_endpoint(username)
    if posts:
        return posts

    # Method 3: Try fetching from web profile page
    posts = _try_web_scrape(username)
    if posts:
        return posts

    logger.warning(f"All Instagram scraping methods failed for @{username}")
    return []


def _try_public_json(username: str) -> List[Dict]:
    """Try the public ?__a=1&__d=dis endpoint."""
    try:
        url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            user_data = data.get("graphql", {}).get("user", {})
            edges = (
                user_data.get("edge_owner_to_timeline_media", {}).get("edges", [])
            )
            posts = []
            for edge in edges[:12]:  # Last 12 posts
                node = edge.get("node", {})
                caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                caption = (
                    caption_edges[0]["node"]["text"] if caption_edges else ""
                )
                posts.append({
                    "id": node.get("shortcode", ""),
                    "caption": caption,
                    "timestamp": node.get("taken_at_timestamp", 0),
                    "url": f"https://www.instagram.com/p/{node.get('shortcode', '')}/",
                    "image_url": node.get("display_url", ""),
                })
            return posts
    except Exception as e:
        logger.debug(f"Public JSON method failed for @{username}: {e}")
    return []


def _try_embed_endpoint(username: str) -> List[Dict]:
    """Try fetching from the embed/oembed endpoint for recent content."""
    try:
        # This won't give us a feed, but can confirm account exists
        url = f"https://www.instagram.com/{username}/embed/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            html = resp.text
            # Extract post data from embed HTML
            posts = _parse_embed_html(html, username)
            return posts
    except Exception as e:
        logger.debug(f"Embed method failed for @{username}: {e}")
    return []


def _try_web_scrape(username: str) -> List[Dict]:
    """Try scraping the public web profile page."""
    try:
        url = f"https://www.instagram.com/{username}/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            html = resp.text
            # Look for shared data in the page
            pattern = r'window\._sharedData\s*=\s*({.*?});</script>'
            match = re.search(pattern, html)
            if match:
                data = json.loads(match.group(1))
                user = (
                    data.get("entry_data", {})
                    .get("ProfilePage", [{}])[0]
                    .get("graphql", {})
                    .get("user", {})
                )
                edges = (
                    user.get("edge_owner_to_timeline_media", {}).get("edges", [])
                )
                posts = []
                for edge in edges[:12]:
                    node = edge["node"]
                    caption_edges = node.get("edge_media_to_caption", {}).get(
                        "edges", []
                    )
                    caption = (
                        caption_edges[0]["node"]["text"] if caption_edges else ""
                    )
                    posts.append({
                        "id": node.get("shortcode", ""),
                        "caption": caption,
                        "timestamp": node.get("taken_at_timestamp", 0),
                        "url": f"https://www.instagram.com/p/{node.get('shortcode', '')}/",
                        "image_url": node.get("display_url", ""),
                    })
                return posts
    except Exception as e:
        logger.debug(f"Web scrape method failed for @{username}: {e}")
    return []


def _parse_embed_html(html: str, username: str) -> List[Dict]:
    """Parse Instagram embed HTML for post content."""
    posts = []
    try:
        # Find caption text in embed
        caption_pattern = r'class="Caption"[^>]*>(.*?)</div>'
        captions = re.findall(caption_pattern, html, re.DOTALL)

        # Find shortcodes/links
        link_pattern = r'instagram\.com/p/([A-Za-z0-9_-]+)'
        shortcodes = re.findall(link_pattern, html)

        for i, shortcode in enumerate(set(shortcodes)):
            caption = captions[i] if i < len(captions) else ""
            # Clean HTML from caption
            caption = re.sub(r"<[^>]+>", "", caption).strip()
            posts.append({
                "id": shortcode,
                "caption": caption,
                "timestamp": 0,
                "url": f"https://www.instagram.com/p/{shortcode}/",
                "image_url": "",
            })
    except Exception as e:
        logger.debug(f"Embed HTML parsing failed: {e}")
    return posts


def generate_post_id(username: str, caption: str) -> str:
    """Generate a stable ID from username + caption for dedup."""
    content = f"{username}:{caption[:200]}"
    return hashlib.md5(content.encode()).hexdigest()
