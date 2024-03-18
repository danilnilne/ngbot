FROM python:3.12.2

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3", "start.py"]