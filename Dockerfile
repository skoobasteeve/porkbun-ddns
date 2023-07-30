FROM python:3.11-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV CRON_INTERVAL=20

COPY . .

CMD [ "/bin/sh", "entrypoint.sh" ]