from flask import Flask, request, jsonify
from utils.twitter_cookies import extract_cookies_from_txt, extract_username_from_cookies
from x_follow import get_followers, get_following

app = Flask(__name__)

COOKIE_URL = "https://r2.lam.io.vn/cookies/x_cookies.txt"

@app.route("/api/followers")
def followers():
    username = request.args.get("username")
    try:
        cookies = extract_cookies_from_txt(COOKIE_URL)
        if not username:
            username = extract_username_from_cookies(cookies)
            if not username:
                return jsonify({"status": "error", "message": "Could not determine username from cookies"})
        data = get_followers(username, cookies)
        return jsonify({"status": "ok", "data": data})
    except Exception as e:
        return jsonify({"status": "ok", "data": str(e)})

@app.route("/api/following")
def following():
    username = request.args.get("username")
    try:
        cookies = extract_cookies_from_txt(COOKIE_URL)
        if not username:
            username = extract_username_from_cookies(cookies)
            if not username:
                return jsonify({"status": "error", "message": "Could not determine username from cookies"})
        data = get_following(username, cookies)
        return jsonify({"status": "ok", "data": data})
    except Exception as e:
        return jsonify({"status": "ok", "data": str(e)})

@app.route("/api/me")
def me():
    try:
        cookies = extract_cookies_from_txt(COOKIE_URL)
        username = extract_username_from_cookies(cookies)
        if username:
            return jsonify({"status": "ok", "username": username})
        return jsonify({"status": "error", "message": "Could not extract username from cookies"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)