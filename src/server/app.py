"""FastAPI Web 服务"""

import os
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

# 路径配置
BASE_DIR = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE_DIR / 'output'

app = FastAPI(title="美股财经日报", version="1.0.0")


# 添加 Cache-Control 中间件，防止 Cloudflare 缓存
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # 对所有页面禁用缓存
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


app.add_middleware(NoCacheMiddleware)

# 挂载静态文件目录
if (OUTPUT_DIR / 'assets').exists():
    app.mount("/assets", StaticFiles(directory=OUTPUT_DIR / 'assets'), name="assets")


@app.get("/", response_class=HTMLResponse)
async def index():
    """首页 - 显示最新报告"""
    index_file = OUTPUT_DIR / 'index.html'
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding='utf-8'))

    # 如果没有报告，显示提示页面
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>美股财经日报</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                   display: flex; justify-content: center; align-items: center;
                   min-height: 100vh; margin: 0; background: #f5f5f5; }
            .message { text-align: center; padding: 40px; background: white;
                       border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            h1 { color: #1a73e8; }
            p { color: #666; }
        </style>
    </head>
    <body>
        <div class="message">
            <h1>美股财经日报</h1>
            <p>暂无报告。请先运行数据抓取和报告生成脚本。</p>
        </div>
    </body>
    </html>
    """)


@app.get("/report/{date}", response_class=HTMLResponse)
async def get_report(date: str, report_type: str = "premarket"):
    """获取指定日期的报告"""
    # 验证日期格式
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # 查找报告文件
    report_file = OUTPUT_DIR / f'{date}-{report_type}.html'
    if not report_file.exists():
        # 尝试不带类型的文件名
        report_file = OUTPUT_DIR / f'{date}.html'

    if report_file.exists():
        return HTMLResponse(content=report_file.read_text(encoding='utf-8'))

    raise HTTPException(status_code=404, detail=f"Report for {date} not found")


def get_reports_list():
    """获取报告列表数据"""
    reports = []

    if OUTPUT_DIR.exists():
        for file in OUTPUT_DIR.glob('*.html'):
            if file.name == 'index.html':
                continue

            # 解析文件名获取日期和类型
            name = file.stem
            parts = name.split('-')

            if len(parts) >= 3:
                date = '-'.join(parts[:3])
                report_type = parts[3] if len(parts) > 3 else 'daily'
            else:
                date = name
                report_type = 'daily'

            # 类型显示名称
            type_names = {
                'daily': '综合日报',
                'premarket': '盘前报告',
                'options': '期权日报',
            }
            type_display = type_names.get(report_type, report_type)

            reports.append({
                'date': date,
                'type': report_type,
                'type_display': type_display,
                'filename': file.name,
                'url': f'/report/{date}?report_type={report_type}'
            })

    # 按日期降序排列
    reports.sort(key=lambda x: (x['date'], x['type']), reverse=True)
    return reports


@app.get("/reports", response_class=HTMLResponse)
async def list_reports():
    """列出所有可用报告 - HTML 页面"""
    reports = get_reports_list()

    # 按日期分组
    reports_by_date = {}
    for report in reports:
        date = report['date']
        if date not in reports_by_date:
            reports_by_date[date] = []
        reports_by_date[date].append(report)

    # 生成 HTML
    reports_html = ""
    for date in sorted(reports_by_date.keys(), reverse=True):
        date_reports = reports_by_date[date]
        links_html = ""
        for r in date_reports:
            links_html += f'<a href="{r["url"]}" class="report-type-link">{r["type_display"]}</a>'

        reports_html += f'''
        <div class="report-item">
            <div class="report-date">{date}</div>
            <div class="report-links">{links_html}</div>
        </div>
        '''

    html = f'''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>历史报告 - 美股财经日报</title>
        <link rel="stylesheet" href="/assets/styles.css">
        <style>
            .reports-container {{
                max-width: 800px;
                margin: 0 auto;
            }}
            .report-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 20px;
                background: var(--card-bg);
                border-radius: 8px;
                margin-bottom: 12px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }}
            .report-item:hover {{
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }}
            .report-date {{
                font-size: 18px;
                font-weight: 600;
                color: var(--text-color);
            }}
            .report-links {{
                display: flex;
                gap: 12px;
            }}
            .report-type-link {{
                padding: 6px 16px;
                background: var(--primary-color);
                color: white;
                text-decoration: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 500;
                transition: background 0.2s;
            }}
            .report-type-link:hover {{
                background: #1557b0;
            }}
            .page-title {{
                text-align: center;
                margin-bottom: 32px;
            }}
            .page-title h2 {{
                font-size: 28px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
            .page-title p {{
                color: var(--text-secondary);
            }}
            .no-reports {{
                text-align: center;
                padding: 60px 20px;
                color: var(--text-secondary);
            }}
        </style>
    </head>
    <body>
        <header class="header">
            <div class="container">
                <a href="/" class="logo" data-i18n="siteTitle">美股财经日报</a>
                <div class="header-right">
                    <nav class="nav">
                        <a href="/" data-i18n="latestReport">最新报告</a>
                        <a href="/reports" data-i18n="historyReports">历史报告</a>
                    </nav>
                    <div class="lang-toggle" onclick="toggleLanguage()">
                        <span class="lang-option" data-lang="zh">中</span>
                        <span class="lang-option" data-lang="en">EN</span>
                    </div>
                </div>
            </div>
        </header>

        <main class="main">
            <div class="container">
                <div class="reports-container">
                    <div class="page-title">
                        <h2 data-i18n="historyReportsTitle">历史报告</h2>
                        <p data-i18n="historyReportsDesc">查看往期财经日报</p>
                    </div>
                    {reports_html if reports_html else '<div class="no-reports" data-i18n="noHistoryReports">暂无历史报告</div>'}
                </div>
            </div>
        </main>

        <footer class="footer">
            <div class="container">
                <p data-i18n="dataSource">数据来源：Yahoo Finance, Finnhub, Investing.com</p>
            </div>
        </footer>

        <script>
        const translations = {{
            zh: {{
                siteTitle: '美股财经日报',
                latestReport: '最新报告',
                historyReports: '历史报告',
                historyReportsTitle: '历史报告',
                historyReportsDesc: '查看往期财经日报',
                noHistoryReports: '暂无历史报告',
                dataSource: '数据来源：Yahoo Finance, Finnhub, Investing.com',
                dailyReport: '综合日报',
                premarketReport: '盘前报告',
                optionsReport: '期权日报'
            }},
            en: {{
                siteTitle: 'US Stock Daily',
                latestReport: 'Latest',
                historyReports: 'History',
                historyReportsTitle: 'Report History',
                historyReportsDesc: 'View past daily reports',
                noHistoryReports: 'No reports available',
                dataSource: 'Data: Yahoo Finance, Finnhub, Investing.com',
                dailyReport: 'Daily Report',
                premarketReport: 'Pre-Market',
                optionsReport: 'Options'
            }}
        }};

        function getCurrentLang() {{
            return localStorage.getItem('lang') || 'zh';
        }}

        function toggleLanguage() {{
            const currentLang = getCurrentLang();
            const newLang = currentLang === 'zh' ? 'en' : 'zh';
            localStorage.setItem('lang', newLang);
            applyLanguage(newLang);
        }}

        function applyLanguage(lang) {{
            document.querySelectorAll('[data-i18n]').forEach(el => {{
                const key = el.getAttribute('data-i18n');
                if (translations[lang][key]) {{
                    el.textContent = translations[lang][key];
                }}
            }});

            document.querySelectorAll('.lang-option').forEach(opt => {{
                opt.classList.toggle('active', opt.getAttribute('data-lang') === lang);
            }});

            document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';

            // 翻译报告类型链接
            document.querySelectorAll('.report-type-link').forEach(link => {{
                const text = link.textContent.trim();
                if (lang === 'en') {{
                    if (text === '综合日报') link.textContent = 'Daily Report';
                    else if (text === '盘前报告') link.textContent = 'Pre-Market';
                    else if (text === '期权日报') link.textContent = 'Options';
                }} else {{
                    if (text === 'Daily Report') link.textContent = '综合日报';
                    else if (text === 'Pre-Market') link.textContent = '盘前报告';
                    else if (text === 'Options') link.textContent = '期权日报';
                }}
            }});
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            applyLanguage(getCurrentLang());
        }});
        </script>
    </body>
    </html>
    '''

    return HTMLResponse(content=html)


@app.get("/api/reports")
async def api_reports():
    """API: 获取报告列表 (JSON)"""
    return {'reports': get_reports_list()}


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """启动服务器"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == '__main__':
    start_server()
