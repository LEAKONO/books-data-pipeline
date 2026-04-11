from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id='test_simple',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
) as dag:
    test = BashOperator(
        task_id='test_task',
        bash_command='echo "Airflow is working!" && date'
    )
