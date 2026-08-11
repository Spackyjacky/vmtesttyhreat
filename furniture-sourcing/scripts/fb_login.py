"""
One-time interactive login: opens a real (headed) browser window so you can
log into Facebook yourself and set your Marketplace location to Cardiff.
The session is then saved to data/fb_storage_state.json and reused by the
scraper so it doesn't need your password and doesn't log in again each run.

Run this again whenever Facebook logs the saved session out (expected
occasionally — e.g. after a security checkpoint).
"""

import os

from playwright.sync_api import sync_playwright

STORAGE_STATE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "fb_storage_state.json"
)


def main():
    os.makedirs(os.path.dirname(STORAGE_STATE_PATH), exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.facebook.com/login")

        print("1. Log in to Facebook in the opened browser window.")
        print("2. Go to Marketplace and set your location to Cardiff (this is")
        print("   remembered per-account and controls what 'local' results show).")
        input("Press Enter here once you've done both steps... ")

        context.storage_state(path=STORAGE_STATE_PATH)
        print(f"Saved session to {STORAGE_STATE_PATH}")
        browser.close()


if __name__ == "__main__":
    main()
