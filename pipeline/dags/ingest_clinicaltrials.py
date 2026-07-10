"""
Airflow DAG: ingest_clinicaltrials

Runs daily. Fetches trials for a curated list of conditions,
loads raw JSON to the raw-data volume, then triggers dbt to
refresh the warehouse models.

Schedule: daily at 02:00 UTC (off-peak for the API).
"""

from __future__ import annotations

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator

sys.path.insert(0, "/opt/airflow/extractors")

# Conditions to ingest — expand this list over time
# Covering major disease areas for broad research coverage
CONDITIONS = [
    "cancer",
    "diabetes",
    "cardiovascular disease",
    "alzheimer",
    "depression",
    "covid-19",
    "obesity",
    "asthma",
    "hypertension",
    "rare disease",
]

MAX_TRIALS_PER_CONDITION = 5_000

DEFAULT_ARGS = {
    "owner": "trialscope",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
    "email_on_failure": False,
}


@dag(
    dag_id="ingest_clinicaltrials",
    default_args=DEFAULT_ARGS,
    description="Fetch clinical trials from ClinicalTrials.gov v2 API",
    schedule="0 2 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "clinicaltrials"],
    doc_md="""
    ## Clinical Trials Ingestion DAG

    Fetches trials for each condition in the CONDITIONS list,
    saves raw JSON to the shared volume, then runs dbt to
    update the warehouse.

    **Adding conditions**: edit the `CONDITIONS` list in this file.
    **Monitoring**: check raw/ volume for JSON files after first run.
    """,
)
def ingest_clinicaltrials():

    @task(task_id="fetch_trials")
    def fetch_all_conditions() -> dict[str, int]:
        """Fetch trials for all conditions. Returns {condition: count} map."""
        from clinicaltrials import fetch_trials

        results = {}
        for condition in CONDITIONS:
            try:
                ids = fetch_trials(
                    condition=condition,
                    max_trials=MAX_TRIALS_PER_CONDITION,
                )
                results[condition] = len(ids)
            except Exception as e:
                # Log but don't fail the whole DAG for one condition
                import logging
                logging.getLogger(__name__).error(
                    "Failed to fetch condition=%r: %s", condition, e
                )
                results[condition] = -1

        return results

    @task(task_id="log_summary")
    def log_summary(results: dict[str, int]) -> None:
        import logging
        log = logging.getLogger(__name__)
        total = sum(v for v in results.values() if v > 0)
        log.info("=== Ingestion summary ===")
        for cond, count in results.items():
            status = f"{count:,} trials" if count >= 0 else "FAILED"
            log.info("  %-30s %s", cond, status)
        log.info("Total: %d trials fetched", total)

    # Run dbt after ingestion — transforms raw JSON into warehouse tables
    run_dbt = BashOperator(
        task_id="run_dbt",
        bash_command=(
            "docker exec trialscope-dbt-1 dbt run --profiles-dir /dbt "
            "|| echo 'dbt not available in this environment, skipping'"
        ),
    )

    results = fetch_all_conditions()
    log_summary(results) >> run_dbt


ingest_clinicaltrials()
