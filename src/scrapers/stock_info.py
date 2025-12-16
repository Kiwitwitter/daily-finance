"""股票基本信息抓取模块 - 用于 hover 显示"""

import json
import yfinance as yf
from datetime import datetime
from pathlib import Path

# 需要获取信息的股票列表（从其他模块汇总）
DEFAULT_STOCKS = [
    'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'META', 'GOOGL', 'AMD', 'NFLX',
    'COIN', 'PLTR', 'NIO', 'BABA', 'BA', 'DIS', 'INTC', 'MU',
    'PYPL', 'SQ', 'SHOP', 'UBER', 'JPM', 'BAC', 'GS',
    'XOM', 'CVX', 'PFE', 'JNJ', 'UNH', 'V', 'MA', 'WMT',
    'SPY', 'QQQ', 'IWM', 'DIA', '^VIX'
]


def format_number(num):
    """格式化大数字"""
    if num is None:
        return '-'
    if num >= 1e12:
        return f'{num/1e12:.2f}T'
    elif num >= 1e9:
        return f'{num/1e9:.2f}B'
    elif num >= 1e6:
        return f'{num/1e6:.2f}M'
    elif num >= 1e3:
        return f'{num/1e3:.2f}K'
    else:
        return f'{num:.2f}'


def fetch_stock_info(symbols: list = None) -> dict:
    """抓取股票基本信息"""
    print("Fetching stock info for hover tooltips...")

    if symbols is None:
        symbols = DEFAULT_STOCKS

    stock_info = {}

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # 获取今日数据
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose')

            # 计算涨跌幅
            change_pct = None
            change_val = None
            if current_price and prev_close:
                change_val = current_price - prev_close
                change_pct = (change_val / prev_close) * 100

            stock_info[symbol] = {
                'symbol': symbol,
                'name': info.get('shortName') or info.get('longName') or symbol,
                'current_price': current_price,
                'prev_close': prev_close,
                'change': round(change_val, 2) if change_val else None,
                'change_pct': round(change_pct, 2) if change_pct else None,
                'volume': info.get('volume') or info.get('regularMarketVolume'),
                'volume_formatted': format_number(info.get('volume') or info.get('regularMarketVolume')),
                'market_cap': info.get('marketCap'),
                'market_cap_formatted': format_number(info.get('marketCap')),
                'day_high': info.get('dayHigh') or info.get('regularMarketDayHigh'),
                'day_low': info.get('dayLow') or info.get('regularMarketDayLow'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
                'pe_ratio': info.get('trailingPE'),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
            }
            print(f"  {symbol}: {stock_info[symbol]['name']}")

        except Exception as e:
            print(f"  Error fetching {symbol}: {e}")
            stock_info[symbol] = {
                'symbol': symbol,
                'name': symbol,
                'error': str(e)
            }

    result = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'count': len(stock_info),
        'stocks': stock_info
    }

    # 保存到文件
    output_path = Path(__file__).parent.parent.parent / 'data' / 'stock_info.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Stock info saved to {output_path}")
    return result


if __name__ == '__main__':
    data = fetch_stock_info()
    print(f"\nFetched info for {data['count']} stocks")
