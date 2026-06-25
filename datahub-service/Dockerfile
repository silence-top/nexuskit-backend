FROM python:3.12-slim

# 安全：非 root 用户运行
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# 先复制依赖文件，利用 Docker 层缓存
COPY pyproject.toml .

# 安装依赖（生产模式不安装 dev 依赖）
RUN pip install --no-cache-dir -e .

# 复制应用代码
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini .

# 切换非 root 用户
USER appuser

EXPOSE 8000

# 启动命令：生产环境建议用 gunicorn + uvicorn workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
