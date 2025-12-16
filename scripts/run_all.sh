#!/bin/bash
# 完整工作流程：Docker 抓取 -> 本地 Claude 分析 -> Docker 生成报告

set -e

echo "=========================================="
echo "美股财经日报 - 完整更新流程"
echo "=========================================="

cd "$(dirname "$0")/.."

# 1. Docker 内抓取数据
echo ""
echo "[1/3] Docker 内抓取数据..."
docker-compose exec -T web python scripts/daily_job.py

# 2. 本地运行 Claude 分析
echo ""
echo "[2/3] 本地运行 Claude 分析..."
python3 scripts/analyze.py

# 3. Docker 内重新生成报告（包含分析结果）
echo ""
echo "[3/3] Docker 内生成报告..."
docker-compose exec -T web python src/generators/build.py

echo ""
echo "=========================================="
echo "完成！访问 http://localhost:8000 查看报告"
echo "=========================================="
