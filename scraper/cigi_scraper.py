import logging
from datetime import datetime

import requests

from config import START_DATE

logger = logging.getLogger(__name__)

CIGI_API_URL = "https://www.cigionline.org/api/search/"

# Map CIGI topic IDs to our categories (fallback before AI classification)
CIGI_TOPIC_MAP = {
    31: "AI",           # Artificial Intelligence
    32: "AI",           # Data Governance
    49: "AI",           # Transformative Technologies
    63: "AI",           # Intellectual Property
    21803: "AI",        # Digital Economy
    21805: "AI",        # Digital Governance
    21812: "AI",        # Quantum Technology
    40: "Security",     # National Security
    20732: "Security",  # Space Governance
    21806: "Security",  # Foreign Interference
    21808: "Security",  # Geopolitics
    21813: "Security",  # Surveillance
    81: "Trade",        # Trade
    48: "Finance",      # Financial Governance
    50: "Finance",      # G20/G7
    41: "Human Rights", # Democracy
    54: "Human Rights", # Human Rights
    21807: "Human Rights", # Freedom of Thought
    21809: "Human Rights", # Global Cooperation
    21810: "Climate",   # Climate/Environment
    37: "Climate",      # Environmental governance
}


def fetch_cigi_articles():
    articles = []
    offset = 0
    limit = 50

    while True:
        params = {
            "limit": limit,
            "offset": offset,
            "sort": "date",
            "contenttype": "Publication",
            "contentsubtype": [
                "Books", "CIGI Papers", "Conference Reports", "Essays",
                "Essay Series", "Policy Briefs", "Policy Memos",
                "Quick Insights", "Special Reports",
            ],
            "field": ["authors", "pdf_download", "publishing_date", "topics"],
        }

        resp = requests.get(CIGI_API_URL, params=params, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; ThinkTankMonitor/1.0)"
        })
        resp.raise_for_status()
        data = resp.json()

        items = data.get("items", [])
        if not items:
            break

        for item in items:
            pub_date_raw = item.get("publishing_date", "")
            pub_date = _parse_date(pub_date_raw)

            # Filter by start date
            if pub_date < START_DATE:
                # Since articles are sorted by date desc, once we're before START_DATE,
                # all remaining items will be older. Stop.
                logger.info(f"Reached articles before {START_DATE}, stopping CIGI fetch")
                return articles

            article_id = f"cigi-{item['id']}"

            # Map topics to categories
            topics = item.get("topics", [])
            categories = []
            for t in topics:
                cat = CIGI_TOPIC_MAP.get(t["id"])
                if cat and cat not in categories:
                    categories.append(cat)

            # Authors
            authors = [a["title"] for a in item.get("authors", [])]

            articles.append({
                "id": article_id,
                "source": "CIGI",
                "title": item.get("title", "").strip(),
                "title_zh": "",
                "link": f"https://www.cigionline.org{item['url']}" if item.get("url") else "",
                "description": item.get("snippet", "").strip(),
                "summary_zh": "",
                "authors": authors,
                "pubDate": pub_date,
                "categories": categories,
                "subjects": [t["title"] for t in topics],
                "type": "CIGI Publication",
            })

        total = data.get("meta", {}).get("total_count", 0)
        offset += limit
        if offset >= total:
            break

    return articles


def _parse_date(date_str):
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return date_str[:10] if len(date_str) >= 10 else date_str
