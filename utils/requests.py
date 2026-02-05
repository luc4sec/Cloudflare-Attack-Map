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

# def http_request_dash_guardnet(method, endpoint, headers=HEADERS, data=None, params=None):
#     url = f"http://10.1.10.203:8080/api/v1{endpoint}"
#     response = requests.request(method, url, headers=headers, json=data, params=params)
#     return response

# def graphql_request(query, variables=None, retries=3):
#     endpoint = "/graphql"
#     data = {
#         "query": query,
#         "variables": variables
#     }
#     return http_request2("POST", endpoint, headers=HEADERS, data=data)