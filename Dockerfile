FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN addgroup --system proofthread && adduser --system --ingroup proofthread proofthread

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations
RUN python -m pip install --upgrade pip && python -m pip install .

RUN mkdir -p /app/data && chown -R proofthread:proofthread /app
USER proofthread

VOLUME ["/app/data"]
CMD ["proofthread"]
