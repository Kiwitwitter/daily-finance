"""财经日历抓取模块 - 使用网页抓取"""

import json
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup


def fetch_calendar() -> dict:
    """抓取财经日历（经济数据发布）- 从 Investing.com"""
    print("Fetching economic calendar...")

    today = datetime.now()
    events = []

    try:
        # 尝试从 Investing.com 抓取
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        url = 'https://www.investing.com/economic-calendar/'
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找日历表格行
            rows = soup.select('tr.js-event-item')

            for row in rows[:30]:  # 限制数量
                try:
                    time_elem = row.select_one('td.time')
                    country_elem = row.select_one('td.flagCur span')
                    event_elem = row.select_one('td.event a')
                    actual_elem = row.select_one('td.act')
                    forecast_elem = row.select_one('td.fore')
                    prev_elem = row.select_one('td.prev')

                    if event_elem:
                        event_time = time_elem.get_text(strip=True) if time_elem else ''
                        country = country_elem.get('title', '') if country_elem else ''
                        event_name = event_elem.get_text(strip=True) if event_elem else ''

                        # 只取美国数据
                        if 'United States' in country or 'USD' in (country_elem.get_text() if country_elem else ''):
                            events.append({
                                'time': f"{today.strftime('%Y-%m-%d')} {event_time}",
                                'country': 'US',
                                'event': event_name,
                                'impact': 'medium',
                                'actual': actual_elem.get_text(strip=True) if actual_elem else None,
                                'estimate': forecast_elem.get_text(strip=True) if forecast_elem else None,
                                'prev': prev_elem.get_text(strip=True) if prev_elem else None,
                                'unit': ''
                            })
                except Exception:
                    continue

    except Exception as e:
        print(f"  Warning: Could not fetch from Investing.com: {e}")
        # 返回空数据而不是失败
        events = []

    result = {
        'date': today.strftime('%Y-%m-%d'),
        'fetch_time': today.strftime('%Y-%m-%d %H:%M:%S'),
        'total_events': len(events),
        'us_events': events,
        'all_events': events,
        'note': 'Economic calendar data may be limited. Check Investing.com for full calendar.'
    }

    # 保存到文件
    output_path = Path(__file__).parent.parent.parent / 'data' / 'calendar.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Fetched {len(events)} US economic events for today, saved to {output_path}")
    return result


if __name__ == '__main__':
    data = fetch_calendar()
    print(f"\nToday's US Economic Events:")
    for event in data['us_events'][:10]:
        time_str = event['time'].split(' ')[-1] if ' ' in event['time'] else event['time']
        print(f"  {time_str} - {event['event']}")
        if event['estimate']:
            print(f"           Expected: {event['estimate']}, Previous: {event['prev']}")
