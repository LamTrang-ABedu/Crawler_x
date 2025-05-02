from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

def run_snscrape(username, limit=20):
    cmd = [
        'snscrape',
        '--jsonl',
        f'--max-results={limit}',
        f'twitter-user "{username}"'
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        media_posts = []

        for line in lines:
            tweet = json.loads(line)
            medias = tweet.get("media", [])
            if medias:
                media_posts.append({
                    "url": f"https://twitter.com/{tweet['user']['username']}/status/{tweet['id']}",
                    "content": tweet.get("content", ""),
                    "date": tweet.get("date", ""),
                    "media": medias
                })
        return media_posts
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@app.route('/api/x-media', methods=['GET'])
def get_media():
    username = request.args.get('username')
    if not username:
        return jsonify({"status": "error", "message": "Missing ?username="})
    
    data = run_snscrape(username)
    return jsonify({"status": "ok", "data": data})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)