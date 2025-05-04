import json, os, time, requests, sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
import boto3
from dotenv import load_dotenv
load_dotenv()

COOKIES_URL = "https://r2.lam.io.vn/cookies/x_cookies.txt"
OUTPUT_FILE = "x_media.json"

R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID')
R2_BUCKET_NAME = 'hopehub-storage'

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY')
    )
def download_cookies():
    res = requests.get(COOKIES_URL)
    raw = res.text.strip().splitlines()
    cookies = []
    for line in raw:
        if line.startswith('#') or not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) >= 7:
            domain = parts[0].lstrip(".")
            if "x.com" in domain:
                cookies.append({
                    "domain": domain,
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
    print("[Init] Opening https://x.com/ to prepare cookie domain...")
    driver.get("https://x.com/")
    time.sleep(3)  # Cho phép load hoàn toàn context

    current_domain = urlparse(driver.current_url).hostname
    print(f"[Cookie] Current domain: {current_domain}")

    for cookie in cookies:
        try:
            cookie_domain = cookie['domain'].lstrip(".")
            if cookie_domain != current_domain:
                continue  # bỏ qua nếu cookie domain không khớp
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"Skipping cookie {cookie.get('name')}: {e}")

def scroll_and_collect(driver, max_scroll=30, delay=2):
    media_items = []
    seen_urls = set()

    for _ in range(max_scroll):
        cards = driver.find_elements(By.CSS_SELECTOR, 'article')

        for card in cards:
            try:
                tweet_url = None
                links = card.find_elements(By.TAG_NAME, "a")
                for l in links:
                    href = l.get_attribute("href")
                    if href and "/status/" in href:
                        tweet_url = "https://x.com" + href if href.startswith("/") else href
                        break

                # Lấy ảnh
                imgs = card.find_elements(By.CSS_SELECTOR, "img[alt='Image']")
                for img in imgs:
                    src = img.get_attribute("src")
                    if src and src not in seen_urls:
                        print(f"[IMG] {src}")
                        media_items.append({
                            "type": "image",
                            "url": src,
                            "post_url": tweet_url
                        })
                        seen_urls.add(src)

                # Lấy video
                videos = card.find_elements(By.CSS_SELECTOR, "video")
                for v in videos:
                    poster = v.get_attribute("poster")
                    if poster and poster not in seen_urls:
                        print(f"[VID] {tweet_url}")
                        media_items.append({
                            "type": "video",
                            "thumbnail": poster,
                            "post_url": tweet_url
                        })
                        seen_urls.add(poster)

            except Exception as e:
                print(f"[ERR] Failed to parse card: {e}")
                continue

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay)

    return media_items

def upload_to_r2(media):
    try:
        r2_client = get_s3_client()
        key = "MEDIA/x_media.json"

        # Tải dữ liệu cũ nếu có
        try:
            old_obj = r2_client.get_object(Bucket=R2_BUCKET_NAME, Key=key)
            old_media = json.load(old_obj['Body'])
        except:
            old_media = []

        # Merge và loại bỏ trùng lặp theo 'url'
        all_media = {m.get("url") or m.get("thumbnail"): m for m in old_media + media}
        merged = list(all_media.values())

        # Ghi lại
        r2_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=key,
            Body=json.dumps(merged, indent=2).encode('utf-8'),
            ContentType='application/json'
        )
        print(f"[Upload] Successfully merged and uploaded x_media.json")

    except Exception as e:
        print(f"[Upload] Failed to upload to R2: {e}")

def crawl_x_media(username):
    cookies = download_cookies()
    driver = setup_driver()
    inject_cookies(driver, cookies)
    target_url = f"https://x.com/{username}"
    print("Loading:", target_url)
    driver.get(target_url)
    time.sleep(3)

    media = scroll_and_collect(driver, max_scroll=40)
    driver.quit()

    print(f"Collected {len(media)} media items.")

    upload_to_r2(media)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python app.py <twitter_username>")
        sys.exit(1)
    crawl_x_media(sys.argv[1])
