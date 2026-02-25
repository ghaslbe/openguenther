# ── Stage 1: Build Frontend ──
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Production ──
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies (fonts, ImageMagick, WeasyPrint HTML→PDF)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    imagemagick \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libffi8 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Create data directory
RUN mkdir -p /app/data

ENV DATA_DIR=/app/data
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

WORKDIR /app/backend
CMD ["python", "app.py"]
