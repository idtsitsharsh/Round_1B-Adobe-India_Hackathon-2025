FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY models ./models
COPY input_docs ./input_docs
COPY outputs ./outputs

ENTRYPOINT ["python", "-m", "app.main", "--input", "/app/input_docs", "--output", "/app/outputs"]
