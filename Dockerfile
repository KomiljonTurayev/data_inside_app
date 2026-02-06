FROM python:3.12.8-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py run.py ./
COPY app/ app/
COPY workflows/ workflows/

# Create output directories
RUN mkdir -p outputs app/static/images/generated

EXPOSE 8080

CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8080"]
