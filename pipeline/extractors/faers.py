"""
FDA FAERS (adverse event reports) extractor.

Fetches drug adverse events from the OpenFDA API,
joined later in the warehouse to clinical trial drugs.

Usage:
    python faers.py --drug semaglutide --max-records 5000
"""

import argparse
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

API_BASE = os.getenv("FAERS_API_URL", "https://api.fda.gov/drug/event.json")
RAW_DATA_DIR = Path(os.getenv("RAW_DATA_PATH", "/opt/airflow/raw/faers"))
PAGE_SIZE = 100  # FAERS max is 100 per request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


@retry(
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    stop=stop_after_attempt(5),
    wait=wait_exponential(min=2, max=30),
    reraise=True,
)
def _get(url: str, params: dict) -> dict:
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code == 429:
        time.sleep(60)
        resp = requests.get(url, params=params, timeout=30)
    if resp.status_code == 404:
        return {"results": [], "meta": {"results": {"total": 0}}}
    resp.raise_for_status()
    return resp.json()


def fetch_adverse_events(
    drug_name: str,
    max_records: int = 5000,
    output_dir: Path = RAW_DATA_DIR,
) -> int:
    """
    Fetch adverse event reports for a given drug name.
    Saves one JSON batch file per page.
    Returns total records saved.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    skip = 0

    log.info("Fetching FAERS events for drug=%r", drug_name)

    while saved < max_records:
        limit = min(PAGE_SIZE, max_records - saved)
        data = _get(API_BASE, {
            "search": f'patient.drug.medicinalproduct:"{drug_name}"',
            "limit": limit,
            "skip": skip,
        })

        results = data.get("results", [])
        if not results:
            break

        # Save batch
        batch_file = output_dir / f"{drug_name.lower().replace(' ', '_')}_{skip:06d}.json"
        batch_file.write_text(json.dumps({
            "drug_query": drug_name,
            "fetched_at": datetime.utcnow().isoformat(),
            "skip": skip,
            "count": len(results),
            "results": results,
        }, indent=2))

        saved += len(results)
        skip += len(results)
        log.info("Saved %d records (total %d)", len(results), saved)

        total = data.get("meta", {}).get("results", {}).get("total", 0)
        if skip >= total:
            break

        time.sleep(0.5)

    log.info("Done. Saved %d FAERS records for %r", saved, drug_name)
    return saved


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--drug", required=True)
    parser.add_argument("--max-records", type=int, default=5000)
    args = parser.parse_args()
    fetch_adverse_events(args.drug, args.max_records)
