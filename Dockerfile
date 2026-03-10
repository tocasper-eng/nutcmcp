FROM python:3.12-slim

# 安裝 FreeTDS（pymssql 需要）
RUN apt-get update && apt-get install -y \
    freetds-dev \
    freetds-bin \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
