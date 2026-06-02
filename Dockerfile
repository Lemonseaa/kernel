FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY checkpoint_ai ./checkpoint_ai
COPY scripts ./scripts
COPY tests ./tests
COPY checkpointai ./checkpointai

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

RUN mkdir -p /app/data

ENV CHECKPOINT_AI_DB_PATH=/app/data/checkpoint_ai.db

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python scripts/health_check.py

CMD ["python", "scripts/run_checkpointai_service.py"]
