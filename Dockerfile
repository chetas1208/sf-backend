FROM python:3.13-slim-bookworm@sha256:c45a22ea000adfd9cda29364bbe7edd23001ce5cc2ad15857cfbf7766943b9ca

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

COPY pyproject.toml requirements.lock ./

# Install exact runtime and build dependencies before installing this package.
RUN pip install --no-cache-dir --requirement requirements.lock

COPY app ./app

# The build backend is already pinned above, so no mutable build isolation is needed.
RUN pip install --no-cache-dir --no-deps --no-build-isolation .

USER app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD ["python", "-m", "app.healthcheck"]

CMD ["contacts-api"]
