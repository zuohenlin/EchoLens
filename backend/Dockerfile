# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml /app/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r <(uv pip compile pyproject.toml) \
    --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    --extra-index-url https://mirrors.aliyun.com/pypi/simple/

COPY . /app

EXPOSE 5001
CMD ["uv", "run", "python", "run.py"]
