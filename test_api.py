import requests
from requests.auth import HTTPBasicAuth

# 🔐 WordPress Zugangsdaten
WP_USERNAME = "modusmarketingwebadmin"
WP_APP_PASSWORD = "PRWL 9zbt uuwn xDfU Sq97 MFJW"

# 📡 Ziel: REST-API auf deiner Seite
endpoint = "https://lead.modus-marketing.de/wp-json/mycred/v1/deduct"

# 🧾 Das soll abgezogen werden
payload = {
    "user_id": 1,  # <- Deine ID
    "amount": 5,   # <- Wie viele Credits sollen abgezogen werden?
    "log": "🔧 Test: 5 Credits manuell abgezogen"
}

# 📬 Senden!
res = requests.post(endpoint, json=payload, auth=HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD))

# 📣 Zeig mir die Antwort
print("Status-Code:", res.status_code)
print("Antwort:", res.text)
