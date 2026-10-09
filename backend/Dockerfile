FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    -r requirements.txt

# 预热中文嵌入模型（Qdrant 镜像，fastembed 缓存目录布局）
# fastembed 0.4.2 的 bge-small-zh 只认本地/GCS 缓存：目录存在即直接使用，运行时无需联网
COPY docker_warmup.py .
RUN python docker_warmup.py

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
