# 美股财经日报自动化系统

每日自动抓取美股市场数据，生成包含期权数据、投行评级、财经日历、核心新闻等板块的财经日报。支持中英文切换。

## 功能特性

- **盘前市场汇总**：三大指数行情、财经日历、重点财报、投行评级、核心新闻、重点关注领域
- **期权市场日报**：市场概览、VIX 恐慌指数、Call/Put 占比、指数/个股期权成交量排行
- **智能分析**：使用 Claude Code 生成中英文双语新闻摘要和投资逻辑
- **股票悬浮详情**：hover 股票代码显示实时价格、涨跌幅、成交量等信息
- **多语言支持**：一键切换中文/英文界面

## 架构设计

### Docker + Local 混合架构

本项目采用 **Docker 容器** 与 **本地环境** 混合运行的架构：

```
┌─────────────────────────────────────────────────────────────┐
│                        本地环境 (Local)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Claude Code CLI                                     │   │
│  │  - 新闻智能分析                                        │   │
│  │  - 生成中英文摘要                                      │   │
│  │  - 无需额外 API 费用                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                 │
│                            │ 写入 data/analysis.json         │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    data/ 目录                         │   │
│  │  (本地与 Docker 共享)                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                 │
└────────────────────────────│─────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     Docker 容器 (Container)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  数据抓取     │  │  报告生成     │  │  Web 服务    │      │
│  │  - 期权数据   │  │  - Jinja2    │  │  - FastAPI   │      │
│  │  - 新闻评级   │  │  - HTML 渲染  │  │  - Port 8000 │      │
│  │  - 财经日历   │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Cloudflare Tunnel (可选)                              │   │
│  │  - 公网访问                                            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 为什么使用本地 Claude Code？

**智能分析模块** 使用本地安装的 [Claude Code CLI](https://claude.ai/code) 而非调用 API，原因如下：

1. **零额外成本**：Claude Code CLI 包含在 Claude Pro/Team 订阅中，无需额外支付 API 费用
2. **无需管理密钥**：不需要配置和保护 API Key
3. **相同质量**：使用相同的 Claude 模型，分析质量一致

## 技术栈

| 组件 | 技术 |
|------|------|
| 数据抓取 | Python + yfinance + finnhub-python |
| 智能分析 | Claude Code CLI (本地) |
| 模板渲染 | Jinja2 |
| Web 服务 | FastAPI + Uvicorn |
| 容器化 | Docker + Docker Compose |
| 公网访问 | Cloudflare Tunnel (可选) |

## 数据源

| 数据 | 来源 | 方式 |
|------|------|------|
| 期权成交量 | Yahoo Finance | yfinance |
| 股票价格/信息 | Yahoo Finance | yfinance |
| VIX 恐慌指数 | Yahoo Finance | yfinance |
| 财报日历 | Finnhub | REST API |
| 市场新闻 | Finnhub | REST API |
| 投行评级 | Yahoo Finance | yfinance |
| 财经日历 | Investing.com | 网页抓取 |

## 快速开始

### 前置要求

- Docker & Docker Compose
- Python 3.11+ (本地环境，用于 Claude 分析)
- [Claude Code CLI](https://claude.ai/code) (本地安装)
- Finnhub API Key (免费)

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone <repo-url>
   cd daily-finance
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env，填入你的 API Key
   ```

3. **启动 Docker 服务**
   ```bash
   docker-compose up -d --build
   ```

4. **运行完整工作流**
   ```bash
   ./scripts/run_all.sh
   ```

5. **访问报告**
   - 本地：http://localhost:8000
   - 公网：配置 Cloudflare Tunnel 后通过自定义域名访问

## 使用方法

### 手动运行完整流程

```bash
./scripts/run_all.sh
```

此脚本按顺序执行：
1. Docker 内抓取所有数据
2. 本地运行 Claude 智能分析
3. Docker 内生成 HTML 报告

### 单独运行各步骤

```bash
# 仅抓取数据 (Docker 内)
docker-compose exec web python scripts/daily_job.py

# 仅运行 Claude 分析 (本地)
python3 scripts/analyze.py

# 仅生成报告 (Docker 内)
docker-compose exec web python src/generators/build.py
```

### 定时自动运行

