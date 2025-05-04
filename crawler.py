import time
import json
import requests

def crawl_user_media(username, callback=None):
    print(f"[Crawler] Crawling media for {username}...")

    # Giả lập crawl dữ liệu
    time.sleep(3)
    result = {"username": username, "media": [{"type": "image", "url": "https://example.com/image.jpg"}]}

    # Gửi callback nếu có
    if callback:
        try:
            requests.post(callback, json={"status": "finished", "result": result})
        except Exception as e:
            print(f"[Callback Error] {e}")
    else:
        print(f"[Done] Crawling for {username} complete.")
