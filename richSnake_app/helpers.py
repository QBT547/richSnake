import hashlib
import hmac
from urllib.parse import unquote

import requests

BOT_TOKEN = "7942185037:AAGHRARwj9S388Im3LZLsjrm4wj2a7bqno8"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def validate_init_data(init_data: str, bot_token: str):
    vals = {k: unquote(v) for k, v in [s.split('=', 1)
                                       for s in init_data.split('&')]}
    data_check_string = '\n'.join(
        f"{k}={v}" for k, v in sorted(vals.items()) if k != 'hash')

    secret_key = hmac.new("WebAppData".encode(),
                          bot_token.encode(), hashlib.sha256).digest()
    h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256)
    return h.hexdigest() == vals['hash']


def get_telegram_user_photo(telegram_id):
    """Fetches the Telegram user's avatar photo URL."""
    try:
        response = requests.get(f"{TELEGRAM_API_URL}/getUserProfilePhotos", params={
            "user_id": telegram_id,
            "limit": 1  # Fetch only the first photo
        })
        data = response.json()

        if data.get("ok") and data["result"]["total_count"] > 0:
            # Get the file ID of the user's photo
            file_id = data["result"]["photos"][0][0]["file_id"]

            # Request the file path using the file ID
            file_response = requests.get(
                f"{TELEGRAM_API_URL}/getFile", params={"file_id": file_id})
            file_data = file_response.json()

            if file_data.get("ok"):
                # Construct the file URL
                file_path = file_data["result"]["file_path"]
                return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

    except requests.RequestException:
        # Handle request failure (e.g., network issues)
        pass

    return None  # Return None if no photo is found or if an error occurs