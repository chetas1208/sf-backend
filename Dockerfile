FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CONTACTS_HOST=0.0.0.0 \
    CONTACTS_PORT=8000 \
    CONTACTS_DATABASE_URL=sqlite+pysqlite:////data/contacts.db \
    CONTACTS_SEED_DATA=true

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir /data \
    && chown app:app /data

COPY pyproject.toml ./
COPY app ./app

# Install only the production dependencies declared in pyproject.toml.
RUN pip install --no-cache-dir .

USER app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD ["python", "-m", "app.healthcheck"]

CMD ["contacts-api"]
