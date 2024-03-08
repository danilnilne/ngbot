FROM python:3.12.2

WORKDIR /app

RUN git clone https://github.com/danilnilne/ngbot.git \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r ngbot/requirements.txt

COPY config.yml ./ngbot

CMD ["python3", "ngbot/start.py"]