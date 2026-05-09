import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time, random

def get_profile_data(username: str) -> dict:
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    
    driver = uc.Chrome(options=options)
    try:
        url = f"https://app.notjustanalytics.com/analysis/i_am_anupdutta"
        driver.get(url)
        time.sleep(random.uniform(3, 6))  # Human-like delay
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # Extract metrics from the rendered HTML
        # (You'll need to inspect the actual page to find CSS selectors)
        return parse_metrics(soup)
    finally:
        driver.quit()
