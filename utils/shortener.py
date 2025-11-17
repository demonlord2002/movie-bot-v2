# utils/shortener.py
import os
import requests
from dotenv import load_dotenv

load_dotenv("config.env")
XTG_API = os.getenv("XTG_API")  # set this in config.env

def short_it(url: str) -> str:
    """Return shortened url using XTG API. On failure returns original url."""
    try:
        if not XTG_API:
            return url
        # craft API request for text response (short link only)
        api = f"https://xtglinks.com/api?api={XTG_API}&url={requests.utils.requote_uri(url)}&format=text"
        r = requests.get(api, timeout=10)
        if r.status_code == 200 and r.text.strip():
            return r.text.strip()
        # fallback: try json response
        api2 = f"https://xtglinks.com/api?api={XTG_API}&url={requests.utils.requote_uri(url)}"
        r2 = requests.get(api2, timeout=10)
        if r2.status_code == 200:
            j = r2.json()
            if j.get("status") == "success" and j.get("shortenedUrl"):
                return j.get("shortenedUrl")
    except Exception:
        pass
    return url
