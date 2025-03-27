FROM python:3.11-slim

# Create and set working directory
RUN mkdir -p /app
WORKDIR /app

# Install system dependencies including redis-server and git
RUN apt-get update && apt-get install -y \
    build-essential \
    redis-server \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone repository
RUN git clone https://github.com/pendialek/replicate-ai.git . && \
    rm -rf .git

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Verify key packages are installed correctly
RUN python3 -c "import flask; import replicate; import openai; import redis; print('All key packages verified successfully!')"

# Create directories and set permissions
RUN mkdir -p /app/images /app/metadata && \
    chmod -R 755 . && \
    chmod +x app.sh

# Setup .env file if it doesn't exist
RUN if [ ! -f ".env" ]; then \
    cp .env.example .env && \
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))') && \
    sed -i "s/your_secret_key_here/$SECRET_KEY/" .env && \
    chmod 600 .env; \
    fi

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1
ENV RATELIMIT_STORAGE_URL=redis://localhost:6379/0

# Create script to start both redis and the app
RUN echo '#!/bin/bash\nservice redis-server start\ngunicorn --workers 4 --bind ${HOST:-0.0.0.0}:${PORT:-5000} app:app' > /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh

# Expose port
EXPOSE ${HOST:-0.0.0.0}

# Run the application with Redis
CMD ["/app/docker-entrypoint.sh"]