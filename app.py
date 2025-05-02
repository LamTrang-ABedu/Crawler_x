
from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

def scrape_user_list(username: str, mode: str):
    if mode not in ['followers', 'following']:
        return []

    try:
        result = subprocess.run(
            ["snscrape", f"--jsonl", f"--{mode}", username],
            capture_output=True,
            text=True,
            check=True
        )
        users = []
        for line in result.stdout.strip().split("\n"):
            data = json.loads(line)
            users.append(data.get("username"))
        return users
    except subprocess.CalledProcessError as e:
        return {"error": f"Scrape failed: {e.stderr}"}

@app.route("/api/followers")
def get_followers():
    username = request.args.get("username")
    if not username:
        return jsonify({"status": "error", "message": "Missing ?username="})
    data = scrape_user_list(username, "followers")
    return jsonify({"status": "ok", "data": data})

@app.route("/api/following")
def get_following():
    username = request.args.get("username")
    if not username:
        return jsonify({"status": "error", "message": "Missing ?username="})
    data = scrape_user_list(username, "following")
    return jsonify({"status": "ok", "data": data})

@app.route("/")
def index():
    return "Twitter/X Follow Service (via snscrape)"
