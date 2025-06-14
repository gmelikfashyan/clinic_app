# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Обновление системных пакетов и установка зависимостей PostgreSQL
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    gcc \
    python3-dev \
    musl-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование requirements
COPY requirements.txt /app/

# Установка зависимостей Python
RUN pip install --no-cache-dir \
    --upgrade pip \
    wheel \
    setuptools && \
    pip install --no-cache-dir psycopg2-binary && \
    pip install --no-cache-dir -r requirements.txt

# Копирование всего проекта
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput





# Открытие порта
EXPOSE 8000

# Запуск приложения через gunicorn
CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:8000 clinic_project.wsgi:application"]