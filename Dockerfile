# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Обновление pip и установка системных зависимостей
RUN pip install --upgrade pip && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование и установка зависимостей с доп. параметрами
COPY requirements.txt /app/

# Более надежная установка зависимостей
RUN pip install --no-cache-dir \
    --upgrade pip \
    wheel \
    setuptools && \
    pip install --no-cache-dir -r requirements.txtFROM python:3.11-slim


# Copy the entire project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations (optional - can also be done separately)
RUN python manage.py migrate

# Expose the port the app runs on
EXPOSE 8000

# Use gunicorn to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "clinic_project.wsgi:application"]