FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY visjpeg/ ./visjpeg/
COPY run.py .

# Non-root user
RUN useradd -m -s /bin/bash visjpeg && chown -R visjpeg:visjpeg /app
USER visjpeg

EXPOSE 8501

CMD ["python3", "-m", "visjpeg"]
