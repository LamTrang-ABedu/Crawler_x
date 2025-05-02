from fastapi import FastAPI, Query
from utils.cookie_helper import load_twitter_cookies, get_username_from_cookies, call_api
import uvicorn

app = FastAPI()

@app.get("/api/following")
async def get_following(username: str = Query(None)):
    cookies = load_twitter_cookies()
    if not cookies:
        return {"status": "error", "message": "Missing valid cookies"}

    user = username or get_username_from_cookies(cookies)
    if not user:
        return {"status": "error", "message": "Could not determine username from cookies"}

    data = call_api(user, cookies, kind="following")
    return {"status": "ok", "data": data}

@app.get("/api/followers")
async def get_followers(username: str = Query(None)):
    cookies = load_twitter_cookies()
    if not cookies:
        return {"status": "error", "message": "Missing valid cookies"}

    user = username or get_username_from_cookies(cookies)
    if not user:
        return {"status": "error", "message": "Could not determine username from cookies"}

    data = call_api(user, cookies, kind="followers")
    return {"status": "ok", "data": data}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10002)