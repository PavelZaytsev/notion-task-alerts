FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for notifications and timezone
RUN apt-get update && apt-get install -y \
    libnotify-bin \
    dbus-x11 \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set timezone (configurable via environment variable, defaults to UTC)
ENV TZ=${TZ:-UTC}
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user for security
RUN useradd -m -u 1000 notionuser && chown -R notionuser:notionuser /app
USER notionuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "notion_task_alerts.py"] 