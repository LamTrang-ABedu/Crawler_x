import json, os, time, requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
import boto3
from dotenv import load_dotenv

COOKIES_URL = "https://r2.lam.io.vn/cookies/x_cookies.txt"
TARGET_URL = "https://x.com/xingyinxiaoyi/media"
OUTPUT_FILE = "x_media.json"

def download_cookies():
    res = requests.get(COOKIES_URL)
    raw = res.text.strip().splitlines()
    cookies = []
    for line in raw:
        if line.startswith('#') or not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) >= 7:
            cookies.append({
                "domain": parts[0],
                "name": parts[5],
                "value": parts[6],
                "path": parts[2],
                "secure": parts[3].lower() == 'true',
            })
    return cookies

def setup_driver():
    options = Options()
    options.headless = True
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def inject_cookies(driver, cookies):
    driver.get("https://x.com/")
    for cookie in cookies:
        if cookie['domain'].startswith("."):
            cookie['domain'] = cookie['domain'][1:]
        driver.add_cookie(cookie)

def scroll_and_collect(driver, max_scroll=30, delay=2):
    media_items = []
    seen_urls = set()
    for _ in range(max_scroll):
        cards = driver.find_elements(By.CSS_SELECTOR, 'article')
        for card in cards:
            try:
                imgs = card.find_elements(By.CSS_SELECTOR, "img")
                links = card.find_elements(By.TAG_NAME, "a")
                tweet_url = None
                for l in links:
                    href = l.get_attribute("href")
                    if href and "/status/" in href:
                        tweet_url = href
                        break
                for img in imgs:
                    src = img.get_attribute("src")
                    if src and "media" in src and src not in seen_urls:
                        media_items.append({
                            "title": "Tweet by @xingyinxiaoyi",
                            "thumb": src,
                            "video": None,
                            "source": tweet_url
                        })
                        seen_urls.add(src)
            except:
                continue
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay)
    return media_items

def upload_to_r2(file_path, key_path):
    load_dotenv()
    access_key = os.getenv("R2_ACCESS_KEY")
    secret_key = os.getenv("R2_SECRET_KEY")
    endpoint = os.getenv("R2_ENDPOINT")
    bucket = os.getenv("R2_BUCKET")

    session = boto3.session.Session()
    s3 = session.client('s3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

    with open(file_path, 'rb') as f:
        s3.put_object(Bucket=bucket, Key=key_path, Body=f, ContentType='application/json')
        print(f"[OK] Uploaded to R2 → MEDIA/{key_path}")

def crawl_x_media():
    cookies = download_cookies()
    driver = setup_driver()
    inject_cookies(driver, cookies)
    print("Loading target page...")
    driver.get(TARGET_URL)
    time.sleep(3)

    media = scroll_and_collect(driver, max_scroll=40)
    driver.quit()

    print(f"Collected {len(media)} media items.")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(media, f, indent=2, ensure_ascii=False)
    print(f"Saved to {OUTPUT_FILE}")

    upload_to_r2(OUTPUT_FILE, "MEDIA/x_media.json")

if __name__ == "__main__":
    crawl_x_media()
