FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# системные зависимости (минимум)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# зависимости отдельно, чтобы кешировались
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# код проекта
COPY . .

# том для данных (SQLite, прочее)
VOLUME /data

# дефолт на случай, если в .env не задано
ENV DATABASE_URL=sqlite:///data/shop.db

# документируем порт
EXPOSE 8000
# команду запуска задаёт docker-compose





