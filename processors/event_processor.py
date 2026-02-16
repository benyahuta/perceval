"""
LLM-based event processor.
Takes raw scraped text and uses an LLM to determine if it's a relevant event
and extract structured information.
"""
import json
import logging
from typing import Dict, Optional
from config.settings import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
    OPENAI_MODEL,
    ANTHROPIC_MODEL,
    RELEVANT_KEYWORDS,
)

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are an event extraction assistant. Analyze the following text scraped from {source} and determine if it describes an upcoming event related to startups, tech, business, finance, entrepreneurship, hackathons, pitch competitions, case competitions, trading competitions, or career opportunities.

If it IS a relevant upcoming event, extract the details and return JSON:
{{
    "is_event": true,
    "title": "Event title",
    "description": "Brief 1-2 sentence description",
    "event_date": "Date/time if found (any format), or 'TBD'",
    "location": "Location if found, or 'TBD'",
    "category": "one of: speaker, pitch_competition, hackathon, case_competition, trading_competition, networking, workshop, career_fair, info_session, other",
    "relevance_score": 1-10 (10 = extremely relevant to a Duke student interested in startups/tech/business)
}}

If it is NOT a relevant event (e.g., just general content, old event, unrelated), return:
{{
    "is_event": false,
    "reason": "brief reason why"
}}

IMPORTANT:
- Only flag UPCOMING or currently-open events/competitions
- For external sources, only flag competitions (pitch, hackathon, case, trading)
- Be generous with relevance - if it might interest a Duke student in business/tech, include it
- Return ONLY valid JSON, nothing else

Text to analyze:
---
{text}
---"""


def process_raw_content(raw_item: Dict) -> Optional[Dict]:
    """
    Process a raw scraped item through the LLM to extract event info.
    Returns structured event dict or None if not relevant.
    """
    source = raw_item.get("source", "unknown")
    text = raw_item.get("raw_text", "")

    if not text or len(text) < 20:
        return None

    # Quick keyword pre-filter to save API calls
    text_lower = text.lower()
    has_keyword = any(kw.lower() in text_lower for kw in RELEVANT_KEYWORDS)
    if not has_keyword and raw_item.get("type") not in ("hackathons", "pitch_competitions"):
        logger.debug(f"Skipping item from {source} - no relevant keywords")
        return None

    prompt = EXTRACTION_PROMPT.format(source=source, text=text[:1500])

    try:
        result = _call_llm(prompt)
        if not result:
            return None

        parsed = json.loads(result)

        if not parsed.get("is_event", False):
            return None

        if parsed.get("relevance_score", 0) < 4:
            return None

        # Merge with raw item data
        event = {
            "source": source,
            "source_id": raw_item.get("source_id", ""),
            "title": parsed.get("title", "Unknown Event"),
            "description": parsed.get("description", ""),
            "event_date": parsed.get("event_date", "TBD"),
            "location": parsed.get("location", "TBD"),
            "url": raw_item.get("url", ""),
            "category": parsed.get("category", "other"),
            "relevance_score": parsed.get("relevance_score", 5),
            "raw_text": text[:500],
        }
        return event

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"LLM processing error: {e}")
        return None


def _call_llm(prompt: str) -> Optional[str]:
    """Call the configured LLM provider."""
    if LLM_PROVIDER == "anthropic":
        return _call_anthropic(prompt)
    else:
        return _call_openai(prompt)


def _call_openai(prompt: str) -> Optional[str]:
    """Call OpenAI API."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You extract event information from text. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None


def _call_anthropic(prompt: str) -> Optional[str]:
    """Call Anthropic API."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Anthropic API error: {e}")
        return None
