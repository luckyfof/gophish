#!/usr/bin/env python3

import requests
import sys
import os
import time

# Config (you need to fill these)
INFOMANIAK_API_TOKEN = "YOUR_INFOMANIAK_API_TOKEN"
DOMAIN = "yourdomain.com"

HEADERS = {
    "Authorization": f"Bearer {INFOMANIAK_API_TOKEN}",
    "Content-Type": "application/json"
}

def create_txt_record(name, value):
    url = f"https://api.infomaniak.com/1/product/dns/domain/{DOMAIN}/record"
    data = {
        "type": "TXT",
        "name": name,
        "ttl": 300,
        "text": value
    }
    resp = requests.post(url, json=data, headers=HEADERS)
    resp.raise_for_status()
    print(f"Added TXT record {name}: {value}")

def delete_txt_record(name):
    # Get all records
    url = f"https://api.infomaniak.com/1/product/dns/domain/{DOMAIN}/record"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    records = resp.json().get("data", [])

    # Find and delete matching TXT
    for record in records:
        if record["type"] == "TXT" and record["name"] == name:
            delete_url = f"https://api.infomaniak.com/1/product/dns/record/{record['id']}"
            del_resp = requests.delete(delete_url, headers=HEADERS)
            del_resp.raise_for_status()
            print(f"Deleted TXT record {name}")

def main():
    action = sys.argv[1]
    domain = os.environ.get("CERTBOT_DOMAIN")
    validation = os.environ.get("CERTBOT_VALIDATION")
    txt_name = f"_acme-challenge.{domain.strip('.')}"
    
    if action == "auth":
        create_txt_record(txt_name, validation)
        # Wait for DNS propagation
        time.sleep(60)
    elif action == "cleanup":
        delete_txt_record(txt_name)
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
