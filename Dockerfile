# ---- Stage 1: build the static Next.js UI ----
FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python runtime serving API + UI ----
FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY clean.py ./clean.py
COPY condo_transactions_raw.csv ./
RUN python clean.py
COPY --from=frontend-build /build/frontend/out ./frontend/out
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]