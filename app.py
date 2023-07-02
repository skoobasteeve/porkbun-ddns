#!/usr/bin/env python

import requests
import json

porkbun_url = "https://porkbun.com/api/json/v3"
api_key = ""
secret_api_key = ""
config_file = "config.json"


def get_public_ip(url: str, headers: dict, body: dict):
    request = requests.post(url=f"{url}/ping", headers=headers, json=body)
    request.raise_for_status

    if request.json()["status"] == "SUCCESS":
        public_ip = request.json()["yourIp"]
    else:
        public_ip = "ERROR"
    
    return public_ip


def get_records(url: str, headers: dict, body: dict, domain: str):
    request = requests.post(url=f"{url}/dns/retrieve/{domain}", headers=headers, json=body)
    request.raise_for_status

    if request.json()["status"] == "SUCCESS":
        records = request.json()["records"]
        records = [r for r in records if r["type"] == "A"]
    else:
        records = "ERROR"
    
    return records


def compare_records(domain: str, subdomains: list, current_records: dict, ip: str):
    to_update = []
    for sub in subdomains:
        records = [r for r in current_records if r["name"] == f"{sub}.{domain}"]
        for r in records:
            if r["content"] != ip:
                to_update.append(r["name"])
    
    return to_update


def main():
    body = {
        "apikey": api_key,
        "secretapikey": secret_api_key
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    public_ip = get_public_ip(url=porkbun_url, headers=headers, body=body)

    with open(config_file) as f:
        config_data = json.load(f)

    for r in config_data["records"]:
        current_records = get_records(url=porkbun_url, headers=headers, body=body, domain=r["domain"])
        records_to_update = compare_records(domain=r["domain"], subdomains=r["subdomains"], current_records=current_records, ip=public_ip)
        print(records_to_update)


if __name__ == "__main__":
    main()


