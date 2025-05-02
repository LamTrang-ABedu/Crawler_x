import requests
import http.cookies
import os

COOKIE_URL = "https://r2.lam.io.vn/cookies/x_cookies.txt"
COOKIE_PATH = "/tmp/x_cookies.txt"

def download_cookiefile():
    if not os.path.exists(COOKIE_PATH):
        r = requests.get(COOKIE_URL)
        if r.ok:
            with open(COOKIE_PATH, "wb") as f:
                f.write(r.content)

def parse_netscape_cookies(path):
    cookies = {}
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            if not line.startswith("#") and "	" in line:
                parts = line.strip().split("	")
                if len(parts) >= 7:
                    domain, _, path, secure, expires, name, value = parts
                    cookies[name] = value
    return cookies

def load_twitter_cookies():
    download_cookiefile()
    cookies = parse_netscape_cookies(COOKIE_PATH)
    if 'auth_token' in cookies and 'ct0' in cookies:
        return cookies
    return None

def get_username_from_cookies(cookies):
    twid = cookies.get("twid")
    if twid and twid.startswith("u="):
        return twid[2:]
    return None

def call_api(username, cookies, kind="following"):
    headers = {
        "Authorization": f"Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAA...",
        "x-csrf-token": cookies["ct0"],
        "Cookie": "; ".join([f"{k}={v}" for k, v in cookies.items()])
    }

    url = f"https://api.twitter.com/1.1/friends/list.json?screen_name={username}&count=200"
    if kind == "followers":
        url = f"https://api.twitter.com/1.1/followers/list.json?screen_name={username}&count=200"

    resp = requests.get(url, headers=headers)
    return resp.json() if resp.ok else f"{resp.status_code} - {resp.text}"