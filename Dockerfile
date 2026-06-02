FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY opc_os ./opc_os
COPY scripts ./scripts
COPY tests ./tests
COPY opc-os ./opc-os

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

RUN mkdir -p /app/data

ENV OPC_OS_DB_PATH=/app/data/opc_os.db

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python scripts/health_check.py

CMD ["python", "scripts/run_opc_os_service.py"]
