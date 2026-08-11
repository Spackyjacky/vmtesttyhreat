# Furniture Sourcing

Finds furniture stock (pine drawers, sideboards, sofas, etc.) in and around
Cardiff by searching eBay and Facebook Marketplace, and keeps a local
database so it only surfaces items you haven't seen yet.

- **eBay** — uses eBay's official Browse API. Fully compliant, no risk.
- **Facebook Marketplace** — has no public API. This drives a real browser
  with your own logged-in session to run searches. **This is against
  Facebook's Terms of Service** and carries a real risk of your account
  being rate-limited, checkpointed, or suspended. Read the "Facebook risk"
  section below before using it.

## Setup

```bash
cd furniture-sourcing
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

### eBay API keys

1. Create a free account at https://developer.ebay.com
2. Go to **My Account > Application Keys** and create a keyset.
3. Use the **Production** Client ID and Client Secret (not Sandbox).
4. Put them in `.env`:
   ```
   EBAY_CLIENT_ID=...
   EBAY_CLIENT_SECRET=...
   ```

No further eBay setup needed — the client handles OAuth token requests
itself using the client-credentials flow.

### Facebook session

```bash
python scripts/fb_login.py
```

This opens a real browser window. Log in with your own account, then in
that same browser go to Marketplace and set your location to **Cardiff**
(Facebook remembers this per-account and it's what "local" results are
based on). Press Enter in the terminal once done — your session is saved to
`data/fb_storage_state.json` and reused on future runs so you don't have to
log in again. Re-run this script whenever Facebook logs the saved session
out.

## Usage

```bash
# search both sources, print + store only new listings
python -m src.main run

# just one source
python -m src.main run --source ebay
python -m src.main run --source facebook

# show recently stored listings without searching again
python -m src.main report
```

Search terms, price range, and location matching are configured in
`config.yaml`.

To run it periodically, add a cron entry, e.g. every 2 hours:

```
0 */2 * * * cd /path/to/furniture-sourcing && venv/bin/python -m src.main run >> run.log 2>&1
```

## Facebook risk — read before using

- There is no official Marketplace API. This tool automates a normal
  browser using your logged-in session, functionally the same as you
  clicking around manually, but at machine speed and on a schedule. Doing
  this is a violation of Facebook's Terms of Service, and Facebook has
  taken both technical (rate limiting, checkpoints) and legal action
  against scrapers in the past.
- Realistic consequences range from nothing, to a login checkpoint /
  CAPTCHA, to temporary rate-limiting, to account suspension. There's no
  way to make this fully safe — using your own primary account carries the
  most risk if it gets flagged.
- To reduce (not eliminate) risk: don't lower `delay_seconds_between_terms`
  much below the default, don't run more often than every couple of hours,
  and don't add extra search terms far beyond what you actually need.
- If Facebook shows a security checkpoint or CAPTCHA in the saved session,
  don't try to script around it — run `scripts/fb_login.py` again and
  resolve it manually in the browser.
- Facebook's HTML/class names are auto-generated and change periodically,
  so `src/facebook_scraper.py`'s text-parsing heuristics may need updates
  if listings stop being extracted correctly (titles/prices are parsed
  from the visible text of each listing card — check that logic first).

## Notes on eBay location filtering

eBay's Browse API doesn't offer a clean "radius from postcode" search like
their website does. This tool searches all of GB by keyword and then
filters client-side by matching each item's returned city/postcode against
`location.ebay_accepted_locations` in `config.yaml`. Widen or narrow that
list to trade off coverage vs. relevance.

## Data

Listings are stored in `data/listings.db` (SQLite), keyed by source +
listing ID, so repeated runs only report genuinely new stock. Delete the
file to reset. `data/` is gitignored, as is `.env`.
