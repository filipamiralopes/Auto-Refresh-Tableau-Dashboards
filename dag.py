from airflow.models import Variable
from .tableau import refresh_tagged_wbs
from .consts import TABLEAU_TOKENS, MY_PIPELINE
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator

default_args = {
    "owner": "filipa",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "refresh_tableau_dashboards",
    default_args=default_args,
    description="This one-task dag triggers the refresh of a Tableau dashboard with tag my_pipeline",
    schedule_interval=timedelta(days=1),
)

start = DummyOperator(
    task_id="start",
    dag=dag,
)

refresh_dash = PythonOperator(
    task_id="refresh_tableau_dashboards",
    python_callable=refresh_tagged_wbs,
    op_kwargs={
        "token_name": MY_PIPELINE,
        "token_secret": TABLEAU_TOKENS[MY_PIPELINE],
        "tag": MY_PIPELINE
    },
    dag=dag,
)


# Set the task dependencies within the DAG
start >> refresh_dash

if __name__ == "__main__":
    dag.cli()
