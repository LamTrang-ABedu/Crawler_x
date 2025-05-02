from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

COOKIE_URL = "https://r2.lam.io.vn/cookies/x_cookies.txt"

def load_filtered_cookies():
    try:
        resp = requests.get(COOKIE_URL)
        lines = resp.text.splitlines()
        cookies = {}
        for line in lines:
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 7:
                domain = parts[0]
                name = parts[5]
                value = parts[6]
                if "twitter.com" in domain or ".x.com" in domain:
                    cookies[name] = value
        return cookies
    except Exception as e:
        print("Error loading cookies:", e)
        return {}

def extract_username(cookies):
    headers = {
        "x-csrf-token": cookies.get("ct0", ""),
        "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAvE9gkZ%2FvZTXXkjlIoCkZK1Jz8Ys%3DfdnQvwXnK2HFgFeKu4J96T0PuYJr4QLw3T3LmR8qy0wMTA4odw",
    }
    try:
        r = requests.get("https://twitter.com/settings/account", headers=headers, cookies=cookies)
        if r.ok and 'screen_name":"' in r.text:
            return r.text.split('screen_name":"')[1].split('"')[0]
    except Exception as e:
        print("Username extract failed:", e)
    return None

def get_follow_data(kind, username, cookies):
    headers = {
        "accept": "application/json",
        "x-csrf-token": cookies.get("ct0", ""),
        "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAvE9gkZ%2FvZTXXkjlIoCkZK1Jz8Ys%3DfdnQvwXnK2HFgFeKu4J96T0PuYJr4QLw3T3LmR8qy0wMTA4odw",
    }
    if kind == "followers":
        api_url = "https://twitter.com/i/api/graphql/44t_YZ5pV4oBpfw9t_A5NQ/Followers"
    else:
        api_url = "https://twitter.com/i/api/graphql/Me7zG49R0Jy7NYZzYcSPXw/Following"

    variables = {
        "userId": None,
        "screenName": username,
        "count": 100
    }

    try:
        resp = requests.get(
            api_url,
            headers=headers,
            cookies=cookies,
            params={"variables": str(variables).replace("'", '"')}
        )
        return resp.text
    except Exception as e:
        return f"Request error: {e}"

@app.route("/api/followers")
def api_followers():
    cookies = load_filtered_cookies()
    username = request.args.get("username") or extract_username(cookies)
    if not username:
        return jsonify({"status": "error", "message": "Could not determine username from cookies"})
    result = get_follow_data("followers", username, cookies)
    return jsonify({"status": "ok", "data": result})

@app.route("/api/following")
def api_following():
    cookies = load_filtered_cookies()
    username = request.args.get("username") or extract_username(cookies)
    if not username:
        return jsonify({"status": "error", "message": "Could not determine username from cookies"})
    result = get_follow_data("following", username, cookies)
    return jsonify({"status": "ok", "data": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)