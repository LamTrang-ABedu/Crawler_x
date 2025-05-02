from flask import Flask, request, jsonify
import requests
import os
import re

app = Flask(__name__)

COOKIE_URL = "https://r2.lam.io.vn/cookies/x_cookies.txt"
COOKIE_PATH = "/tmp/x_cookies.txt"

def filter_essential_cookies(cookie_txt):
    allowed_keys = {'auth_token', 'ct0', 'guest_id', 'kdt', 'twid'}
    result = []
    for line in cookie_txt.splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        parts = line.split('\t')
        if len(parts) == 7 and parts[5] in allowed_keys:
            result.append('\t'.join(parts))
    return '\n'.join(result)

def load_filtered_cookie_file():
    if not os.path.exists(COOKIE_PATH):
        resp = requests.get(COOKIE_URL)
        if resp.ok:
            filtered = filter_essential_cookies(resp.text)
            with open(COOKIE_PATH, 'w', encoding='utf-8') as f:
                f.write(filtered)

def parse_cookies_to_dict():
    cookies = {}
    with open(COOKIE_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.strip().split('\t')
            if len(parts) == 7:
                cookies[parts[5]] = parts[6]
    return cookies

def get_logged_in_username(headers, cookies):
    res = requests.get("https://twitter.com/settings/account", headers=headers, cookies=cookies)
    if res.ok:
        match = re.search(r'"screen_name":"(.*?)"', res.text)
        if match:
            return match.group(1)
    return None

def fetch_friends(username, mode='following'):
    endpoint = 'friends/list.json' if mode == 'following' else 'followers/list.json'
    url = f"https://api.twitter.com/1.1/{endpoint}?screen_name={username}&count=200"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAt%2Ff4Gz..."
    }

    cookies = parse_cookies_to_dict()
    res = requests.get(url, headers=headers, cookies=cookies)

    if res.status_code == 200:
        users = res.json().get('users', [])
        return [{"username": u["screen_name"], "name": u["name"], "bio": u["description"]} for u in users]
    else:
        return {"error": f"{res.status_code} - {res.text}"}

@app.route('/')
def home():
    return 'X Follow Service is running.'

@app.route('/api/following')
def api_following():
    load_filtered_cookie_file()
    username = request.args.get("username")
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAt%2Ff4Gz..."
    }
    cookies = parse_cookies_to_dict()
    if not username:
        username = get_logged_in_username(headers, cookies)
        if not username:
            return jsonify({"status": "error", "message": "Could not determine username from cookies"}), 400
    data = fetch_friends(username, mode='following')
    return jsonify({"status": "ok", "data": data})

@app.route('/api/followers')
def api_followers():
    load_filtered_cookie_file()
    username = request.args.get("username")
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAt%2Ff4Gz..."
    }
    cookies = parse_cookies_to_dict()
    if not username:
        username = get_logged_in_username(headers, cookies)
        if not username:
            return jsonify({"status": "error", "message": "Could not determine username from cookies"}), 400
    data = fetch_friends(username, mode='followers')
    return jsonify({"status": "ok", "data": data})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
