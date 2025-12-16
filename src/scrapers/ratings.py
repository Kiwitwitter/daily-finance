"""投行评级抓取模块 - 使用 yfinance"""

import json
import yfinance as yf
from datetime import datetime
from pathlib import Path

# 主要关注的股票列表
WATCHED_STOCKS = [
    'AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN', 'META', 'GOOGL', 'AMD', 'NFLX',
    'COIN', 'PLTR', 'NIO', 'BABA', 'BA', 'DIS', 'INTC', 'MU',
    'PYPL', 'SQ', 'SHOP', 'UBER', 'JPM', 'BAC',
    'XOM', 'CVX', 'PFE', 'JNJ', 'UNH', 'V', 'MA', 'WMT'
]


def fetch_ratings() -> dict:
    """抓取投行评级 - 使用 yfinance"""
    print("Fetching analyst ratings...")

    today = datetime.now()
    all_ratings = []
    recent_changes = []

    for symbol in WATCHED_STOCKS:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # 获取分析师目标价
            target_mean = info.get('targetMeanPrice')
            target_high = info.get('targetHighPrice')
            target_low = info.get('targetLowPrice')
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')

            # 获取推荐
            recommendation = info.get('recommendationKey', '')
            num_analysts = info.get('numberOfAnalystOpinions', 0)

            if target_mean:
                # 计算潜在涨跌幅
                upside = None
                if current_price and target_mean:
                    upside = round((target_mean - current_price) / current_price * 100, 1)

                rating_info = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'target_high': target_high,
                    'target_low': target_low,
                    'target_mean': target_mean,
                    'upside_pct': upside,
                    'recommendation': recommendation,
                    'num_analysts': num_analysts
                }
                all_ratings.append(rating_info)

            # 获取最近的升级/降级信息
            try:
                upgrades = ticker.upgrades_downgrades
                if upgrades is not None and not upgrades.empty:
                    # 取最近的几条
                    recent = upgrades.head(3)
                    for idx, row in recent.iterrows():
                        recent_changes.append({
                            'symbol': symbol,
                            'company': row.get('Firm', ''),
                            'from_grade': row.get('FromGrade', ''),
                            'to_grade': row.get('ToGrade', ''),
                            'action': row.get('Action', ''),
                            'date': str(idx)[:10] if idx else ''
                        })
            except Exception:
                pass

        except Exception as e:
            print(f"  Error fetching rating for {symbol}: {e}")
            continue

    # 按潜在涨幅排序
    all_ratings.sort(key=lambda x: x.get('upside_pct') or 0, reverse=True)

    # 按日期排序近期变化
    recent_changes.sort(key=lambda x: x.get('date', ''), reverse=True)

    result = {
        'date': today.strftime('%Y-%m-%d'),
        'fetch_time': today.strftime('%Y-%m-%d %H:%M:%S'),
        'ratings_count': len(all_ratings),
        'ratings': all_ratings,
        'recent_changes': recent_changes[:20]
    }

    # 保存到文件
    output_path = Path(__file__).parent.parent.parent / 'data' / 'ratings.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Fetched ratings for {len(all_ratings)} stocks, saved to {output_path}")
    return result


if __name__ == '__main__':
    data = fetch_ratings()
    print(f"\nTop ratings by upside:")
    for r in data['ratings'][:5]:
        upside = r.get('upside_pct')
        upside_str = f"+{upside}%" if upside else "N/A"
        print(f"  {r['symbol']}: Target ${r['target_mean']:.2f} ({upside_str}) - {r['recommendation']}")

    if data['recent_changes']:
        print(f"\nRecent changes:")
        for c in data['recent_changes'][:5]:
            print(f"  {c['symbol']}: {c['action']} by {c['company']}")
