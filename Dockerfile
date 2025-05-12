# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

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