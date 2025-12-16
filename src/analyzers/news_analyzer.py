"""新闻智能分析模块 - 使用 Claude Code CLI 生成中文摘要和投资逻辑"""

import json
import subprocess
import sys
from pathlib import Path

# 路径配置
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'


def load_json(filename: str) -> dict:
    """加载 JSON 数据文件"""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def analyze_news() -> dict:
    """使用 Claude Code CLI 分析新闻并生成中文摘要"""

    # 加载原始数据
    news_data = load_json('news.json')
    ratings_data = load_json('ratings.json')
    options_data = load_json('options.json')
    earnings_data = load_json('earnings.json')

    # 准备新闻内容
    news_list = news_data.get('news', [])[:15]
    news_text = "\n".join([
        f"- {n.get('headline', '')} (相关股票: {', '.join(n.get('related', []))})"
        for n in news_list
    ])

    # 准备评级变化
    rating_changes = ratings_data.get('recent_changes', [])[:10]
    ratings_text = "\n".join([
        f"- {r.get('symbol')}: {r.get('firm')} {r.get('action', '')} to {r.get('to_grade', '')}"
        for r in rating_changes
    ])

    # 准备期权数据
    market_overview = options_data.get('market_overview', {})
    top_stocks = options_data.get('top_25_stocks', [])[:10]
    options_text = f"""
市场情绪: {market_overview.get('sentiment', 'N/A')}
P/C Ratio: {market_overview.get('pc_ratio', 'N/A')}
期权成交量 TOP 5: {', '.join([s.get('symbol', '') for s in top_stocks[:5]])}
"""

    # 准备财报日历
    before_market = earnings_data.get('before_market', [])[:5]
    after_market = earnings_data.get('after_market', [])[:5]
    earnings_text = f"""
盘前财报: {', '.join([e.get('symbol', '') for e in before_market])}
盘后财报: {', '.join([e.get('symbol', '') for e in after_market])}
"""

    # 构建 prompt
    prompt = f"""你是一位专业的美股市场分析师。请基于以下今日市场数据，生成简洁的分析报告，同时提供中文和英文版本。

## 今日新闻
{news_text}

## 投行评级变化
{ratings_text}

## 期权市场数据
{options_text}

## 今日财报
{earnings_text}

请按以下 JSON 格式输出分析结果，只输出 JSON，不要其他任何内容：

{{
    "core_news": [
        {{
            "tag": "中文分类标签(如:科技/金融/宏观/能源等)",
            "tag_en": "English tag (e.g., Tech/Finance/Macro/Energy)",
            "summary": "一句话中文摘要，包含投资逻辑",
            "summary_en": "One-line English summary with investment insight"
        }},
        // 最多 7 条核心新闻
    ],
    "focus_areas": [
        {{
            "title": "中文关注领域名称",
            "title_en": "English focus area name",
            "reason": "为什么今天需要关注这个领域",
            "reason_en": "Why this area deserves attention today"
        }},
        // 3-5 个今日重点关注领域
    ]
}}

要求：
1. 中文摘要要简洁有力，突出投资价值
2. 英文翻译要地道专业，符合金融行业表达习惯
3. tag/tag_en 使用简短的分类标签
4. focus_areas 要结合新闻、评级、期权数据综合分析
5. 只输出纯 JSON，不要 markdown 代码块，不要任何其他文字"""

    # 调用 Claude Code CLI
    try:
        result = subprocess.run(
            ['claude', '-p', prompt, '--output-format', 'text'],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            print(f"Claude CLI error: {result.stderr}")
            return get_default_result(news_list)

        response_text = result.stdout.strip()

        # 尝试提取 JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        # 找到 JSON 的开始和结束
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            response_text = response_text[start_idx:end_idx]

        result_data = json.loads(response_text.strip())

        # 保存分析结果
        output_file = DATA_DIR / 'analysis.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        print(f"Analysis saved to {output_file}")
        return result_data

    except subprocess.TimeoutExpired:
        print("Claude CLI timeout")
        return get_default_result(news_list)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Response was: {response_text[:500]}")
        return get_default_result(news_list)
    except Exception as e:
        print(f"Error: {e}")
        return get_default_result(news_list)


def get_default_result(news_list: list) -> dict:
    """返回默认结果"""
    return {
        "core_news": [
            {"tag": "市场", "summary": n.get('headline', '')[:60]}
            for n in news_list[:7]
        ],
        "focus_areas": []
    }


def main():
    """主函数"""
    print("Starting news analysis with Claude Code CLI...")
    result = analyze_news()
    print(f"Generated {len(result.get('core_news', []))} news summaries")
    print(f"Generated {len(result.get('focus_areas', []))} focus areas")


if __name__ == '__main__':
    main()
