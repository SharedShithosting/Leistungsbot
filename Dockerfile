FROM python:3-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY Bot.py BotHelper.py BotScheduler.py google_place.py leistungsdb.py /usr/src/app/

ENV LEISTUNGSBOT_CONFIG_FILE "/config/BotConfig.yml"

CMD [ "python", "-u", "./Bot.py" ]