"""报告生成模块 - 使用 Jinja2 渲染 HTML"""

import json
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


# 路径配置
BASE_DIR = Path(__file__).parent.parent.parent
TEMPLATE_DIR = Path(__file__).parent / 'templates'
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'output'


def load_json(filename: str) -> dict:
    """加载 JSON 数据文件"""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def setup_output_dir():
    """初始化输出目录"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    assets_dir = OUTPUT_DIR / 'assets'
    assets_dir.mkdir(exist_ok=True)

    # 复制 CSS 文件
    css_src = TEMPLATE_DIR / 'styles.css'
    css_dst = assets_dir / 'styles.css'
    if css_src.exists():
        shutil.copy(css_src, css_dst)


def build_premarket_report(analysis_data: dict = None) -> str:
    """生成盘前报告 HTML"""
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('premarket.html')

    # 加载数据
    calendar_data = load_json('calendar.json')
    earnings_data = load_json('earnings.json')
    ratings_data = load_json('ratings.json')
    news_data = load_json('news.json')
    stock_info_data = load_json('stock_info.json')
    stock_info = stock_info_data.get('stocks', {}) if stock_info_data else {}

    today = datetime.now().strftime('%Y-%m-%d')

    # 处理日历事件
    calendar_events = []
    if calendar_data.get('us_events'):
        for event in calendar_data['us_events'][:10]:
            calendar_events.append({
                'time': event.get('time', '')[11:16],  # 只取时间部分
                'event': event.get('event', ''),
                'estimate': event.get('estimate'),
                'prev': event.get('prev')
            })

    # 处理财报数据
    earnings = None
    if earnings_data:
        earnings = {
            'before_market': earnings_data.get('before_market', [])[:10],
            'after_market': earnings_data.get('after_market', [])[:10]
        }

    # 处理评级变化 - 合并目标价数据
    recent_changes = ratings_data.get('recent_changes', [])[:10]
    ratings_dict = {r['symbol']: r for r in ratings_data.get('ratings', [])}

    rating_changes = []
    for change in recent_changes:
        symbol = change.get('symbol')
        rating_info = ratings_dict.get(symbol, {})
        rating_changes.append({
            **change,
            'target_mean': rating_info.get('target_mean'),
            'upside_pct': rating_info.get('upside_pct'),
            'current_price': rating_info.get('current_price'),
        })

    # 智能分析数据（由外部提供或使用默认值）
    core_news = []
    focus_areas = []

    if analysis_data:
        core_news = analysis_data.get('core_news', [])
        focus_areas = analysis_data.get('focus_areas', [])
    else:
        # 默认使用原始新闻标题
        if news_data.get('news'):
            for i, news in enumerate(news_data['news'][:7], 1):
                core_news.append({
                    'tag': '市场',
                    'summary': news.get('headline', '')[:60]
                })

    # 渲染 HTML
    html = template.render(
        date=today,
        update_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        calendar_events=calendar_events,
        earnings=earnings,
        rating_changes=rating_changes,
        core_news=core_news,
        focus_areas=focus_areas,
        stock_info=stock_info
    )

    # 保存文件
    setup_output_dir()

    # 保存为日期命名的文件
    output_file = OUTPUT_DIR / f'{today}-premarket.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    # 同时更新 index.html
    index_file = OUTPUT_DIR / 'index.html'
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Premarket report saved to {output_file}")
    return str(output_file)


def build_options_report(analysis_data: dict = None) -> str:
    """生成期权日报 HTML"""
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('options.html')

    # 加载数据
    options_data = load_json('options.json')

    today = datetime.now().strftime('%Y-%m-%d')

    # 处理市场概览
    market_overview = options_data.get('market_overview', {})

    # 添加情绪样式类
    sentiment = market_overview.get('sentiment', '中性')
    if '看涨' in sentiment:
        market_overview['sentiment_class'] = 'bullish'
    elif '看跌' in sentiment:
        market_overview['sentiment_class'] = 'bearish'
    else:
        market_overview['sentiment_class'] = ''

    # 处理指数期权数据
    index_options = []
    for idx in options_data.get('index_options', []):
        total = idx.get('total_volume', 0)
        call_vol = idx.get('call_volume', 0)
        put_vol = idx.get('put_volume', 0)

        call_pct = round(call_vol / total * 100) if total > 0 else 50
        put_pct = 100 - call_pct

        index_options.append({
            **idx,
            'call_pct': call_pct,
            'put_pct': put_pct
        })

    # 个股期权 TOP 25
    top_25_stocks = options_data.get('top_25_stocks', [])

    # 智能分析（由外部提供）
    analysis = analysis_data.get('analysis', '') if analysis_data else ''

    # 渲染 HTML
    html = template.render(
        date=today,
        update_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        market_overview=market_overview,
        index_options=index_options,
        top_25_stocks=top_25_stocks,
        analysis=analysis
    )

    # 保存文件
    setup_output_dir()

    output_file = OUTPUT_DIR / f'{today}-options.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Options report saved to {output_file}")
    return str(output_file)


def get_file_update_time(filename: str) -> str:
    """获取数据文件的更新时间（EDT时区格式）"""
    filepath = DATA_DIR / filename
    if filepath.exists():
        mtime = filepath.stat().st_mtime
        return datetime.fromtimestamp(mtime).strftime('%Y/%m/%d %H:%M EDT')
    return '--'


def build_combined_report(premarket_analysis: dict = None, options_analysis: dict = None) -> str:
    """生成合并的日报 HTML（带 Tab 切换）"""
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('combined.html')

    today = datetime.now().strftime('%Y-%m-%d')

    # ===== 盘前数据 =====
    calendar_data = load_json('calendar.json')
    earnings_data = load_json('earnings.json')
    ratings_data = load_json('ratings.json')
    news_data = load_json('news.json')
    stock_info_data = load_json('stock_info.json')
    stock_info = stock_info_data.get('stocks', {}) if stock_info_data else {}

    # 处理日历事件
    calendar_events = []
    if calendar_data.get('us_events'):
        for event in calendar_data['us_events'][:10]:
            calendar_events.append({
                'time': event.get('time', '')[11:16],
                'event': event.get('event', ''),
                'estimate': event.get('estimate'),
                'prev': event.get('prev')
            })

    # 处理财报数据
    earnings = None
    if earnings_data:
        earnings = {
            'before_market': earnings_data.get('before_market', [])[:10],
            'after_market': earnings_data.get('after_market', [])[:10]
        }

    # 处理评级变化 - 按股票合并
    recent_changes = ratings_data.get('recent_changes', [])[:20]  # 取更多以便合并
    ratings_dict = {r['symbol']: r for r in ratings_data.get('ratings', [])}

    # 按股票分组
    grouped = {}
    for change in recent_changes:
        symbol = change.get('symbol')
        if symbol not in grouped:
            rating_info = ratings_dict.get(symbol, {})
            grouped[symbol] = {
                'symbol': symbol,
                'target_mean': rating_info.get('target_mean'),
                'upside_pct': rating_info.get('upside_pct'),
                'current_price': rating_info.get('current_price'),
                'firms': []
            }
        grouped[symbol]['firms'].append({
            'company': change.get('company'),
            'action': change.get('action'),
            'from_grade': change.get('from_grade'),
            'to_grade': change.get('to_grade'),
            'date': change.get('date')
        })

    # 转为列表，限制显示数量
    rating_changes = list(grouped.values())[:8]

    # 智能分析数据 - 优先从 analysis.json 读取
    analysis_data = load_json('analysis.json')
    core_news = []
    focus_areas = []

    if analysis_data:
        core_news = analysis_data.get('core_news', [])
        focus_areas = analysis_data.get('focus_areas', [])
    elif premarket_analysis:
        core_news = premarket_analysis.get('core_news', [])
        focus_areas = premarket_analysis.get('focus_areas', [])
    else:
        if news_data.get('news'):
            for i, news in enumerate(news_data['news'][:7], 1):
                core_news.append({
                    'tag': '市场',
                    'summary': news.get('headline', '')[:60]
                })

    # ===== 期权数据 =====
    options_data = load_json('options.json')
    market_overview = options_data.get('market_overview', {})

    sentiment = market_overview.get('sentiment', '中性')
    if '看涨' in sentiment:
        market_overview['sentiment_class'] = 'bullish'
    elif '看跌' in sentiment:
        market_overview['sentiment_class'] = 'bearish'
    else:
        market_overview['sentiment_class'] = ''

    index_options = []
    for idx in options_data.get('index_options', []):
        total = idx.get('total_volume', 0)
        call_vol = idx.get('call_volume', 0)
        put_vol = idx.get('put_volume', 0)
        call_pct = round(call_vol / total * 100) if total > 0 else 50
        put_pct = 100 - call_pct
        # 计算 P/C 比率
        pc_ratio = round(put_vol / call_vol, 2) if call_vol > 0 else 0
        index_options.append({
            **idx,
            'call_pct': call_pct,
            'put_pct': put_pct,
            'pc_ratio': pc_ratio
        })

    # 处理 top 25 股票，添加 P/C 比率
    top_25_stocks = []
    for stock in options_data.get('top_25_stocks', []):
        call_vol = stock.get('call_volume', 0)
        put_vol = stock.get('put_volume', 0)
        pc_ratio = round(put_vol / call_vol, 2) if call_vol > 0 else 0
        top_25_stocks.append({
            **stock,
            'pc_ratio': pc_ratio
        })

    # ===== 获取更新时间 =====
    # 盘前数据更新时间取最新的数据文件
    premarket_files = ['calendar.json', 'earnings.json', 'ratings.json', 'news.json']
    premarket_times = [get_file_update_time(f) for f in premarket_files]
    premarket_update_time = max(premarket_times) if premarket_times else '--:--'

    options_update_time = get_file_update_time('options.json')

    # 渲染 HTML
    html = template.render(
        date=today,
        premarket_update_time=premarket_update_time,
        options_update_time=options_update_time,
        # 盘前数据
        calendar_events=calendar_events,
        earnings=earnings,
        rating_changes=rating_changes,
        core_news=core_news,
        focus_areas=focus_areas,
        stock_info=stock_info,
        # 期权数据
        market_overview=market_overview,
        index_options=index_options,
        top_25_stocks=top_25_stocks,
    )

    # 保存文件
    setup_output_dir()

    output_file = OUTPUT_DIR / f'{today}-daily.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    # 同时更新 index.html
    index_file = OUTPUT_DIR / 'index.html'
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Combined report saved to {output_file}")
    return str(output_file)


def main():
    parser = argparse.ArgumentParser(description='Build financial reports')
    parser.add_argument('--type', choices=['premarket', 'options', 'both', 'combined'],
                        default='combined', help='Report type to generate')
    args = parser.parse_args()

    if args.type == 'combined':
        build_combined_report()
    elif args.type == 'both':
        build_premarket_report()
        build_options_report()
    elif args.type == 'premarket':
        build_premarket_report()
    elif args.type == 'options':
        build_options_report()


if __name__ == '__main__':
    main()
