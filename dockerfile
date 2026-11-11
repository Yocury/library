FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE=/data/library.db

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data reports

EXPOSE 8000

CMD ["sh", "-c", "python -c 'from app import init_db; init_db()' && gunicorn -b 0.0.0.0:8000 -w 2 app:app"]