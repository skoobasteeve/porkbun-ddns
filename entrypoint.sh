#!/bin/sh

crontab -r
echo "*/${CRON_INTERVAL} * * * * python /usr/src/app/app.py" | crontab -

python /usr/src/app/app.py
crond -f