# syntax=docker/dockerfile:1.6

FROM node:20-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        python3 \
        python3-pip \
        curl \
        ca-certificates \
        inotify-tools \
        watchman && \
    rm -rf /var/lib/apt/lists/*

# Node 官方镜像已自带 yarn；启用 corepack 并安装常用 CLI。
RUN corepack enable && \
    corepack prepare pnpm@latest --activate && \
    npm install -g \
      turbo@latest \
      vite@latest \
      next@latest \
      pm2@latest \
      serve@latest

ENV CHOKIDAR_USEPOLLING=1 \
    WATCHPACK_POLLING=true \
    BROWSER=none

WORKDIR /workspace

CMD ["bash", "-lc", "tail -f /dev/null"]
