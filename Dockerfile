FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=.

# Install system utilities & GDAL runtime dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend, data, and pre-built frontend
COPY backend /app/backend
COPY data /app/data
COPY frontend/dist /app/frontend/dist
COPY run_inference.py /app/run_inference.py
COPY evaluate_submission.py /app/evaluate_submission.py

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
