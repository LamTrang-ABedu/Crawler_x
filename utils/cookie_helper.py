import requests

def extract_cookies_from_txt(url):
    response = requests.get(url)
    content = response.text
    cookies = {}
    for line in content.splitlines():
        if not line.startswith("#") and "\t" in line:
            parts = line.strip().split("\t")
            if len(parts) >= 7:
                name = parts[5]
                value = parts[6]
                cookies[name] = value
    return cookies

def extract_username_from_cookies(cookies: dict) -> str | None:
    twid = cookies.get("twid")
    if twid and twid.startswith("u="):
        return twid[2:]
    return None