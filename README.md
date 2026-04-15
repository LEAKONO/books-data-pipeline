#  Book Pipeline — End-to-End Data Engineering Project

An automated, production-grade data pipeline that scrapes, loads, transforms, and visualizes book data from [books.toscrape.com](http://books.toscrape.com).

---

## Project Overview

This project demonstrates a complete data engineering workflow following industry best practices:

- **Extract** — Web scraping 1,000 books across 50 pages using Python & BeautifulSoup
- **Load** — Idempotent data ingestion into Snowflake with UPC-based deduplication
- **Transform** — Multi-layer data modeling with dbt (RAW → STAGING)
- **Orchestrate** — Fully automated daily pipeline with Apache Airflow
- **Visualize** — Interactive dashboards with Metabase

---

## Pipeline Statistics

| Metric | Value |
|--------|-------|
| Books Scraped | 1,000 |
| Pages Processed | 50 |
| Categories | 28 |
| Duplicates Skipped | 100 |
| New Rows Loaded | 900 |
| Average Price | £35.07 |
| Pipeline Runtime | ~6 minutes end-to-end |

---

##  Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    END-TO-END DATA PIPELINE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Source                                                      │
│     books.toscrape.com                                          │
│          │                                                      │
│          ▼                                                      │
│   Scraper (Python + BeautifulSoup)                           │
│     └── 50 pages → 1,000 books → JSON files                    │
│          │                                                      │
│          ▼                                                      │
│   Loader (Snowflake Connector)                               │
│     └── UPC deduplication → 900 new rows loaded                │
│          │                                                      │
│          ▼                                                      │
│   Snowflake Data Warehouse                                    │
│     ├── BOOKS_DB.RAW.RAW_BOOKS        (landing zone)           │
│     ├── BOOKS_DB.STAGING.STG_BOOKS    (cleaned view)           │
│     ├── BOOKS_DB.STAGING.DIM_CATEGORIES (dimension table)      │
│     └── BOOKS_DB.STAGING.FACT_BOOKS   (fact table)             │
│          │                                                      │
│          ▼                                                      │
│   dbt Transformations                                         │
│     ├── Data cleaning & normalization                           │
│     ├── Category mapping & aggregations                         │
│     └── Mart layer ready for analytics                          │
│          │                                                      │
│          ▼                                                      │
│   Apache Airflow Orchestration                                │
│     └── DAG: scrape_books → load_to_snowflake → run_dbt        │
│          │                                                      │
│          ▼                                                      │
│   Metabase Visualization                                      │
│     ├── Books per Category                                      │
│     ├── Average Price by Category                               │
│     └── Rating Distribution                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

##  Project Structure

```
book-pipeline/
│
├── scrapers/
│   └── books_scraper.py          # Scrapes books.toscrape.com (50 pages, 1000 books)
│
├── loaders/
│   └── snowflake_loader.py       # Loads JSON to Snowflake with UPC deduplication
│
├── dbt_project/                  # dbt transformation project
│   ├── models/
│   │   ├── staging/
│   │   │   └── stg_books.sql     # Cleaned staging view
│   │   └── marts/
│   │       ├── dim_categories.sql # Category dimension with aggregated metrics
│   │       └── fact_books.sql     # Book fact table
│   ├── macros/
│   │   └── generate_schema_name.sql  # Custom schema naming macro
│   └── dbt_project.yml           # dbt project configuration
│
├── airflow/
│   └── dags/
│       └── books_pipeline.py     # Airflow DAG (scrape → load → transform)
│
├── data/
│   └── raw/                      # JSON files output from scraper
│
├── logs/                         # Scraper and loader logs
│
├── .env.example                  # Environment variables template
├── .gitignore
├── requirements.txt
└── README.md
```

---

##  Quick Start

### Prerequisites

- Python 3.10+
- Snowflake account
- Java 11+ (for Metabase)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/LEAKONO/books-data-pipeline.git
cd book-pipeline
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your Snowflake credentials:

```env
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=BOOKS_USER
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=BOOKS_DB
SNOWFLAKE_SCHEMA=RAW
SNOWFLAKE_WAREHOUSE=BOOKS_WH
```

### 4. Configure dbt Profile

```bash
nano ~/.dbt/profiles.yml
```

```yaml
dbt_project:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: your_account
      user: BOOKS_USER
      password: your_password
      role: BOOKS_ROLE
      database: BOOKS_DB
      warehouse: BOOKS_WH
      schema: STAGING
      threads: 4
```

---

##  Usage

### Run Each Step Manually

**Step 1 — Scrape book data:**
```bash
python scrapers/books_scraper.py
```
Output: `data/raw/books_YYYYMMDD_HHMMSS.json`

**Step 2 — Load to Snowflake:**
```bash
python loaders/snowflake_loader.py
```

**Step 3 — Run dbt transformations:**
```bash
cd dbt_project
dbt run --profiles-dir ~/.dbt
```

**Step 4 — Launch Metabase:**
```bash
java --add-opens=java.base/java.nio=ALL-UNNAMED -jar metabase.jar
```
Access at `http://localhost:3000`

---

### Run with Airflow (Automated)

```bash
# Terminal 1 — Scheduler
source airflow-venv/bin/activate
export AIRFLOW_HOME=~/Engineer/book-pipeline/airflow
airflow scheduler

# Terminal 2 — Webserver
source airflow-venv/bin/activate
export AIRFLOW_HOME=~/Engineer/book-pipeline/airflow
airflow webserver --port 8080
```

Access Airflow UI at `http://localhost:8080` and trigger `books_pipeline` DAG.

---

##  Data Model

### Schema Architecture

```
BOOKS_DB
  ├── RAW
  │     └── RAW_BOOKS          ← Python loader writes here
  └── STAGING
        ├── STG_BOOKS           ← dbt cleaned view
        ├── DIM_CATEGORIES      ← dimension table
        └── FACT_BOOKS          ← fact table for analysis
```

### RAW.RAW_BOOKS — Landing Table

| Column | Type | Description |
|--------|------|-------------|
| ID | NUMBER | Auto-generated primary key |
| TITLE | VARCHAR | Book title |
| CATEGORY | VARCHAR | Genre category |
| RATING | INT | Rating (1–5 stars) |
| PRICE | DECIMAL | Current price (£) |
| IN_STOCK | BOOLEAN | Availability status |
| UPC | VARCHAR | Unique product code |
| NUM_REVIEWS | INT | Number of customer reviews |
| SCRAPED_AT | TIMESTAMP | When data was scraped |
| LOADED_AT | TIMESTAMP | When data was loaded |

### STAGING.DIM_CATEGORIES — Dimension Table

| Column | Type | Description |
|--------|------|-------------|
| CATEGORY | VARCHAR | Genre category |
| TOTAL_BOOKS | INT | Books in this category |
| AVG_PRICE | DECIMAL | Average price |
| AVG_RATING | DECIMAL | Average rating |

### STAGING.FACT_BOOKS — Fact Table

| Column | Type | Description |
|--------|------|-------------|
| BOOK_ID | VARCHAR | Surrogate key |
| TITLE | VARCHAR | Book title |
| CATEGORY | VARCHAR | Genre category |
| PRICE | DECIMAL | Current price |
| RATING | INT | Star rating |
| IN_STOCK | BOOLEAN | Availability |

---

##  Results

### Top Categories (1,000 Books)

| Rank | Category | Count |
|------|----------|-------|
| 1 | Nonfiction | 110 |
| 2 | Sequential Art | 75 |
| 3 | Fiction | 65 |
| 4 | Young Adult | 54 |
| 5 | Fantasy | 48 |

### Data Quality Improvements

| Issue | Before | After |
|-------|--------|-------|
| Uncategorized books | 219 books with no category | Mapped to "General Collection" |
| Duplicate UPCs | 100 duplicates across runs | Skipped during load |

---

##  Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Scraping | Python, BeautifulSoup, Requests | Extract book data from web |
| Loading | Python, Snowflake Connector | Ingest data into warehouse |
| Warehouse | Snowflake | Cloud data storage |
| Transformation | dbt | Data modeling & cleaning |
| Orchestration | Apache Airflow | Daily pipeline scheduling |
| Visualization | Metabase | Dashboards & charts |
| Version Control | Git & GitHub | Code management |

---

##  Airflow DAG

```
scrape_books → load_to_snowflake → run_dbt
```

| Task | Tool | Duration |
|------|------|----------|
| scrape_books | Python + BeautifulSoup | ~3 minutes |
| load_to_snowflake | Python + Snowflake Connector | ~30 seconds |
| run_dbt | dbt + Snowflake | ~2 minutes |
| **Total** | | **~6 minutes** |

Schedule: `0 6 * * *` (daily at 6am UTC)

---

##  Future Enhancements

- [ ] Incremental loading in dbt
- [ ] Data quality tests with `dbt-expectations`
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Containerization with Docker
- [ ] Infrastructure as Code with Terraform
- [ ] Great Expectations for data validation

---

##  License

This project is for educational and portfolio purposes.

---

##  Connect

**Emmanuel Leakono** — [GitHub](https://github.com/Leakono) • [LinkedIn](https://linkedin.com/in/emmanuel-leakono)