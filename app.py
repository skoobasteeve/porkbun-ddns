#!/usr/bin/env python

'''
A simple Dynamic DNS script for Porkbun - https://porkbun.com

To run:
1. Generate API credentials for your Porkbun account.
2. Ensure that any domains you want to update have "API Access" turned
   on in the Porkbun domain management console.
3. Create a file called 'config.json' and, using 'config.json.example'
   as a reference, add your API credentials and any domains you wish
   to keep updated. This file should be in the same location as the script.
4. Run the script: python ./app.py
5. (optional) Create a cron job or systemd timer to run the script on a
   schedule.

For Docker environments, you can also use the pre-baked Docker image:
https://hub.docker.com/repository/docker/skoobasteeve/porkbun-ddns

More info:
https://github.com/skoobasteeve/porkbun-ddns

'''

import requests
import json
import sys
import logging
import os

porkbun_url = "https://porkbun.com/api/json/v3"
config_file = f"{sys.path[0]}/config.json"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


# Send a ping to Healthchecks.io when task succeeds or fails
def healthchecks(hc_url: str, message: str, fail: bool = False):
    # Skip if url not provided in config
    if not hc_url:
        logging.info("No Healthchecks URL provided, skipping...")
        return

    # If signaling a failure, add /1 to the URL so Healthchecks knows
    if fail:
        hc_url = hc_url + "/1"

    try:
        # Send request to Healthchecks
        request = requests.post(url=hc_url, data=message, timeout=10)
        request.raise_for_status()
    except Exception as x:
        logging.error("Exception", x)


# Check for any issues related to the provided configuration file
def validate_config(config_file: str):
    # Check if config.json exists
    if not os.path.isfile(config_file):
        logging.error("config.json not found! Exiting...")
        sys.exit(1)

    # Check if the file contains valid JSON
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
    except json.decoder.JSONDecodeError as x:
        logging.error(f"Invalid JSON in config.json: {x}")
        logging.error("Exiting...")
        sys.exit(1)

    # Check that API credentials are provided in the file
    api_key = config_data.get('api_key', {})
    secret_key = config_data.get('secret_key', {})
    if not api_key:
        logging.error("Porkbun API key not specified in config.json. " +
                      "Exiting...")
        sys.exit(1)
    if not secret_key:
        message = ("Porkbun API secret key not specified in config.json. " +
                   "Exiting...")
        logging.error(message)
        sys.exit(1)


# Get the public IP address of the system that the script is running on
def get_public_ip(url: str, headers: dict, body: dict, hc_url: str) -> str:
    # Use Porkbun's /ping endpoint to return a public IP
    try:
        request = requests.post(url=f"{url}/ping", headers=headers, json=body)
        request.raise_for_status()

        # If Porkbun has any issues providing an IP, raise an exception
        if request.json()["status"] == "SUCCESS":
            public_ip = request.json()["yourIp"]
        else:
            public_ip = "ERROR"
            raise Exception(request.json())
    except Exception as x:
        logging.error("Exception:", x)
        healthchecks(hc_url=hc_url, message=str(x), fail=True)
        sys.exit(1)

    return public_ip


# Get a list of all DNS records for a given domain
def get_records(url: str, headers: dict, body: dict, domain: str,
                hc_url: str) -> list:
    try:
        # Send a request to Porkbun's DNS API
        request = requests.post(url=f"{url}/dns/retrieve/{domain}",
                                headers=headers, json=body)
        request.raise_for_status()

        # If Porkbun has any issues providing the records, raise an exception
        if request.json()["status"] == "SUCCESS":
            records = request.json()["records"]
            # Filter the list to include only "A" records
            records = [r for r in records if r["type"] == "A"]
        else:
            records = "ERROR"
            raise Exception(request.json())
    except Exception as x:
        logging.error("Exception:", x)
        healthchecks(hc_url=hc_url, message=str(x), fail=True)

    return records


# Determine which records specified in config.json need to be updated
def compare_records(domain: str, current_records: dict,
                    ip: str, subdomains: list,
                    update_root: bool = False) -> list:
    to_update = []
    # For each subdomain specified in the config file, compare the IP in
    # its Porkbun DNS record with the IP of the current system.
    # If the IP addresses don't match, add the record to a list.
    for sub in subdomains:
        records = [r for r in current_records if r["name"] == f"{sub}.{domain}"]
        for r in records:
            record_dict = {}
            if r["content"] != ip:
                record_dict["domain"] = domain
                record_dict["subdomain"] = sub
                to_update.append(record_dict)

    # If the config file specifies that the root domain should be updated,
    # check the domain in Porkbun and add to the list if it needs updating.
    if update_root:
        records = [r for r in current_records if r["name"] == f"{domain}"]
        for r in records:
            record_dict = {}
            if r["content"] != ip:
                record_dict["domain"] = domain
                record_dict["subdomain"] = ""
                to_update.append(record_dict)

    return to_update


# Update a DNS "A" record in Porkbun
def update_record(url: str, headers: dict, body: dict, domain: str,
                  subdomain: str, ip: str, hc_url: str) -> str:
    # Add the public IP address to the request body
    body["content"] = ip
    body["ttl"] = "600"

    # Send the update request to Porkbun
    try:
        request = requests.post(url=f"{url}/dns/editByNameType/{domain}/A/{subdomain}",
                                headers=headers, json=body)
        request.raise_for_status()
    except Exception as x:
        healthchecks(hc_url=hc_url, message=str(x), fail=True)
        return str(f"Exception: {x}")

    return request.json()["status"]


def main():

    # Check the validity of config.json and exit if it's not valid
    validate_config(config_file=config_file)

    # Open the config file for reading
    with open(config_file, 'r') as f:
        config_data = json.load(f)

    # Get the Healthchecks.io url from the config file
    hc_url = config_data.get('healthchecks_url', {})

    # Add credentials to the request body
    body = {
        "apikey": config_data['api_key'],
        "secretapikey": config_data['secret_key']
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Get the public IP of the current system
    public_ip = get_public_ip(url=porkbun_url, headers=headers, body=body,
                              hc_url=hc_url)

    # Determine which DNS records in the config file need to be updated
    records_to_update = []
    for r in config_data["records"]:
        # Get DNS records from Porkbun
        current_records = get_records(url=porkbun_url, headers=headers,
                                      body=body,
                                      domain=r["domain"], hc_url=hc_url)
        # Compare Porkbun records with the current public IP
        r_to_update = compare_records(domain=r["domain"],
                                      subdomains=r["subdomains"],
                                      current_records=current_records,
                                      ip=public_ip,
                                      update_root=r["update_root"])
        # Build the list of records to update
        records_to_update = r_to_update + records_to_update

    # Update all records whose IP address differs from the public IP
    if records_to_update:
        hc_message = ""
        for r in records_to_update:
            result = update_record(url=porkbun_url, headers=headers, body=body,
                                   domain=r["domain"],
                                   subdomain=r["subdomain"],
                                   ip=public_ip, hc_url=hc_url)
            if r['subdomain']:
                log_str = f"{r['subdomain']}.{r['domain']} {result}"
            else:
                log_str = f"{r['domain']} {result}"

            if "Exception:" in result:
                logging.error(log_str)
                healthchecks(hc_url=hc_url, message=str(log_str), fail=True)
            else:
                logging.info(log_str)
                hc_message = hc_message + f"\n{log_str}"
        healthchecks(hc_url=hc_url, message=hc_message, fail=False)
    else:
        message = "All records are up-to-date."
        logging.info(message)
        healthchecks(hc_url=hc_url, message=message, fail=False)


if __name__ == "__main__":
    main()
