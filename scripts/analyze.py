#!/usr/bin/env python3
"""本地运行 Claude 分析脚本 - 需要在本地执行（非 Docker）"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.analyzers.news_analyzer import analyze_news


def main():
    print("=" * 50)
    print("运行 Claude 智能分析（本地）")
    print("=" * 50)

    result = analyze_news()

    print(f"生成 {len(result.get('core_news', []))} 条核心新闻")
    print(f"生成 {len(result.get('focus_areas', []))} 个关注领域")
    print("=" * 50)


if __name__ == '__main__':
    main()
