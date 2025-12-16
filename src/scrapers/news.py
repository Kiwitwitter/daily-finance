"""新闻抓取模块 - 使用 Finnhub API"""

import json
import os
import finnhub
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def fetch_news() -> dict:
    """抓取市场新闻"""
    print("Fetching market news...")

    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        raise ValueError("FINNHUB_API_KEY not found in environment variables")

    client = finnhub.Client(api_key=api_key)

    # 获取今天和昨天的日期
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    # 获取市场综合新闻
    news_list = client.general_news('general', min_id=0)

    # 过滤和处理新闻
    processed_news = []
    for news in news_list[:50]:  # 取前50条
        processed_news.append({
            'id': news.get('id'),
            'headline': news.get('headline', ''),
            'summary': news.get('summary', ''),
            'source': news.get('source', ''),
            'url': news.get('url', ''),
            'datetime': datetime.fromtimestamp(news.get('datetime', 0)).strftime('%Y-%m-%d %H:%M'),
            'category': news.get('category', ''),
            'related': news.get('related', '')
        })

    result = {
        'date': today.strftime('%Y-%m-%d'),
        'fetch_time': today.strftime('%Y-%m-%d %H:%M:%S'),
        'news_count': len(processed_news),
        'news': processed_news
    }

    # 保存到文件
    output_path = Path(__file__).parent.parent.parent / 'data' / 'news.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Fetched {len(processed_news)} news articles, saved to {output_path}")
    return result


if __name__ == '__main__':
    data = fetch_news()
    print(f"\nSample headlines:")
    for news in data['news'][:5]:
        print(f"  - {news['headline'][:80]}...")
