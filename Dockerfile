# syntax=docker/dockerfile:1.4
FROM python:3.12-slim

WORKDIR /app

# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy entire project (including src/)
COPY . .

# include src/ in Python module search path
ENV PYTHONPATH=/app/src

ENV PORT=8080

# start the bot via its module path
CMD ["python", "-m", "trovabenzina.core.bot"]
