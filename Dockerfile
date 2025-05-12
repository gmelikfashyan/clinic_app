# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Обновление системных пакетов и установка зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    gcc \
    python3-dev \
    musl-dev && \
    rm -rf /var/lib/apt/lists/*

# Создаем и устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements первым слоем для кэширования
COPY requirements.txt /app/

# Установка зависимостей с дополнительной диагностикой
RUN pip install --no-cache-dir \
    --upgrade pip \
    wheel \
    setuptools && \
    pip install --no-cache-dir psycopg2-binary && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /app/

# Скрипт для выполнения миграций с расширенной диагностикой
RUN <<EOF
#!/bin/bash
set -e

# Проверка переменных окружения
if [ -z "$DATABASE_URL" ]; then
    echo "ОШИБКА: DATABASE_URL не установлен. Миграции не могут быть выполнены."
    exit 1
fi

# Попытка выполнения миграций с подробным выводом
echo "Попытка выполнения миграций..."
python manage.py migrate --noinput || {
    echo "ОШИБКА при выполнении миграций. Проверьте подключение к базе данных."
    exit 1
}

# Сбор статических файлов
python manage.py collectstatic --noinput
EOF

# Открываем порт
EXPOSE 8000

# Команда запуска
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "clinic_project.wsgi:application"]