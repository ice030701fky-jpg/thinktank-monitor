import json
import os
from datetime import datetime, timezone


def load_articles(filepath):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("articles", [])
    except (json.JSONDecodeError, KeyError):
        return []


def save_articles(filepath, articles):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    data = {
        "articles": articles,
        "lastUpdated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_existing_ids(articles):
    return {a["id"] for a in articles}


def merge_new_articles(existing, new_articles):
    existing_ids = get_existing_ids(existing)
    added = []
    for article in new_articles:
        if article["id"] not in existing_ids:
            existing.append(article)
            added.append(article)
    return existing, added
