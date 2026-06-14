FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libxml2-dev \
    libxslt1-dev \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install --no-cache-dir flask && \
    pip install --no-cache-dir -e .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV SMARTRESUME_CONFIG=/app/configs/config.yaml

EXPOSE 4999

CMD ["python", "scripts/start.py", "--help"]