Docker 容器内置 cron 任务，每天美东时间 5:00 AM 自动抓取数据并生成报告。

如需包含 Claude 智能分析，可在本地设置 cron：

```bash
# 编辑本地 crontab
crontab -e

# 添加定时任务 (美东 5:00 AM = UTC 10:00 AM)
0 10 * * * cd /path/to/daily-finance && ./scripts/run_all.sh >> logs/local.log 2>&1
```

## 项目结构

```
daily-finance/
├── src/
│   ├── scrapers/          # 数据抓取模块
│   │   ├── options.py     # 期权数据
│   │   ├── news.py        # 新闻数据
│   │   ├── ratings.py     # 投行评级
│   │   ├── econ_calendar.py # 财经日历
│   │   ├── earnings.py    # 财报日历
│   │   └── stock_info.py  # 股票信息
│   ├── analyzers/         # 智能分析模块
│   │   └── news_analyzer.py # Claude 新闻分析
│   ├── generators/        # 报告生成模块
│   │   ├── build.py       # 报告构建
│   │   └── templates/     # HTML 模板
│   └── server/            # Web 服务
│       └── app.py         # FastAPI 应用
├── scripts/
│   ├── run_all.sh         # 完整工作流脚本
│   ├── analyze.py         # 本地 Claude 分析
│   └── daily_job.py       # Docker 内定时任务
├── data/                  # 数据文件 (gitignore)
├── output/                # 生成的报告 (gitignore)
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

## 配置说明

### 环境变量 (.env)

| 变量 | 说明 | 必需 |
|------|------|------|
| `FINNHUB_API_KEY` | Finnhub API 密钥 | 是 |
| `TZ` | 时区设置 | 是 |
| `CLOUDFLARE_TUNNEL_TOKEN` | Cloudflare Tunnel 令牌 | 否 |

### Cloudflare Tunnel - 使用 Mac 作为服务器

本项目使用 **Cloudflare Tunnel** 将本地 Mac（如 Mac Studio）作为 Web 服务器，无需公网 IP 即可提供公网访问。

#### 为什么选择这种方案？

| 优势 | 说明 |
|------|------|
| **零成本** | 无需租用云服务器，利用现有 Mac 硬件 |
| **安全** | 无需开放端口，所有流量通过 Cloudflare 加密隧道 |
| **简单** | 无需配置防火墙、端口转发、DDNS |
| **高性能** | Mac Studio 性能远超同价位云服务器 |

#### 架构说明

```
用户浏览器
    │
    ▼
finance.yourdomain.com (Cloudflare DNS)
    │
    │  Cloudflare 全球 CDN
    ▼
Cloudflare Edge Server
    │
    │  加密隧道 (Tunnel)
    ▼
┌─────────────────────────────┐
│  你的 Mac Studio (本地)      │
│  ┌───────────────────────┐  │
│  │ cloudflared (容器)     │  │
│  │   ↓                   │  │
│  │ FastAPI (容器)         │  │
│  │   Port 8000           │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

#### 配置步骤

1. **登录 Cloudflare Zero Trust Dashboard**
   - 访问 https://one.dash.cloudflare.com/
   - 进入 Networks → Tunnels

2. **创建 Tunnel**
   - 点击 "Create a tunnel"
   - 选择 "Cloudflared" 类型
   - 命名你的 Tunnel（如 `financial-daily`）
   - 复制生成的 Token

3. **配置环境变量**
   ```bash
   # 编辑 .env 文件
   CLOUDFLARE_TUNNEL_TOKEN=你复制的Token
   ```

4. **配置公共主机名**
   - 在 Tunnel 配置页面，添加 Public Hostname
   - Subdomain: `finance`（或你喜欢的名称）
   - Domain: 选择你的域名
   - Service: `http://localhost:8000`

5. **启动服务**
   ```bash
   docker-compose up -d
   ```

6. **验证访问**
   - 访问 `https://finance.yourdomain.com`
   - 应该能看到财经日报页面

#### 注意事项

- Mac 需要保持开机和联网状态
- 建议在"系统设置 → 节能"中禁用自动休眠
- Tunnel 断开会自动重连，但长时间断网需手动检查

## License

本项目采用 [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.html) 开源协议。

