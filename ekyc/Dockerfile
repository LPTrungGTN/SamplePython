FROM python:3.12.0-slim

WORKDIR /app

COPY . /app

CMD pip install --no-cache-dir -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8001 --reload
