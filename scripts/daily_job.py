#!/usr/bin/env python3
"""每日定时任务 - 抓取数据并生成报告"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

def log(message: str):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def run_scraper(name: str, module: str) -> bool:
    """运行单个数据抓取模块"""
    log(f"开始抓取: {name}")
    try:
        result = subprocess.run(
            [sys.executable, '-m', module],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        if result.returncode == 0:
            log(f"✓ {name} 完成")
            return True
        else:
            log(f"✗ {name} 失败: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        log(f"✗ {name} 超时")
        return False
    except Exception as e:
        log(f"✗ {name} 错误: {e}")
        return False

def run_build() -> bool:
    """生成报告"""
    log("开始生成报告")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'src.generators.build', '--type', 'combined'],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            log("✓ 报告生成完成")
            return True
        else:
            log(f"✗ 报告生成失败: {result.stderr}")
            return False
    except Exception as e:
        log(f"✗ 报告生成错误: {e}")
        return False

def run_analysis() -> bool:
    """运行 Claude 新闻分析"""
    log("开始 Claude 智能分析")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'src.analyzers.news_analyzer'],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=120  # 2分钟超时
        )
        if result.returncode == 0:
            log("✓ Claude 分析完成")
            return True
        else:
            log(f"✗ Claude 分析失败: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        log("✗ Claude 分析超时")
        return False
    except Exception as e:
        log(f"✗ Claude 分析错误: {e}")
        return False


def main():
    log("=" * 50)
    log("开始每日数据更新任务")
    log("=" * 50)

    # 抓取所有数据
    scrapers = [
        ("期权数据", "src.scrapers.options"),
        ("新闻数据", "src.scrapers.news"),
        ("评级数据", "src.scrapers.ratings"),
        ("财经日历", "src.scrapers.econ_calendar"),
        ("财报日历", "src.scrapers.earnings"),
        ("股票信息", "src.scrapers.stock_info"),
    ]

    success_count = 0
    for name, module in scrapers:
        if run_scraper(name, module):
            success_count += 1

    log(f"数据抓取完成: {success_count}/{len(scrapers)} 成功")

    # 注意：Claude 分析需要在本地运行（使用 scripts/analyze.py）
    # Docker 容器内没有 claude CLI

    # 生成报告
    if success_count > 0:
        run_build()
    else:
        log("所有数据抓取失败，跳过报告生成")

    log("=" * 50)
    log("每日任务结束")
    log("=" * 50)

if __name__ == '__main__':
    main()
