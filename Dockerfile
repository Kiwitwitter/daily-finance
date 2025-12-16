FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    cron \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY data/ ./data/
COPY output/ ./output/

# 复制配置文件
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY crontab /etc/cron.d/daily-finance

# 设置 crontab 权限
RUN chmod 0644 /etc/cron.d/daily-finance && \
    crontab /etc/cron.d/daily-finance

# 创建必要的目录
RUN mkdir -p data output/assets logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV TZ=America/New_York

# 暴露端口
EXPOSE 8000

# 使用 supervisor 启动多个服务
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
