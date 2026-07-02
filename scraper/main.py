import logging
import sys

from config import ARTICLES_FILE
from storage import load_articles, merge_new_articles, save_articles
from swp_scraper import fetch_swp_articles
from ai_processor import process_articles

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("=== ThinkTank Monitor: Daily Scraper ===")

    # Load existing articles
    existing_articles = load_articles(ARTICLES_FILE)
    logger.info(f"Loaded {len(existing_articles)} existing articles")

    # Step 1: Scrape SWP
    logger.info("Scraping SWP RSS feed...")
    try:
        swp_articles = fetch_swp_articles()
        logger.info(f"Fetched {len(swp_articles)} articles from SWP")
    except Exception as e:
        logger.error(f"Failed to scrape SWP: {e}")
        sys.exit(1)

    # Step 2: Merge and find new articles
    merged, new_articles = merge_new_articles(existing_articles, swp_articles)
    logger.info(f"New articles: {len(new_articles)}, Total: {len(merged)}")

    if not new_articles:
        logger.info("No new articles found. Done.")
        return

    # Step 3: AI processing for new articles
    logger.info("Starting AI classification and summarization...")
    new_articles = process_articles(new_articles)

    # Step 4: Update merged list with AI-processed articles
    for i, article in enumerate(merged):
        for new_article in new_articles:
            if new_article["id"] == article["id"]:
                merged[i] = new_article
                break

    # Step 5: Save
    save_articles(ARTICLES_FILE, merged)
    logger.info(f"Saved {len(merged)} articles to {ARTICLES_FILE}")

    # Print summary of new articles
    for article in new_articles:
        logger.info(f"  NEW: [{article['source']}] {article['title'][:80]}")
        logger.info(f"    Categories: {article.get('categories', [])}")
        logger.info(f"    Summary: {article.get('summary_zh', '')[:100]}...")


if __name__ == "__main__":
    main()
