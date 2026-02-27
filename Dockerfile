# ============================================
# Stage 1: Build Frontend (Vue.js + Vite)
# ============================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app

# Copy package files first (leverage Docker cache)
COPY web/package.json web/package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy frontend source code
COPY web/ .

# Build frontend
RUN npm run build

# ============================================
# Stage 2: Backend + Serve Frontend
# ============================================
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source code
COPY src/ ./src/
COPY static/ ./static/
COPY assets/ ./assets/

# Copy frontend build output from stage 1
COPY --from=frontend-builder /app/dist ./web/dist/

# Create necessary directories
RUN mkdir -p /app/assets/saves /app/logs

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8002

EXPOSE 8002

# Start backend in production mode (no --dev flag)
CMD ["uvicorn", "src.server.main:app", "--host", "0.0.0.0", "--port", "8002"]
