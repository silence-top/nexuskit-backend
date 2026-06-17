FROM python:3.12.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel build

COPY sdk /sdk
COPY services/pyproject.toml .

RUN pip install --no-cache-dir .

# 复制服务代码
COPY services /app

# 复制 Docker 环境变量文件（关键）
COPY services/.env.docker /app/.env

EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
