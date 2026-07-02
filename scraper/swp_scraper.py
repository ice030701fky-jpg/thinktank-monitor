import re
from datetime import datetime

import requests
from lxml import etree

from config import SWP_RSS_URL, START_DATE

NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
}


def parse_pubdate(date_str):
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        try:
            dt = datetime.strptime(date_str.strip(), "%a, %d %b %Y %H:%M:%S %z")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return date_str.strip()


def clean_html(raw_html):
    if not raw_html:
        return ""
    clean = re.compile(r"<[^>]+>")
    text = clean.sub("", raw_html)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&apos;", "'")
    text = " ".join(text.split())
    return text.strip()


def fetch_swp_articles():
    resp = requests.get(SWP_RSS_URL, timeout=30, headers={
        "User-Agent": "Mozilla/5.0 (compatible; ThinkTankMonitor/1.0; +https://github.com)"
    })
    resp.raise_for_status()

    root = etree.fromstring(resp.content)
    articles = []

    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        description_raw = item.findtext("description", "")
        description = clean_html(description_raw)
        pubdate_raw = item.findtext("pubDate", "")
        pub_date = parse_pubdate(pubdate_raw)
        identifier = item.findtext(f"{{{NS['dc']}}}identifier", "").strip()
        category = item.findtext("category", "").strip()

        # Authors
        creator = item.findtext(f"{{{NS['dc']}}}creator", "").strip()
        authors = [a.strip() for a in creator.split(";") if a.strip()] if creator else []

        # Subjects
        subjects = []
        for subj in item.findall(f"{{{NS['dc']}}}subject"):
            text = subj.text.strip() if subj.text else ""
            if text:
                subjects.append(text)

        article_id = f"swp-{identifier}" if identifier else f"swp-{hash(link)}"

        articles.append({
            "id": article_id,
            "source": "SWP",
            "title": title,
            "title_zh": "",
            "link": link,
            "description": description,
            "summary_zh": "",
            "authors": authors,
            "pubDate": pub_date or "",
            "categories": [],
            "subjects": subjects,
            "type": category,
        })

    # Filter by start date
    articles = [a for a in articles if a["pubDate"] >= START_DATE]

    return articles
