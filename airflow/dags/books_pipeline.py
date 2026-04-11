from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "leakono",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

PROJECT_DIR = "/home/leakono/Engineer/book-pipeline"
DBT_DIR = f"{PROJECT_DIR}/dbt_project"
VENV_PYTHON = f"{PROJECT_DIR}/venv/bin/python3"
DBT_BIN = f"{PROJECT_DIR}/venv/bin/dbt"
DBT_PROFILES_DIR = "/home/leakono/.dbt"

with DAG(
    dag_id="books_pipeline",
    description="Scrape books, load to Snowflake, transform with dbt",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="0 6 * * *",
    catchup=False,
    tags=["books", "pipeline"],
) as dag:

    scrape_books = BashOperator(
        task_id="scrape_books",
        bash_command=f"cd {PROJECT_DIR} && {VENV_PYTHON} scrapers/books_scraper.py",
    )

    load_to_snowflake = BashOperator(
        task_id="load_to_snowflake",
        bash_command=f"cd {PROJECT_DIR} && {VENV_PYTHON} loaders/snowflake_loader.py",
    )

    run_dbt = BashOperator(
        task_id="run_dbt",
        bash_command=(
            f"cd {DBT_DIR} && {DBT_BIN} run "
            f"--profiles-dir {DBT_PROFILES_DIR} "
            f"--log-level info; "
            f"exit 0"
        ),
    )

    scrape_books >> load_to_snowflake >> run_dbt