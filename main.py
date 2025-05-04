from flask import Flask, request, jsonify
from crawler import crawl_user_media

app = Flask(__name__)

@app.route('/crawl', methods=['POST'])
def crawl():
    data = request.get_json()
    username = data.get("username")
    callback = data.get("callback")

    if not username:
        return jsonify({"error": "Missing username"}), 400

    try:
        crawl_user_media(username, callback)
        return jsonify({"status": "Crawling started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
