FROM python:3.11-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN crontab crontab

CMD [ "/bin/sh", "entrypoint.sh" ]