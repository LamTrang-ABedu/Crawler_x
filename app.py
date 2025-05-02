from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

COOKIE_URL = "https://r2.lam.io.vn/cookies/x_cookies.txt"

def load_cookies():
    raw = requests.get(COOKIE_URL).text
    cookies = {}
    for line in raw.splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        parts = line.strip().split('\t')
        if len(parts) >= 7:
            cookies[parts[5]] = parts[6]
    return cookies

def fetch_friends(user, mode='following'):
    endpoint = 'friends/list.json' if mode == 'following' else 'followers/list.json'
    url = f"https://api.twitter.com/1.1/{endpoint}?screen_name={user}&count=200"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAt%2Ff4Gz..."
    }

    cookies = load_cookies()

    res = requests.get(url, headers=headers, cookies=cookies)

    if res.status_code == 200:
        users = res.json().get('users', [])
        return [{"username": u["screen_name"], "name": u["name"], "bio": u["description"]} for u in users]
    else:
        return {"error": f"{res.status_code} - {res.text}"}

@app.route('/')
def index():
    return 'X Follow Service is running.'

@app.route('/api/following')
def api_following():
    username = request.args.get("username")
    if not username:
        return jsonify({"status": "error", "message": "Missing username"}), 400
    data = fetch_friends(username, mode='following')
    return jsonify({"status": "ok", "data": data})

@app.route('/api/followers')
def api_followers():
    username = request.args.get("username")
    if not username:
        return jsonify({"status": "error", "message": "Missing username"}), 400
    data = fetch_friends(username, mode='followers')
    return jsonify({"status": "ok", "data": data})

if __name__ == '__main__':
    app.run(debug=True)
