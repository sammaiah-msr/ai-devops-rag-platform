FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY ingest.py .
COPY knowledge ./knowledge

# OpenShift compatibility:
# Allow the arbitrary UID assigned by OpenShift to write to /app
RUN mkdir -p /app/vector_db \
    && chgrp -R 0 /app \
    && chmod -R g=u /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]