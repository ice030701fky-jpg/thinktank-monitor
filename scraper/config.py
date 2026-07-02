import os

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"

SWP_RSS_URL = "https://www.swp-berlin.org/en/SWPPublications.xml"

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
ARTICLES_FILE = os.path.join(DATA_DIR, "articles.json")

START_DATE = "2026-06-01"

TOPICS = ["AI", "Security", "Trade", "Climate", "Finance", "Human Rights"]

TOPIC_LABELS = {
    "AI": "AI 人工智能",
    "Security": "安全",
    "Trade": "贸易",
    "Climate": "气候",
    "Finance": "金融",
    "Human Rights": "人权",
}
