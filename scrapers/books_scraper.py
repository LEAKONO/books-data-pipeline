import requests
import json
import time
import logging
import os
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


BASE_URL = "http://books.toscrape.com"
CATALOGUE_URL = "http://books.toscrape.com/catalogue"

REQUEST_DELAY = 0.5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}


def get_total_pages() -> int:
    """Find out how many pages of books exist"""
    url = f"{CATALOGUE_URL}/page-1.html"
    soup = fetch_page(url)
    
    if soup is None:
        logger.warning("Could not fetch first page, defaulting to 50 pages")
        return 50
    
    # Find the pagination section
    pagination = soup.select("ul.pager li.current")
    if pagination:
        # Text looks like: "Page 1 of 50"
        text = pagination[0].text.strip()
        parts = text.split()
        if len(parts) >= 3:
            try:
                total_pages = int(parts[-1])
                logger.info(f"Found {total_pages} total pages")
                return total_pages
            except ValueError:
                pass
    
    # Alternative: count "next" buttons or default to 50
    logger.info("Could not determine total pages, defaulting to 50")
    return 50


def fetch_page(url: str) -> BeautifulSoup | None:
    try:
        logger.info(f"Fetching: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching {url}: {e}")
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection failed: {url}")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout: {url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Unexpected error fetching {url}: {e}")

    return None


def get_book_urls_from_listing(page_number: int) -> list[str]:
    url = f"{CATALOGUE_URL}/page-{page_number}.html"
    soup = fetch_page(url)

    if soup is None:
        logger.warning(f"Skipping listing page {page_number} - fetch failed")
        return []

    articles = soup.select("article.product_pod")
    urls = []

    for article in articles:
        anchor = article.select_one("h3 a")
        if anchor and anchor.get("href"):
            relative_url = anchor["href"].replace("../", "")
            full_url = f"{CATALOGUE_URL}/{relative_url}"
            urls.append(full_url)

    logger.info(f"Found {len(urls)} books on listing page {page_number}")
    return urls


def scrape_book_detail(url: str) -> dict | None:
    soup = fetch_page(url)

    if soup is None:
        logger.warning(f"Skipping book detail page: {url}")
        return None

    try:
        title = soup.select_one("h1").text.strip()
        rating_tag = soup.select_one("p.star-rating")
        rating_word = rating_tag["class"][1] if rating_tag else "Zero"
        rating = RATING_MAP.get(rating_word, 0)

        price_tag = soup.select_one("p.price_color")
        price = float(price_tag.text.strip().replace("£", "").replace("Â", ""))

        availability_tag = soup.select_one("p.availability")
        availability = availability_tag.text.strip() if availability_tag else "Unknown"
        in_stock = "In stock" in availability
        breadcrumbs = soup.select("ul.breadcrumb li")
        category = breadcrumbs[2].text.strip() if len(breadcrumbs) >= 3 else "Unknown"

        table_data = {}
        rows = soup.select("table.table-striped tr")
        for row in rows:
            header = row.select_one("th")
            value = row.select_one("td")
            if header and value:
                table_data[header.text.strip()] = value.text.strip()

        upc = table_data.get("UPC", "")
        price_excl_tax = float(
            table_data.get("Price (excl. tax)", "£0")
            .replace("£", "").replace("Â", "")
        )
        price_incl_tax = float(
            table_data.get("Price (incl. tax)", "£0")
            .replace("£", "").replace("Â", "")
        )
        num_reviews = int(table_data.get("Number of reviews", "0"))

        description_tag = soup.select_one("article.product_page > p")
        description = description_tag.text.strip() if description_tag else ""

        return {
            "title":            title,
            "category":         category,
            "rating":           rating,
            "rating_word":      rating_word,
            "price":            price,
            "price_excl_tax":   price_excl_tax,
            "price_incl_tax":   price_incl_tax,
            "in_stock":         in_stock,
            "availability":     availability,
            "upc":              upc,
            "num_reviews":      num_reviews,
            "description":      description[:500],  
            "url":              url,
            "scraped_at":       datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to parse book detail at {url}: {e}")
        return None


def scrape(max_pages: int = None) -> list[dict]:
    """Scrape all books - auto-detects total pages if max_pages is None"""
    
    # Auto-detect total pages if not specified
    if max_pages is None:
        max_pages = get_total_pages()
    
    logger.info(f"=== Will scrape {max_pages} pages ===")
    
    logger.info("=== Pass 1: Collecting book URLs from listing pages ===")
    all_urls = []

    for page in range(1, max_pages + 1):
        urls = get_book_urls_from_listing(page)
        all_urls.extend(urls)
        logger.info(f"Page {page}/{max_pages} complete. Total URLs so far: {len(all_urls)}")

        if page < max_pages:
            time.sleep(REQUEST_DELAY)

    logger.info(f"Total book URLs collected: {len(all_urls)}")

    logger.info("=== Pass 2: Scraping individual book detail pages ===")
    all_books = []

    for i, url in enumerate(all_urls, 1):
        book = scrape_book_detail(url)
        
        if book:
            all_books.append(book)

        if i % 10 == 0:
            logger.info(f"Progress: {i}/{len(all_urls)} books scraped ({len(all_books)} successful)")

        time.sleep(REQUEST_DELAY)

    logger.info(f"Scraping complete. Total books collected: {len(all_books)}")
    return all_books


def save_to_json(books: list[dict]) -> str:
    os.makedirs("data/raw", exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"data/raw/books_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(books)} books to {filename}")
    return filename


if __name__ == "__main__":
    logger.info("=== Book Scraper Starting ===")
    books = scrape(max_pages=None)  
    
    if books:
        saved_path = save_to_json(books)
        logger.info(f"=== Done. Saved {len(books)} books to {saved_path} ===")
        
        # Print summary
        categories = {}
        for book in books:
            cat = book.get("category", "Unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        logger.info("=== Category Summary ===")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  {cat}: {count} books")
    else:
        logger.error("=== No books collected. Check logs above. ===")