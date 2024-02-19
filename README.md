# Porkbun Dynamic DNS

Minimal Dynamic DNS client for Porkbun.

## How to use

Create a file named `config.json` based on [config_example.json](config_example.json) in this repo and update it with the below information:
- `api_key` - *str* - Porkbun API key
- `secret_key` - *str* - Porkbun API secret key
- `healthchecks_url` - *str* - (optional) Healthchecks.io URL to monitor for issues
- `verbose_output` - *bool* - (Default `false`) Output a result for all runs, even if no action was taken.
- At least one domain block within `records` similar to the below:
  ``` json
  "records": [
    {
      "domain": "example.com",
      "subdomains": ["subdomain01", "subdomain02", "subdomain03"],
      "update_root": true
    }
  ]
  ```
- `records.domain` - *str* - Root domain name
- `records.subdomain` - *list* - Comma-separated list of subdomains
- `records.update_root` - *bool* - If set to `true`, the script will update the root domain in addition to the subdomains.


### Docker

The [container](https://hub.docker.com/r/skoobasteeve/porkbun-ddns) checks for DNS updates every 15 minutes or whenever it's restarted. Mount a valid `config.json` as a volume and you're good-to-go.

**One-liner**
``` shell
docker run --init --detach --volume $PWD/config.json:/usr/src/app/config.json:z skoobasteeve/porkbun-ddns:main
```

**Docker compose**
``` yaml
---
version: "3.7"
services:
  porkbun-ddns:
    container_name: porkbun-ddns
    image: skoobasteeve/porkbun-ddns:main
    init: true
    volumes:
      - $PWD/config.json:/usr/src/app/config.json
    environment:
      - CRON_INTERVAL=20 #Default, in minutes
    restart: unless-stopped
```

#### Customize interval

The porkbun-ddns Docker image checks your IP for changes every 20 minutes by default. If you'd like to change this, set the `CRON_INTERVAL` variable in your `docker run` command or `docker-compose.yml`.

### Python

You can also run the script directly with your local Python interpreter.

1. Clone this repo
   ```shell
   git clone https://github.com/skoobasteeve/porkbun-ddns.git
   ```
2. Install the dependencies.
   ``` shell
   cd porkbun-ddns
   pip install -r requirements.txt
   ```
3. Create a `config.json` and add the [required information](#how-to-use). It should be located in the same directory as the script.
4. Run the script.
   ``` shell
   python ./app.py
   ```
5. (optional) Set up a cron job or systemd timer to run the script on a schedule.


## Contributing

All contributions welcome! Feel free to file an [issue](https://github.com/skoobasteeve/porkbun-ddns/issues) or open a [pull request](https://github.com/skoobasteeve/porkbun-ddns/pulls). 