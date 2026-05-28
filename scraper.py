# scraper.py
# AUTOMATION layer — drives Chrome to the website and orchestrates the scraping.
# The actual extraction logic lives in extractor.py
#
# nodriver is the official successor of undetected-chromedriver.
# It communicates directly via Chrome DevTools Protocol (CDP) — no Selenium,
# no chromedriver binary needed. It is fully async, so we wrap it for Streamlit.

import asyncio
import json
import sys
import os
import time

import nodriver as uc

from extractor import EXTRACT_JS, validate_result, clean_result


# ---------------------------------------------------------------------------
# Public sync entry-point (called by app.py / Streamlit)
# ---------------------------------------------------------------------------

def get_profile_data(username: str, headless: bool = False) -> dict:
    """
    Synchronous wrapper so that Streamlit can call the async scraper directly.
    Raises on failure — the caller (app.py) handles displaying the error.
    """
    return uc.loop().run_until_complete(_scrape(username, headless))


def save_to_json(data: dict, filepath: str = "info.JSON"):
    """Save scraped data to a JSON file next to this script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, filepath)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"[scraper] Saved to {full_path}")


# ---------------------------------------------------------------------------
# Async implementation
# ---------------------------------------------------------------------------

async def _scrape(username: str, headless: bool) -> dict:
    """
    Full scraping pipeline using nodriver:
    1. Start Chrome (patched to evade bot detection)
    2. Navigate to the NotJustAnalytics profile page
    3. Handle any Cloudflare challenge (cf_verify)
    4. Wait for the data section to render
    5. Inject extraction JS and collect the result
    6. Validate, clean, and return
    """
    print(f"[scraper] Launching Chrome for @{username}...")

    browser = await uc.start(
        headless=headless,
        browser_args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--window-size=1920,1080",
            "--disable-blink-features=AutomationControlled",
        ],
    )

    try:
        url = f"https://app.notjustanalytics.com/analysis/{username}"
        print(f"[scraper] Navigating to {url}")
        tab = await browser.get(url)

        # ── Step 1: attempt Cloudflare bypass ─────────────────────────────
        # nodriver has a built-in helper that detects and clicks the CF checkbox
        print("[scraper] Attempting Cloudflare bypass...")
        try:
            await tab.cf_verify()
            print("[scraper] Cloudflare check passed (or not present).")
        except Exception as cf_err:
            print(f"[scraper] cf_verify skipped/failed: {cf_err}")
            # Not fatal — the page may not have a CF challenge

        # ── Step 2: wait for actual data to appear ─────────────────────────
        print("[scraper] Waiting for analytics data to load...")
        loaded = await _wait_for_data(tab, timeout=40)

        if not loaded:
            # Dump page text to help debug what blocked us
            try:
                body = await tab.evaluate("document.body.innerText || ''")
                preview = (body or "")[:500].replace("\n", " ")
                print(f"[scraper] Page text preview (500 chars): {preview}")
            except Exception:
                pass
            raise RuntimeError(
                "Timed out waiting for analytics data. "
                "The page may still be behind a Cloudflare challenge, "
                "or the username doesn't exist on NotJustAnalytics."
            )

        # ── Step 3: extract metrics via JS ─────────────────────────────────
        print("[scraper] Extracting metrics via JavaScript...")
        result = await tab.evaluate(EXTRACT_JS)

        # result from tab.evaluate() can be None if the JS returned undefined
        if not isinstance(result, dict):
            raise RuntimeError(
                f"JS extractor returned unexpected type: {type(result).__name__} "
                f"(value={result!r}). The page structure may have changed."
            )

        if not validate_result(result):
            # Retry once with a short extra wait for late-loading numbers
            print("[scraper] Metrics look empty — waiting 6s and retrying...")
            await asyncio.sleep(6)
            result = await tab.evaluate(EXTRACT_JS)

            if not isinstance(result, dict) or not validate_result(result):
                raise RuntimeError(
                    "Extracted data has zero followers after retry. "
                    "The profile may be private, or the page layout has changed."
                )

        result = clean_result(result, username)
        print(f"[scraper] Done! Extracted data for @{username}: {result}")
        return result

    except Exception as e:
        print(f"[scraper] Error: {e}")
        raise

    finally:
        browser.stop()
        print("[scraper] Browser closed.")


async def _wait_for_data(tab, timeout: int = 40) -> bool:
    """
    Poll the page body until 'Followers' and 'Avg' appear, confirming the
    analytics section has rendered.

    Returns True if data was found, False if the timeout was reached.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            body_text = await tab.evaluate("document.body.innerText || ''")
            if isinstance(body_text, str):
                # Check for analytics data keywords
                if "Followers" in body_text and "Avg" in body_text:
                    await asyncio.sleep(1.5)  # brief wait for late-loading numbers
                    return True
                # Detect still-loading states so we can log them
                if "Checking" in body_text or "Just a moment" in body_text:
                    print("[scraper] Cloudflare challenge page detected, waiting...")
                elif "Page not found" in body_text or "404" in body_text:
                    raise RuntimeError(
                        f"Profile not found on NotJustAnalytics. "
                        "Make sure the username is correct."
                    )
        except RuntimeError:
            raise  # re-raise our own specific errors
        except Exception:
            pass  # CDP hiccup — retry next tick

        await asyncio.sleep(1.5)

    return False  # timed out


# ---------------------------------------------------------------------------
# Run standalone: python scraper.py <username>
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "raahavy_"
    print(f"\n{'='*50}")
    print(f"  Scraping @{target} from NotJustAnalytics")
    print(f"{'='*50}\n")

    data = get_profile_data(target)

    if validate_result(data):
        save_to_json(data)
        print("\n--- Result ---")
        print(json.dumps(data, indent=4))
    else:
        print("\n[scraper] Failed to extract data.")
        sys.exit(1)
