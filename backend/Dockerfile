FROM python:3.11-slim AS builder

WORKDIR /app

# Build deps for Python wheels
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --wheel-dir /wheels -r requirements.txt


FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime deps (Unstructured + DB tools)
RUN apt-get update && apt-get install -y \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    libreoffice \
    pandoc \
    imagemagick \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links /wheels /wheels/*

COPY app ./app

ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
