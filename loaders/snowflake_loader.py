import snowflake.connector
import json
import logging
import os
import glob
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Logging setup 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/loader.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Connection 

def get_connection():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"]
    )

def load_books(books: list[dict], conn) -> int:
    """
    Insert a list of book dicts into the RAW_BOOKS table.

    Returns the number of rows successfully inserted.

    We use parameterized queries (%s placeholders) instead of string
    formatting. This is critical for two reasons:
    1. Security — prevents SQL injection attacks
    2. Type safety — the connector handles proper escaping of
       strings, booleans, floats etc automatically
    """
    insert_sql = """
        INSERT INTO RAW_BOOKS (
            TITLE, CATEGORY, RATING, RATING_WORD,
            PRICE, PRICE_EXCL_TAX, PRICE_INCL_TAX,
            IN_STOCK, AVAILABILITY, UPC, NUM_REVIEWS,
            DESCRIPTION, URL, SCRAPED_AT
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s
        )
    """

    rows = []
    for book in books:
        rows.append((
            book.get("title"),
            book.get("category"),
            book.get("rating"),
            book.get("rating_word"),
            book.get("price"),
            book.get("price_excl_tax"),
            book.get("price_incl_tax"),
            book.get("in_stock"),
            book.get("availability"),
            book.get("upc"),
            book.get("num_reviews"),
            book.get("description"),
            book.get("url"),
            book.get("scraped_at"),
        ))

    cursor = conn.cursor()

    try:
        #Insert ALL rows into database
        # instead of making one database call per row
        cursor.executemany(insert_sql, rows)
        inserted = len(rows)
        logger.info(f"Successfully inserted {inserted} rows into RAW_BOOKS")
        return inserted

    except Exception as e:
        logger.error(f"Failed to insert rows: {e}")
        raise

    finally:
        cursor.close()


def get_latest_json_file() -> str | None:
    
    #Find the most recently created JSON file in data/raw/.

 
    files = glob.glob("data/raw/books_*.json")

    if not files:
        logger.error("No JSON files found in data/raw/")
        return None

    latest = max(files, key=os.path.getctime)
    logger.info(f"Found latest file: {latest}")
    return latest


def verify_load(conn) -> None:
    """
    After loading, run a quick check to confirm data landed correctly.
    This is called a sanity check — always verify after loading.
    """
    cursor = conn.cursor()

    try:
        # Total row count
        cursor.execute("SELECT COUNT(*) FROM RAW_BOOKS")
        total = cursor.fetchone()[0]
        logger.info(f"Total rows in RAW_BOOKS: {total}")

        # Count by category
        cursor.execute("""
            SELECT CATEGORY, COUNT(*) as book_count
            FROM RAW_BOOKS
            GROUP BY CATEGORY
            ORDER BY book_count DESC
            LIMIT 5
        """)
        logger.info("Top 5 categories:")
        for row in cursor.fetchall():
            logger.info(f"  {row[0]}: {row[1]} books")

        # Average price
        cursor.execute("SELECT ROUND(AVG(PRICE), 2) FROM RAW_BOOKS")
        avg_price = cursor.fetchone()[0]
        logger.info(f"Average book price: £{avg_price}")

    finally:
        cursor.close()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("=== Snowflake Loader Starting ===")

    # Step 1 — find the latest scraped data file
    json_file = get_latest_json_file()
    if not json_file:
        logger.error("Nothing to load. Run the scraper first.")
        exit(1)

    # Step 2 — read the JSON file
    with open(json_file, "r", encoding="utf-8") as f:
        books = json.load(f)
    logger.info(f"Loaded {len(books)} books from {json_file}")

    # Step 3 — connect to Snowflake
    logger.info("Connecting to Snowflake...")
    conn = get_connection()
    logger.info("Connected successfully")

    try:
        # Step 4 — load the data
        load_books(books, conn)

        # Step 5 — verify it landed correctly
        verify_load(conn)

    finally:
        # Always close the connection, even if something fails
        conn.close()
        logger.info("Connection closed")

    logger.info("=== Loader Complete ===")