cat > README.md << 'EOF'
# Book Pipeline

An end-to-end data pipeline that scrapes book data from books.toscrape.com and loads it into Snowflake for analysis.

## Pipeline Architecture
```
books.toscrape.com → Python Scraper → JSON → Snowflake → dbt → Airflow → Power BI
```

## Project Structure
```
book-pipeline/
├── scrapers/
│   └── books_scraper.py    # Scrapes books.toscrape.com
├── loaders/
│   └── snowflake_loader.py # Loads JSON data into Snowflake
├── dbt_project/            # dbt transformation models (coming soon)
├── dags/                   # Airflow DAGs (coming soon)
├── data/raw/               # Raw JSON files (git ignored)
├── logs/                   # Log files (git ignored)
├── .env.example            # Environment variable template
└── requirements.txt        # Python dependencies
```

## Setup

1. Clone the repository
2. Create a virtual environment and activate it
```bash
   python3 -m venv venv
   source venv/bin/activate
```
3. Install dependencies
```bash
   pip install -r requirements.txt
```
4. Copy .env.example to .env and fill in your credentials
```bash
   cp .env.example .env
```

## Usage

Run the scraper:
```bash
python3 scrapers/books_scraper.py
```

Load data into Snowflake:
```bash
python3 loaders/snowflake_loader.py
```

## Data

- Source: books.toscrape.com (1000 books across 50 pages)
- Fields: title, category, rating, price, availability, UPC, description
- Storage: Snowflake (BOOKS_DB.RAW.RAW_BOOKS)
