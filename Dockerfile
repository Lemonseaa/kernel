FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY loop_harness ./loop_harness
COPY scripts ./scripts
COPY tests ./tests
COPY loopharness ./loopharness

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

RUN mkdir -p /app/data

ENV LOOP_HARNESS_DB_PATH=/app/data/loop_harness.db

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python scripts/ops/health_check.py

CMD ["python", "scripts/ops/run_loopharness_service.py"]
