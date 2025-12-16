"""期权数据抓取模块 - 使用 yfinance"""

import json
import yfinance as yf
from datetime import datetime
from pathlib import Path

# 主要指数 ETF
INDEX_SYMBOLS = ['SPY', 'QQQ', 'IWM', 'DIA', 'VIX']

# 热门个股列表 (高期权成交量股票)
POPULAR_STOCKS = [
    'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'META', 'GOOGL', 'AMD', 'NFLX', 'COIN',
    'PLTR', 'SOFI', 'NIO', 'BABA', 'GME', 'AMC', 'BA', 'DIS', 'INTC', 'MU',
    'PYPL', 'SQ', 'SHOP', 'UBER', 'RIVN', 'LCID', 'F', 'GM', 'JPM', 'BAC',
    'XOM', 'CVX', 'PFE', 'MRNA', 'JNJ', 'UNH', 'V', 'MA', 'WMT', 'TGT'
]


def get_options_volume(symbol: str) -> dict:
    """获取单个股票的期权成交量数据"""
    try:
        ticker = yf.Ticker(symbol)

        # 获取所有到期日
        expirations = ticker.options
        if not expirations:
            return None

        # 获取最近到期日的期权链
        nearest_expiry = expirations[0]
        opt = ticker.option_chain(nearest_expiry)

        calls = opt.calls
        puts = opt.puts

        call_volume = calls['volume'].sum() if 'volume' in calls.columns else 0
        put_volume = puts['volume'].sum() if 'volume' in puts.columns else 0

        # 处理 NaN
        call_volume = int(call_volume) if call_volume == call_volume else 0
        put_volume = int(put_volume) if put_volume == put_volume else 0

        total_volume = call_volume + put_volume
        cp_ratio = round(call_volume / put_volume, 2) if put_volume > 0 else 0

        # 找出成交量最大的期权
        hottest_call = None
        hottest_put = None

        if not calls.empty and 'volume' in calls.columns:
            calls_sorted = calls.dropna(subset=['volume']).sort_values('volume', ascending=False)
            if not calls_sorted.empty:
                top_call = calls_sorted.iloc[0]
                hottest_call = f"C{top_call['strike']:.0f}"

        if not puts.empty and 'volume' in puts.columns:
            puts_sorted = puts.dropna(subset=['volume']).sort_values('volume', ascending=False)
            if not puts_sorted.empty:
                top_put = puts_sorted.iloc[0]
                hottest_put = f"P{top_put['strike']:.0f}"

        hottest = f"{hottest_call or ''}/{hottest_put or ''}".strip('/')

        return {
            'symbol': symbol,
            'call_volume': call_volume,
            'put_volume': put_volume,
            'total_volume': total_volume,
            'cp_ratio': cp_ratio,
            'hottest_option': hottest,
            'expiry': nearest_expiry
        }
    except Exception as e:
        print(f"Error fetching options for {symbol}: {e}")
        return None


def fetch_options_data() -> dict:
    """抓取所有期权数据"""
    print("Fetching options data...")

    # 抓取指数期权
    index_options = []
    for symbol in INDEX_SYMBOLS:
        data = get_options_volume(symbol)
        if data:
            index_options.append(data)
            print(f"  {symbol}: {data['total_volume']:,} contracts")

    # 抓取个股期权
    stock_options = []
    for symbol in POPULAR_STOCKS:
        data = get_options_volume(symbol)
        if data:
            stock_options.append(data)

    # 按成交量排序
    stock_options.sort(key=lambda x: x['total_volume'], reverse=True)
    top_25_stocks = stock_options[:25]

    # 计算市场概览
    total_call_volume = sum(d['call_volume'] for d in stock_options)
    total_put_volume = sum(d['put_volume'] for d in stock_options)
    total_volume = total_call_volume + total_put_volume
    pc_ratio = round(total_put_volume / total_call_volume, 2) if total_call_volume > 0 else 0

    # 判断市场情绪
    if pc_ratio < 0.7:
        sentiment = "极度看涨"
    elif pc_ratio < 0.9:
        sentiment = "偏向看涨"
    elif pc_ratio < 1.1:
        sentiment = "中性"
    elif pc_ratio < 1.3:
        sentiment = "偏向看跌"
    else:
        sentiment = "极度看跌"

    result = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'market_overview': {
            'total_volume': total_volume,
            'total_call_volume': total_call_volume,
            'total_put_volume': total_put_volume,
            'pc_ratio': pc_ratio,
            'sentiment': sentiment
        },
        'index_options': sorted(index_options, key=lambda x: x['total_volume'], reverse=True),
        'top_25_stocks': top_25_stocks
    }

    # 保存到文件
    output_path = Path(__file__).parent.parent.parent / 'data' / 'options.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Options data saved to {output_path}")
    return result


if __name__ == '__main__':
    data = fetch_options_data()
    print(f"\nMarket Overview:")
    print(f"  Total Volume: {data['market_overview']['total_volume']:,}")
    print(f"  P/C Ratio: {data['market_overview']['pc_ratio']}")
    print(f"  Sentiment: {data['market_overview']['sentiment']}")
