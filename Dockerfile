FROM python:3.11

WORKDIR /tgbot

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY bot.py .
COPY download_bot.py .




