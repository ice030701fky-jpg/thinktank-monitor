import logging

from config import ARTICLES_FILE
from storage import load_articles, merge_new_articles, save_articles
from swp_scraper import fetch_swp_articles
from cigi_scraper import fetch_cigi_articles
from ai_processor import process_articles

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("=== ThinkTank Monitor: Daily Scraper ===")

    # Load existing articles
    existing_articles = load_articles(ARTICLES_FILE)
    logger.info(f"Loaded {len(existing_articles)} existing articles")

    all_scraped = []

    # Step 1: Scrape SWP
    logger.info("Scraping SWP RSS feed...")
    try:
        swp_articles = fetch_swp_articles()
        logger.info(f"Fetched {len(swp_articles)} articles from SWP")
        all_scraped.extend(swp_articles)
    except Exception as e:
        logger.error(f"Failed to scrape SWP: {e}")

    # Step 2: Scrape CIGI
    logger.info("Scraping CIGI API...")
    try:
        cigi_articles = fetch_cigi_articles()
        logger.info(f"Fetched {len(cigi_articles)} articles from CIGI")
        all_scraped.extend(cigi_articles)
    except Exception as e:
        logger.error(f"Failed to scrape CIGI: {e}")

    if not all_scraped:
        logger.info("No articles fetched from any source.")
        save_articles(ARTICLES_FILE, existing_articles)
        return

    # Step 3: Merge and find new articles
    merged, new_articles = merge_new_articles(existing_articles, all_scraped)
    logger.info(f"New articles: {len(new_articles)}, Total: {len(merged)}")

    if not new_articles:
        logger.info("No new articles found.")
        # Still update lastUpdated timestamp
        save_articles(ARTICLES_FILE, existing_articles)
        logger.info(f"Updated lastUpdated timestamp in {ARTICLES_FILE}")
        return

    # Step 4: AI processing for new articles
    logger.info("Starting AI classification and summarization...")
    new_articles = process_articles(new_articles)

    # Step 5: Update merged list with AI-processed articles
    for i, article in enumerate(merged):
        for new_article in new_articles:
            if new_article["id"] == article["id"]:
                merged[i] = new_article
                break

    # Step 6: Save
    save_articles(ARTICLES_FILE, merged)
    logger.info(f"Saved {len(merged)} articles to {ARTICLES_FILE}")

    # Print summary of new articles
    for article in new_articles:
        logger.info(f"  NEW: [{article['source']}] {article['title'][:80]}")
        logger.info(f"    Categories: {article.get('categories', [])}")
        logger.info(f"    Summary: {article.get('summary_zh', '')[:100]}...")


if __name__ == "__main__":
    main()
