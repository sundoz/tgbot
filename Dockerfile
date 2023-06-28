FROM python:3.11

WORKDIR /tgbot

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY bot.py .
COPY download_bot.py .
ENV TOKEN=5898838534:AAHhJwk2v56idXyWx9GWxLI6gKLaIT33rP4

CMD ['python', 'bot.py']

