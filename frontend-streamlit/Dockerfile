# iSwitch Roofs CRM - Streamlit Dashboard
# Multi-stage Dockerfile for production deployment
# Version: 2.0.0
# Date: 2025-10-10

# ==============================================================================
# Stage 1: Base Image with Python 3.13
# ==============================================================================
FROM python:3.13-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ==============================================================================
# Stage 2: Dependencies
# ==============================================================================
FROM base as dependencies

# Create app directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ==============================================================================
# Stage 3: Production Image
# ==============================================================================
FROM base as production

# Create non-root user for security
RUN useradd -m -u 1000 streamlit && \
    mkdir -p /app /home/streamlit/.streamlit && \
    chown -R streamlit:streamlit /app /home/streamlit

# Set working directory
WORKDIR /app

# Copy installed dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=streamlit:streamlit Home.py .
COPY --chown=streamlit:streamlit app.py .
COPY --chown=streamlit:streamlit pages/ ./pages/
COPY --chown=streamlit:streamlit utils/ ./utils/

# Copy Streamlit configuration
COPY --chown=streamlit:streamlit .streamlit/ ./.streamlit/

# Create logs directory
RUN mkdir -p /app/logs && chown -R streamlit:streamlit /app/logs

# Switch to non-root user
USER streamlit

# Expose Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Set default command
CMD ["streamlit", "run", "Home.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=true", \
     "--browser.gatherUsageStats=false"]

# ==============================================================================
# Stage 4: Development Image (Optional)
# ==============================================================================
FROM production as development

# Switch back to root to install dev tools
USER root

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest==8.3.4 \
    pytest-cov==6.0.0 \
    black==24.10.0 \
    flake8==7.1.1 \
    mypy==1.13.0 \
    ipython==8.31.0

# Create additional directories for development
RUN mkdir -p /app/tests /app/docs && \
    chown -R streamlit:streamlit /app/tests /app/docs

# Switch back to streamlit user
USER streamlit

# Development command with auto-reload
CMD ["streamlit", "run", "Home.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.runOnSave=true", \
     "--server.fileWatcherType=auto"]

# ==============================================================================
# Build Instructions
# ==============================================================================
# Production build:
#   docker build --target production -t iswitch-streamlit:latest .
#
# Development build:
#   docker build --target development -t iswitch-streamlit:dev .
#
# Run production:
#   docker run -d \
#     --name iswitch-streamlit \
#     -p 8501:8501 \
#     --env-file .env \
#     iswitch-streamlit:latest
#
# Run development:
#   docker run -d \
#     --name iswitch-streamlit-dev \
#     -p 8501:8501 \
#     -v $(pwd):/app \
#     --env-file .env \
#     iswitch-streamlit:dev
#
# Health check:
#   docker exec iswitch-streamlit curl http://localhost:8501/_stcore/health
#
# View logs:
#   docker logs -f iswitch-streamlit
# ==============================================================================
