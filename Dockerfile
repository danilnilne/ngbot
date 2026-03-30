FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home ngbot
WORKDIR /home/ngbot

# 4. Сначала копируем зависимости (кэширование слоев)
COPY --chown=ngbot:ngbot requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --user -r requirements.txt

COPY --chown=ngbot:ngbot . .

USER ngbot

ENV PATH="/home/ngbot/.local/bin:${PATH}"

CMD ["python", "start.py"]
