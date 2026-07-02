import json
import logging
import time

import requests

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, TOPICS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位专业的智库研究分析师。请完成以下任务：

1. 将文章分类到以下一个或多个主题（仅从列表中选择）：
   - AI（人工智能相关，包括数字政策、网络安全、技术治理）
   - Security（安全相关，包括国防、军事、地区冲突、反恐）
   - Trade（贸易相关，包括国际贸易、经济制裁、供应链）
   - Climate（气候相关，包括环境政策、能源转型、可持续发展）
   - Finance（金融相关，包括全球经济、货币政策、金融监管）
   - Human Rights（人权相关，包括民主治理、国际法、人道主义）

2. 将文章标题翻译为简洁的中文

3. 生成一段中文摘要（150-300字），概括文章的核心观点和论证

请严格按以下JSON格式返回，不要包含markdown代码块标记或其他文字：
{"categories": ["主题1"], "title_zh": "中文标题", "summary_zh": "文章摘要内容..."}"""


def classify_and_summarize(article):
    title = article.get("title", "")
    description = article.get("description", "")
    subjects = article.get("subjects", [])
    article_type = article.get("type", "")

    user_content = f"""标题: {title}
描述: {description}
关键词: {", ".join(subjects) if subjects else "无"}
类型: {article_type or "未知"}"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
            content = result["choices"][0]["message"]["content"].strip()

            # Clean markdown code blocks if present
            if content.startswith("```"):
                lines = content.split("\n")
                lines = [l for l in lines if not l.startswith("```")]
                content = "\n".join(lines).strip()

            parsed = json.loads(content)

            categories = parsed.get("categories", [])
            valid_categories = [c for c in categories if c in TOPICS]
            if not valid_categories:
                valid_categories = ["Security"]

            return {
                "categories": valid_categories,
                "title_zh": parsed.get("title_zh", ""),
                "summary_zh": parsed.get("summary_zh", ""),
            }

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Attempt {attempt + 1} failed for '{title}': {e}")
            logger.warning(f"Raw content: {content[:200] if 'content' in dir() else 'N/A'}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
        except requests.RequestException as e:
            logger.error(f"API request failed for '{title}': {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    # Fallback: return empty results
    logger.error(f"All {max_retries} attempts failed for '{title}', using fallback")
    return {
        "categories": ["Security"],
        "title_zh": "",
        "summary_zh": description[:200] if description else "",
    }


def process_articles(articles):
    if not DEEPSEEK_API_KEY:
        logger.warning("DEEPSEEK_API_KEY not set, skipping AI processing")
        return articles

    processed = []
    for i, article in enumerate(articles):
        logger.info(f"Processing [{i + 1}/{len(articles)}]: {article['title'][:60]}...")

        # Skip articles that already have AI processing
        if article.get("summary_zh") and article.get("categories"):
            processed.append(article)
            continue

        ai_result = classify_and_summarize(article)

        article["categories"] = ai_result["categories"]
        article["title_zh"] = ai_result["title_zh"]
        article["summary_zh"] = ai_result["summary_zh"]

        processed.append(article)

        # Rate limiting: wait between requests
        if i < len(articles) - 1:
            time.sleep(1)

    return processed
