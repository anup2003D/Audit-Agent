# scraper.py
# AUTOMATION layer — drives Chrome to the website and orchestrates the scraping.
# The actual extraction logic lives in extractor.py
#
# Uses undetected-chromedriver — a patched Selenium ChromeDriver that evades
# bot detection (Cloudflare, etc.) automatically.  Fully synchronous.

import json
import sys
import os
import time
import platform

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

from extractor import EXTRACT_JS, validate_result, clean_result


# ---------------------------------------------------------------------------
# Chrome version detection (prevents ChromeDriver mismatch)
# ---------------------------------------------------------------------------

def _detect_chrome_version() -> int | None:
    """
    Auto-detect the installed Chrome major version.
    Returns an int like 148, or None if detection fails.
    """
    if platform.system() == "Windows":
        import winreg
        # Try HKCU first (per-user install), then HKLM (system-wide)
        for hive, subkey in [
            (winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Google\Chrome\BLBeacon"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Google\Chrome\BLBeacon"),
        ]:
            try:
                key = winreg.OpenKey(hive, subkey)
                version, _ = winreg.QueryValueEx(key, "version")
                winreg.CloseKey(key)
                major = int(version.split(".")[0])
                print(f"[scraper] Detected Chrome version: {version} (major={major})")
                return major
            except (FileNotFoundError, OSError, ValueError):
                continue
    else:
        # macOS / Linux — try shell
        import subprocess
        for cmd in ["google-chrome --version", "chromium --version"]:
            try:
                out = subprocess.check_output(cmd, shell=True, text=True).strip()
                major = int(out.split()[-1].split(".")[0])
                print(f"[scraper] Detected Chrome version: {out} (major={major})")
                return major
            except Exception:
                continue

    print("[scraper] Could not auto-detect Chrome version, letting UC decide.")
    return None


# ---------------------------------------------------------------------------
# Public entry-point (called by app.py / Streamlit)
# ---------------------------------------------------------------------------

def get_profile_data(username: str, headless: bool = False) -> dict:
    """
    Scrape the NotJustAnalytics profile page for the given Instagram username.
    Returns a dict of metrics.  Raises on failure — the caller (app.py)
    handles displaying the error.
    """
    return _scrape(username, headless)


def save_to_json(data: dict, filepath: str = "info.JSON"):
    """Save scraped data to a JSON file next to this script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, filepath)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"[scraper] Saved to {full_path}")


# ---------------------------------------------------------------------------
# Implementation
# ---------------------------------------------------------------------------

def _scrape(username: str, headless: bool) -> dict:
    """
    Full scraping pipeline using undetected-chromedriver:
    1. Start a patched Chrome (evades bot detection automatically)
    2. Navigate to the NotJustAnalytics profile page
    3. Wait for the data section to render (Cloudflare is handled passively)
    4. Inject extraction JS and collect the result
    5. Validate, clean, and return
    """
    print(f"[scraper] Launching Chrome for @{username}...")

    chrome_ver = _detect_chrome_version()

    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    if headless:
        options.add_argument("--headless=new")

    driver = uc.Chrome(options=options, version_main=chrome_ver)

    try:
        url = f"https://app.notjustanalytics.com/analysis/{username}"
        print(f"[scraper] Navigating to {url}")
        driver.get(url)

        # ── Step 1: wait for actual data to appear ─────────────────────────
        # undetected-chromedriver handles Cloudflare passively — its patched
        # binary avoids triggering the challenge in most cases.  We just need
        # to wait for the analytics content to render.
        print("[scraper] Waiting for analytics data to load...")
        loaded = _wait_for_data(driver, timeout=45)

        if not loaded:
            # Dump page text to help debug what blocked us
            try:
                body = driver.execute_script("return document.body.innerText || '';")
                preview = (body or "")[:500].replace("\n", " ")
                print(f"[scraper] Page text preview (500 chars): {preview}")
            except Exception:
                pass
            raise RuntimeError(
                "Timed out waiting for analytics data. "
                "The page may still be behind a Cloudflare challenge, "
                "or the username doesn't exist on NotJustAnalytics."
            )

        # ── Step 2: extract metrics via JS ─────────────────────────────────
        print("[scraper] Extracting metrics via JavaScript...")
        result = driver.execute_script(EXTRACT_JS)

        # execute_script returns None if the JS returned undefined
        if not isinstance(result, dict):
            raise RuntimeError(
                f"JS extractor returned unexpected type: {type(result).__name__} "
                f"(value={result!r}). The page structure may have changed."
            )

        if not validate_result(result):
            # Retry once with a short extra wait for late-loading numbers
            print("[scraper] Metrics look empty — waiting 6s and retrying...")
            time.sleep(6)
            result = driver.execute_script(EXTRACT_JS)

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
        driver.quit()
        print("[scraper] Browser closed.")


def _wait_for_data(driver, timeout: int = 45) -> bool:
    """
    Poll the page body until 'Followers' and 'Avg' appear, confirming the
    analytics section has rendered.

    Returns True if data was found, False if the timeout was reached.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            body_text = driver.execute_script("return document.body.innerText || '';")
            if isinstance(body_text, str):
                # Check for analytics data keywords
                if "Followers" in body_text and "Avg" in body_text:
                    time.sleep(1.5)  # brief wait for late-loading numbers
                    return True
                # Detect still-loading states so we can log them
                if "Checking" in body_text or "Just a moment" in body_text:
                    print("[scraper] Cloudflare challenge page detected, waiting...")
                elif "Page not found" in body_text or "404" in body_text:
                    raise RuntimeError(
                        "Profile not found on NotJustAnalytics. "
                        "Make sure the username is correct."
                    )
        except RuntimeError:
            raise  # re-raise our own specific errors
        except Exception:
            pass  # WebDriver hiccup — retry next tick

        time.sleep(1.5)

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
