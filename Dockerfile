# syntax=docker/dockerfile:1
FROM python:3.13-slim

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python deps first (cache-friendly)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy project files
COPY . /app

# Railway provides $PORT; default to 8000 locally
EXPOSE 8000

# Run DB migrations then start Gunicorn bound to $PORT
# Note: collectstatic is omitted because STATIC_ROOT is not configured in settings.py
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn --workers 3 --bind 0.0.0.0:${PORT:-8000} config.wsgi:application"]
