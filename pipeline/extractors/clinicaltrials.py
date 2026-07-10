"""
ClinicalTrials.gov v2 API extractor.

Fetches trials by condition, paginates through all results,
and saves raw JSON to disk (one file per trial).
Designed to be called directly or from an Airflow DAG.

Usage:
    python clinicaltrials.py --condition "diabetes" --max-trials 5000
"""

import argparse
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

# ── Config ────────────────────────────────────────────────────────
API_BASE = os.getenv("CLINICALTRIALS_API_URL", "https://clinicaltrials.gov/api/v2")
USER_AGENT = os.getenv(
    "CLINICALTRIALS_USER_AGENT", "TrialScope-Research/1.0 (research@trialscope.io)"
)
RAW_DATA_DIR = Path(os.getenv("RAW_DATA_PATH", "/opt/airflow/raw/clinicaltrials"))
PAGE_SIZE = 1000          # max allowed by the API
RATE_LIMIT_DELAY = 0.5   # seconds between requests (be a good citizen)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


# ── HTTP client ───────────────────────────────────────────────────
def _make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })
    return session


@retry(
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
def _get(session: requests.Session, url: str, params: dict) -> dict:
    resp = session.get(url, params=params, timeout=30)
    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 60))
        log.warning("Rate limited. Sleeping %ds...", retry_after)
        time.sleep(retry_after)
        resp = session.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ── Fetching ──────────────────────────────────────────────────────
def fetch_trials(
    condition: str,
    max_trials: int = 10_000,
    output_dir: Path = RAW_DATA_DIR,
) -> list[str]:
    """
    Fetch all trials for a given condition and save raw JSON files.

    Returns a list of nctIds that were saved.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    session = _make_session()

    saved_ids: list[str] = []
    next_page_token: str | None = None
    fetched = 0
    page = 0

    log.info("Starting fetch: condition=%r, max=%d", condition, max_trials)

    while fetched < max_trials:
        batch_size = min(PAGE_SIZE, max_trials - fetched)

        params: dict = {
            "query.cond": condition,
            "pageSize": batch_size,
            "format": "json",
            "fields": ",".join([
                # Identity
                "NCTId", "BriefTitle", "OfficialTitle", "Acronym",
                # Status
                "OverallStatus", "StartDate", "PrimaryCompletionDate",
                "CompletionDate", "StudyFirstSubmitDate", "LastUpdatePostDate",
                # Design
                "StudyType", "Phase", "DesignAllocation", "DesignInterventionModel",
                "DesignPrimaryPurpose", "DesignMasking",
                # Enrollment
                "EnrollmentCount", "EnrollmentType",
                # Conditions / interventions
                "Condition", "ConditionMeshTerm", "Keyword",
                "InterventionType", "InterventionName", "InterventionDescription",
                "ArmGroupLabel", "ArmGroupType",
                # Sponsors / collaborators
                "LeadSponsorName", "LeadSponsorClass",
                "CollaboratorName", "CollaboratorClass",
                # Eligibility (free text — NLP target)
                "EligibilityCriteria", "HealthyVolunteers",
                "Gender", "MinimumAge", "MaximumAge", "StdAge",
                # Locations
                "LocationFacility", "LocationCity", "LocationState",
                "LocationCountry", "LocationStatus",
                # Outcomes
                "PrimaryOutcomeMeasure", "PrimaryOutcomeTimeFrame",
                "SecondaryOutcomeMeasure",
                # Results
                "ResultsFirstPostDate", "WhyStopped",
            ]),
        }

        if next_page_token:
            params["pageToken"] = next_page_token

        data = _get(session, f"{API_BASE}/studies", params)

        studies = data.get("studies", [])
        if not studies:
            log.info("No more studies returned. Done.")
            break

        for study in studies:
            nct_id = (
                study.get("protocolSection", {})
                     .get("identificationModule", {})
                     .get("nctId")
            )
            if not nct_id:
                continue

            # One JSON file per trial — idempotent: skip if already fetched
            out_path = output_dir / f"{nct_id}.json"
            if not out_path.exists():
                out_path.write_text(json.dumps({
                    "nct_id": nct_id,
                    "fetched_at": datetime.utcnow().isoformat(),
                    "condition_query": condition,
                    "raw": study,
                }, indent=2))
            saved_ids.append(nct_id)

        fetched += len(studies)
        page += 1
        next_page_token = data.get("nextPageToken")

        log.info(
            "Page %d — fetched %d/%d | next_token=%s",
            page, fetched, max_trials,
            next_page_token[:12] + "..." if next_page_token else "none",
        )

        if not next_page_token:
            break

        time.sleep(RATE_LIMIT_DELAY)

    log.info("Done. Saved %d trial files to %s", len(saved_ids), output_dir)
    return saved_ids


def fetch_trial_by_id(nct_id: str, output_dir: Path = RAW_DATA_DIR) -> dict:
    """Fetch a single trial by NCT ID. Useful for updating stale records."""
    output_dir.mkdir(parents=True, exist_ok=True)
    session = _make_session()
    data = _get(session, f"{API_BASE}/studies/{nct_id}", {"format": "json"})
    out_path = output_dir / f"{nct_id}.json"
    out_path.write_text(json.dumps({
        "nct_id": nct_id,
        "fetched_at": datetime.utcnow().isoformat(),
        "condition_query": "direct_fetch",
        "raw": data,
    }, indent=2))
    log.info("Saved %s", out_path)
    return data


def load_raw_trial(nct_id: str, data_dir: Path = RAW_DATA_DIR) -> dict | None:
    """Load a previously saved raw trial JSON."""
    path = data_dir / f"{nct_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def list_fetched_ids(data_dir: Path = RAW_DATA_DIR) -> list[str]:
    """Return all nct_ids that have been saved locally."""
    return [p.stem for p in data_dir.glob("NCT*.json")]


# ── CLI ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch ClinicalTrials.gov data")
    parser.add_argument("--condition", required=True, help="Condition to search for")
    parser.add_argument("--max-trials", type=int, default=5000)
    parser.add_argument("--output-dir", type=Path, default=RAW_DATA_DIR)
    args = parser.parse_args()

    ids = fetch_trials(
        condition=args.condition,
        max_trials=args.max_trials,
        output_dir=args.output_dir,
    )
    print(f"Fetched {len(ids)} trials.")
