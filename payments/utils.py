from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

SERVICE_ACCOUNT_FILE = "credentials/google-play.json"
PACKAGE_NAME = "com.yourapp"

def verify_android_purchase(purchase_token, product_id):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/androidpublisher']
    )

    service = build('androidpublisher', 'v3', credentials=credentials)
    
    try:
        result = service.purchases().products().get(
            packageName=PACKAGE_NAME,
            productId=product_id,
            token=purchase_token
        ).execute()

        if result.get("purchaseState") == 0:
            return {"valid": True, "expiry": None}
        else:
            return {"valid": False}
    except Exception:
        return {"valid": False}
    
import requests
import jwt
import time

APP_STORE_URL = "https://api.storekit.itunes.apple.com/inApps/v1/transactions/lookup"

def verify_ios_purchase(receipt, product_id):
    token = jwt.encode(
        {
            "iss": APP_STORE_ISSUER_ID,
            "iat": int(time.time()),
            "exp": int(time.time()) + 60,
            "aud": "appstoreconnect-v1"
        },
        APP_STORE_PRIVATE_KEY,
        algorithm="ES256",
        headers={"kid": APP_STORE_KEY_ID}
    )

    response = requests.post(APP_STORE_URL, headers={
        "Authorization": f"Bearer {token}"
    }, json={
        "transactionId": receipt
    })

    data = response.json()

    if "data" not in data:
        return {"valid": False}

    item = data["data"][0]

    if item["productId"] != product_id:
        return {"valid": False}

    expiry = item.get("expiresDate")

    return {"valid": True, "expiry": expiry}

