"""财报日历抓取模块 - 使用 Finnhub API + yfinance"""

import json
import os
import finnhub
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def fetch_earnings() -> dict:
    """抓取今日财报日历"""
    print("Fetching earnings calendar...")

    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        raise ValueError("FINNHUB_API_KEY not found in environment variables")

    client = finnhub.Client(api_key=api_key)

    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    tomorrow_str = (today + timedelta(days=1)).strftime('%Y-%m-%d')

    # 使用 Finnhub 获取财报日历
    earnings = client.earnings_calendar(
        _from=today_str,
        to=tomorrow_str,
        symbol='',
        international=False
    )

    today_earnings = []
    if earnings and 'earningsCalendar' in earnings:
        for e in earnings['earningsCalendar']:
            if e.get('date') == today_str:
                # 获取额外的股票信息
                symbol = e.get('symbol', '')
                market_cap = None

                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    market_cap = info.get('marketCap')
                except:
                    pass

                today_earnings.append({
                    'symbol': symbol,
                    'date': e.get('date', ''),
                    'hour': e.get('hour', ''),  # bmo=盘前, amc=盘后
                    'eps_estimate': e.get('epsEstimate'),
                    'eps_actual': e.get('epsActual'),
                    'revenue_estimate': e.get('revenueEstimate'),
                    'revenue_actual': e.get('revenueActual'),
                    'market_cap': market_cap
                })

    # 按市值排序（大公司优先）
    today_earnings.sort(
        key=lambda x: x['market_cap'] if x['market_cap'] else 0,
        reverse=True
    )

    # 分类：盘前 vs 盘后
    before_market = [e for e in today_earnings if e['hour'] == 'bmo']
    after_market = [e for e in today_earnings if e['hour'] == 'amc']

    result = {
        'date': today_str,
        'fetch_time': today.strftime('%Y-%m-%d %H:%M:%S'),
        'total_count': len(today_earnings),
        'before_market': before_market[:15],  # 盘前重点财报
        'after_market': after_market[:15],    # 盘后重点财报
        'all_earnings': today_earnings[:50]   # 全部（前50）
    }

    # 保存到文件
    output_path = Path(__file__).parent.parent.parent / 'data' / 'earnings.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Fetched {len(today_earnings)} earnings reports for today, saved to {output_path}")
    return result


if __name__ == '__main__':
    data = fetch_earnings()

    print(f"\nBefore Market ({len(data['before_market'])} companies):")
    for e in data['before_market'][:5]:
        print(f"  {e['symbol']}: EPS Est. {e['eps_estimate']}")

    print(f"\nAfter Market ({len(data['after_market'])} companies):")
    for e in data['after_market'][:5]:
        print(f"  {e['symbol']}: EPS Est. {e['eps_estimate']}")
