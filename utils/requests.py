import requests
import os
import urllib3
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASEURL = "https://api.cloudflare.com/client/v4"
CLOUDFLARE_ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"
}

def http_request2(method, endpoint, headers=HEADERS, data=None, params=None):
    url = f"{BASEURL}{endpoint}"
    response = requests.request(method, url, headers=headers, json=data, params=params, verify=False)
    return response