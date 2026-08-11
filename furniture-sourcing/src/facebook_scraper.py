"""
Facebook Marketplace has no public API. This module drives a real browser
(via Playwright) using YOUR OWN logged-in session to run searches, the same
way a person browsing manually would. This is against Facebook's Terms of
Service and carries a real risk of your account being flagged, rate-limited,
or suspended — see the README before running this.

Because there's no API, listings are extracted with DOM/text heuristics
(Facebook's HTML class names are auto-generated and change often), so this
is more brittle than the eBay integration and may need selector updates
over time.
"""

import re
import time
from typing import List, Optional
from urllib.parse import quote

from playwright.sync_api import sync_playwright

MARKETPLACE_SEARCH_URL = "https://www.facebook.com/marketplace/search/?query={query}"
ITEM_HREF_SELECTOR = 'a[href*="/marketplace/item/"]'
PRICE_PATTERN = re.compile(r"£\s?[\d,]+(?:\.\d+)?")
ITEM_ID_PATTERN = re.compile(r"/marketplace/item/(\d+)")


def scrape_facebook_marketplace(
    storage_state_path: str,
    search_terms: List[str],
    max_scrolls: int = 6,
    headless: bool = True,
    delay_between_terms: float = 8.0,
) -> List[dict]:
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(storage_state=storage_state_path)
        page = context.new_page()

        for term in search_terms:
            url = MARKETPLACE_SEARCH_URL.format(query=quote(term))
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

            for _ in range(max_scrolls):
                page.mouse.wheel(0, 3000)
                page.wait_for_timeout(1500)

            anchors = page.query_selector_all(ITEM_HREF_SELECTOR)
            seen_hrefs = set()
            for anchor in anchors:
                href = anchor.get_attribute("href")
                if not href or href in seen_hrefs:
                    continue
                seen_hrefs.add(href)
                item = _parse_listing(anchor.inner_text(), href, term)
                if item:
                    results.append(item)

            time.sleep(delay_between_terms)

        context.close()
        browser.close()
    return results


def _parse_listing(text: str, href: str, search_term: str) -> Optional[dict]:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return None

    price_line = next((l for l in lines if PRICE_PATTERN.match(l)), None)
    price_value = None
    if price_line:
        digits = re.sub(r"[^\d.]", "", price_line)
        try:
            price_value = float(digits)
        except ValueError:
            price_value = None

    non_price_lines = [l for l in lines if not PRICE_PATTERN.match(l)]
    title = max(non_price_lines, key=len) if non_price_lines else "Unknown"
    location = lines[-1] if len(lines) >= 2 and lines[-1] != title else None

    id_match = ITEM_ID_PATTERN.search(href)
    external_id = id_match.group(1) if id_match else href
    full_url = href if href.startswith("http") else f"https://www.facebook.com{href}"

    return {
        "source": "facebook",
        "external_id": external_id,
        "title": title,
        "price": price_value,
        "currency": "GBP",
        "url": full_url,
        "location": location,
        "image_url": None,
        "search_term": search_term,
    }
