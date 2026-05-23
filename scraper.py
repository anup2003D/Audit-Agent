# scraper.py
# AUTOMATION layer — drives Chrome to the website and orchestrates the scraping
# The actual extraction logic lives in extractor.py
#
# Think of it like this:
#   scraper.py   = the driver (Selenium — opens browser, navigates, waits)
#   extractor.py = the reader (JavaScript — parses the page, extracts numbers)

import undetected_chromedriver as uc
import time
import json
import sys
import os

from extractor import EXTRACT_JS, validate_result, clean_result


def get_profile_data(username: str, headless: bool = False) -> dict:
    """
    Scrape an Instagram profile from NotJustAnalytics.

    This function handles the AUTOMATION side:
    1. Launch Chrome (with anti-detection patches)
    2. Navigate to the profile page
    3. Wait for data to load
    4. Call the extraction logic from extractor.py
    5. Return the clean result

    Args:
        username: Instagram username (without @)
        headless: If True, run Chrome without a visible window.
                  Default False because Cloudflare blocks headless more often.

    Returns:
        dict matching the format that llm/client.py expects
    """
    print(f"[scraper] Launching Chrome for @{username}...")

    options = uc.ChromeOptions()


    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    # undetected-chromedriver patches Chrome so Cloudflare thinks
    # it's a real human browser, not a Selenium bot
    # version_main must match your installed Chrome version (check chrome://version)
    driver = uc.Chrome(options=options, version_main=148)

    try:
        url = f"https://app.notjustanalytics.com/analysis/{username}"
        print(f"[scraper] Navigating to {url}")
        driver.get(url)

        # --- Wait for data to load ---
        print("[scraper] Waiting for page to load (Cloudflare + data)...")
        _wait_for_data(driver, timeout=20)

        # --- Inject JS from extractor.py and get the result ---
        print("[scraper] Extracting metrics via JavaScript...")
        result = driver.execute_script(EXTRACT_JS)

        if not validate_result(result):
            # Data didn't load — try waiting a bit more and retry
            print("[scraper] No data found, retrying after extra wait...")
            time.sleep(5)
            result = driver.execute_script(EXTRACT_JS)

        # Clean and validate the result
        result = clean_result(result, username)

        print(f"[scraper] Done! Extracted data for @{username}")
        return result

    except Exception as e:
        print(f"[scraper] Error: {e}")
        raise

    finally:
        driver.quit()
        print("[scraper] Browser closed.")


def _wait_for_data(driver, timeout: int = 20):
    """
    Wait until the page text contains 'Followers' — meaning the data
    section has rendered (not just the loading skeleton).
    Falls back to proceeding anyway if the check times out.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            body_text = driver.execute_script("return document.body.innerText || '';")
            # Check if the main data labels have appeared
            if "Followers" in body_text and "Avg" in body_text:
                # Give it 1 more second for any late-loading numbers
                time.sleep(1)
                return
        except Exception:
            pass
        time.sleep(1)

    # If we get here, the timeout was reached — proceed anyway
    print(f"[scraper] Warning: Timed out after {timeout}s waiting for data to load")


def save_to_json(data: dict, filepath: str = "info.JSON"):
    """Save scraped data to a JSON file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, filepath)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"[scraper] Saved to {full_path}")


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
        print(f"\n--- Result ---")
        print(json.dumps(data, indent=4))
    else:
        print("\n[scraper] Failed to extract data.")
        sys.exit(1)
