#!/usr/bin/env python

import requests
import json

porkbun_url = "https://porkbun.com/api/json/v3"
config_file = "config.json"


def get_public_ip(url: str, headers: dict, body: dict) -> str:
    request = requests.post(url=f"{url}/ping", headers=headers, json=body)
    request.raise_for_status

    if request.json()["status"] == "SUCCESS":
        public_ip = request.json()["yourIp"]
    else:
        public_ip = "ERROR"
        raise Exception(request.json())

    return public_ip


def get_records(url: str, headers: dict, body: dict, domain: str) -> list:
    request = requests.post(url=f"{url}/dns/retrieve/{domain}",
                            headers=headers, json=body)
    request.raise_for_status

    if request.json()["status"] == "SUCCESS":
        records = request.json()["records"]
        records = [r for r in records if r["type"] == "A"]
    else:
        records = "ERROR"
        raise Exception(request.json())

    return records


def compare_records(domain: str, current_records: dict,
                    ip: str, subdomains: list,
                    update_root: bool = False) -> list:
    to_update = []
    for sub in subdomains:
        records = [r for r in current_records if r["name"] == f"{sub}.{domain}"]
        for r in records:
            record_dict = {}
            if r["content"] != ip:
                record_dict["domain"] = domain
                record_dict["subdomain"] = sub
                to_update.append(record_dict)

    if update_root:
        records = [r for r in current_records if r["name"] == f"{domain}"]
        for r in records:
            record_dict = {}
            if r["content"] != ip:
                record_dict["domain"] = domain
                record_dict["subdomain"] = ""
                to_update.append(record_dict)

    return to_update


def update_record(url: str, headers: dict, body: dict, domain: str,
                  subdomain: str, ip: str) -> str:
    body["content"] = ip
    body["ttl"] = "600"

    try:
        request = requests.post(url=f"{url}/dns/editByNameType/{domain}/A/{subdomain}",
                                headers=headers, json=body)
        request.raise_for_status()
    except Exception as x:
        return str(x)

    return request.json()["status"]


def main():
    with open(config_file, 'r') as f:
        config_data = json.load(f)

    body = {
        "apikey": config_data['api_key'],
        "secretapikey": config_data['secret_key']
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    public_ip = get_public_ip(url=porkbun_url, headers=headers, body=body)

    records_to_update = []
    for r in config_data["records"]:
        current_records = get_records(url=porkbun_url, headers=headers,
                                      body=body,
                                      domain=r["domain"])
        r_to_update = compare_records(domain=r["domain"],
                                      subdomains=r["subdomains"],
                                      current_records=current_records,
                                      ip=public_ip,
                                      update_root=r["update_root"])
        records_to_update = r_to_update + records_to_update

    if records_to_update:
        for r in records_to_update:
            result = update_record(url=porkbun_url, headers=headers, body=body,
                                   domain=r["domain"],
                                   subdomain=r["subdomain"],
                                   ip=public_ip)
            print(r["domain"], r["subdomain"], "Result:", result)
    else:
        print("No records to update.")


if __name__ == "__main__":
    main()
