# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

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

RUN python manage.py makemigrations --empty your_app_name --name merged_migrations


# Run migrations (опционально)
RUN python manage.py migrate

# Открытие порта
EXPOSE 8000

# Запуск приложения через gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "clinic_project.wsgi:application"]