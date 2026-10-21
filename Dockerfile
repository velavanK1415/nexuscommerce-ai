# Multi-stage Dockerfile for NexusCommerce AI
# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json frontend/yarn.lock* ./
RUN yarn install --frozen-lockfile || yarn install

COPY frontend/ ./
RUN yarn build

# Stage 2: Python Backend Runtime
FROM python:3.11-slim AS runner
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy Backend Code
COPY backend/ ./backend/

# Copy Built Frontend Assets from Stage 1 into /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose Web Port (Render sets $PORT dynamically)
ENV PORT=8000
ENV PYTHONPATH=/app/backend
EXPOSE 8000

# Launch FastAPI backend with uvicorn (serving both API and built static frontend)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
