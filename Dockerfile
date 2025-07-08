# syntax=docker/dockerfile:1.4

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN --mount=type=cache,id=pip-cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
CMD ["python", "bot.py"]
