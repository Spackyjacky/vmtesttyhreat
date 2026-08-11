import argparse
import os

import yaml
from dotenv import load_dotenv

from .ebay_client import EbayClient
from .facebook_scraper import scrape_facebook_marketplace
from .models import Listing
from .storage import get_recent, init_db, upsert_listings

FB_STORAGE_STATE = os.path.join(os.path.dirname(__file__), "..", "data", "fb_storage_state.json")


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def run_ebay(cfg: dict) -> list:
    client_id = os.environ.get("EBAY_CLIENT_ID")
    client_secret = os.environ.get("EBAY_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("EBAY_CLIENT_ID / EBAY_CLIENT_SECRET not set — skipping eBay (see .env.example).")
        return []

    client = EbayClient(client_id, client_secret, cfg["ebay"].get("marketplace_id", "EBAY_GB"))
    accepted_locations = cfg["location"].get("ebay_accepted_locations", [])
    listings = []

    for term in cfg["search_terms"]:
        items = client.search(
            term,
            price_min=cfg["price"].get("min"),
            price_max=cfg["price"].get("max"),
            category_ids=cfg["ebay"].get("category_ids") or None,
        )
        for item in items:
            loc = item.get("itemLocation", {}) or {}
            city = loc.get("city", "") or ""
            postal = loc.get("postalCode", "") or ""
            if accepted_locations and not any(
                a.lower() in city.lower() or postal.upper().startswith(a.upper())
                for a in accepted_locations
            ):
                continue

            price = item.get("price", {}) or {}
            listings.append(
                Listing(
                    source="ebay",
                    external_id=item["itemId"],
                    title=item.get("title", ""),
                    price=float(price["value"]) if price.get("value") else None,
                    currency=price.get("currency", "GBP"),
                    url=item.get("itemWebUrl", ""),
                    location=f"{city} {postal}".strip(),
                    image_url=(item.get("image") or {}).get("imageUrl"),
                    search_term=term,
                )
            )
    return listings


def run_facebook(cfg: dict) -> list:
    if not os.path.exists(FB_STORAGE_STATE):
        print("No saved Facebook session found. Run `python scripts/fb_login.py` first "
              "— skipping Facebook Marketplace.")
        return []

    raw = scrape_facebook_marketplace(
        storage_state_path=FB_STORAGE_STATE,
        search_terms=cfg["search_terms"],
        max_scrolls=cfg["facebook"].get("max_scrolls", 6),
        headless=cfg["facebook"].get("headless", True),
        delay_between_terms=cfg["facebook"].get("delay_seconds_between_terms", 8),
    )

    price_min = cfg["price"].get("min")
    price_max = cfg["price"].get("max")
    listings = []
    for r in raw:
        if r["price"] is not None:
            if price_min is not None and r["price"] < price_min:
                continue
            if price_max is not None and r["price"] > price_max:
                continue
        listings.append(Listing(**r))
    return listings


def main():
    parser = argparse.ArgumentParser(description="Furniture sourcing: eBay + Facebook Marketplace")
    parser.add_argument("command", choices=["run", "report"])
    parser.add_argument("--source", choices=["ebay", "facebook", "all"], default="all")
    parser.add_argument("--config", default=os.path.join(os.path.dirname(__file__), "..", "config.yaml"))
    parser.add_argument("--db", default=os.path.join(os.path.dirname(__file__), "..", "data", "listings.db"))
    args = parser.parse_args()

    load_dotenv()
    os.makedirs(os.path.dirname(args.db), exist_ok=True)
    conn = init_db(args.db)

    if args.command == "report":
        for l in get_recent(conn, limit=50):
            price = f"£{l['price']:.2f}" if l["price"] is not None else "?"
            print(f"[{l['source']}] {l['title']} - {price} - {l['location']} - {l['url']}")
        return

    cfg = load_config(args.config)
    listings = []
    if args.source in ("ebay", "all"):
        print("Searching eBay...")
        listings += run_ebay(cfg)
    if args.source in ("facebook", "all"):
        print("Searching Facebook Marketplace...")
        listings += run_facebook(cfg)

    new_listings = upsert_listings(conn, listings)
    print(f"\nFound {len(listings)} total, {len(new_listings)} new:")
    for l in new_listings:
        price = f"£{l.price:.2f}" if l.price is not None else "?"
        print(f"  [{l.source}] {l.title} - {price} - {l.location} - {l.url}")


if __name__ == "__main__":
    main()
