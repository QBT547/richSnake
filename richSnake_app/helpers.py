import hashlib
import hmac
from urllib.parse import unquote
from django.conf import settings
from richSnake_app.models import Payment

import requests

def validate_init_data(init_data: str, bot_token: str):
    vals = {k: unquote(v) for k, v in [s.split('=', 1)
                                       for s in init_data.split('&')]}
    data_check_string = '\n'.join(
        f"{k}={v}" for k, v in sorted(vals.items()) if k != 'hash')

    secret_key = hmac.new("WebAppData".encode(),
                          bot_token.encode(), hashlib.sha256).digest()
    h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256)
    return h.hexdigest() == vals['hash']


def get_telegram_user_photo(telegram_id, bot_token):
    """Fetches the Telegram user's avatar photo URL."""
    try:

        TELEGRAM_API_URL = f"https://api.telegram.org/bot{bot_token}"
        # Step 1: Request user's profile photos
        response = requests.get(f"{TELEGRAM_API_URL}/getUserProfilePhotos", params={
            "user_id": telegram_id,
            "limit": 1  # Fetch only the first photo
        })
        response.raise_for_status()  # Raises HTTPError for bad responses

        # Parse JSON response
        data = response.json()
        if data.get("ok") and data["result"]["total_count"] > 0:
            # Get the file ID of the user's photo
            file_id = data["result"]["photos"][0][0]["file_id"]

            # Step 2: Request the file path using the file ID
            file_response = requests.get(
                f"{TELEGRAM_API_URL}/getFile", params={"file_id": file_id})
            file_response.raise_for_status()

            # Parse JSON response for file data
            file_data = file_response.json()
            if file_data.get("ok"):
                # Construct and return the file URL
                file_path = file_data["result"]["file_path"]
                return f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

    except requests.RequestException as e:
        # Log or handle network issues here
        print("Network error:", e)
    except ValueError as e:
        # Handle JSON decode error if the response isn't JSON
        print("JSON decoding error:", e)

    # Return None if no photo is found or if any error occurs
    return None


def create_invoice(user, amount=50) -> dict:
    o_id = user.telegram_id

    payment = Payment.objects.create(
        user=user,
        amount=amount,
        order_id=o_id,
        payment_method="telegram"
    )

    o_id = str(o_id) + "&&&" + str(payment.id)
    print(f"[order_id]: {o_id}")
    data = {
        "title": "Rich Snake",
        "description": "Subscription for Rich Snake",
        "payload": o_id,
        "provider_token": "",  # Token from BotFather
        "currency": "XTR",
        "prices": [
            {"label": "Telegram Stars", "amount": amount}
        ]
    }

    headers = {
        'Content-Type': 'application/json'
    }

    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/createInvoiceLink"
    response = requests.post(url, json=data, headers=headers)

    # Process the response
    if 200 <= response.status_code < 300:
        response_data = response.json()
        if response_data['ok']:
            return {"url": response_data['result']}
        else:
            raise Exception(f"Invoice creation failed: {response_data['description']}")
    else:
        raise Exception(f"Error: {response.status_code}; Body: {response.text}; Data: {data}")

