FROM python:3.12-slim

# ── System dependencies for WeasyPrint + Presidio ────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # WeasyPrint rendering engine
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libglib2.0-0 \
    shared-mime-info \
    # Fonts for PDF
    fonts-liberation \
    fonts-dejavu-core \
    # Build tools
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── spaCy language model for Presidio PII detection ──────────────────────────
RUN python -m spacy download en_core_web_sm

# ── Application code ──────────────────────────────────────────────────────────
COPY . .

# ── Entrypoint ────────────────────────────────────────────────────────────────
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
