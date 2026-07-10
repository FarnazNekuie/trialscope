"""
TrialScope API — FastAPI backend.

Serves clinical trial data from the PostgreSQL warehouse.
Auto-docs at /docs (Swagger) and /redoc.
"""

from contextlib import asynccontextmanager
from typing import Optional

import asyncpg
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trialscope:changeme@postgres:5432/trialscope")


# ── Database pool ─────────────────────────────────────────────────
pool: asyncpg.Pool | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    yield
    await pool.close()

async def get_db() -> asyncpg.Pool:
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")
    return pool


# ── App ───────────────────────────────────────────────────────────
app = FastAPI(
    title="TrialScope API",
    description="Clinical trial intelligence for AI drug discovery research.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────
class TrialSummary(BaseModel):
    nct_id: str
    brief_title: str
    overall_status: str
    outcome_label: str | None
    phase_numeric: int | None
    phase_raw: str | None
    enrollment_count: int | None
    lead_sponsor_name: str | None
    lead_sponsor_class: str | None
    start_date: str | None
    completion_date: str | None
    num_conditions: int
    num_locations: int
    completion_prob: float | None
    termination_prob: float | None

class TrialDetail(TrialSummary):
    official_title: str | None
    eligibility_criteria_text: str | None
    healthy_volunteers: str | None
    sex: str | None
    minimum_age: str | None
    maximum_age: str | None
    study_duration_days: int | None
    why_stopped: str | None
    has_results: bool | None
    shap_features: dict | None

class PaginatedTrials(BaseModel):
    total: int
    page: int
    page_size: int
    results: list[TrialSummary]

class PhaseStats(BaseModel):
    phase_numeric: int | None
    count: int
    completion_rate: float | None

class StatusStats(BaseModel):
    overall_status: str
    count: int

class SponsorStats(BaseModel):
    lead_sponsor_class: str | None
    count: int
    avg_enrollment: float | None


# ── Routes ────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/trials", response_model=PaginatedTrials, tags=["trials"])
async def search_trials(
    condition: Optional[str] = Query(None, description="Filter by condition keyword"),
    status: Optional[str] = Query(None, description="e.g. RECRUITING, COMPLETED"),
    phase: Optional[int] = Query(None, ge=1, le=4),
    sponsor_class: Optional[str] = Query(None, description="INDUSTRY, NIH, OTHER"),
    has_prediction: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("enrollment_count", enum=["enrollment_count", "start_date", "completion_prob"]),
    db: asyncpg.Pool = Depends(get_db),
):
    """Search and filter trials from the warehouse."""
    filters = ["1=1"]
    args = []
    i = 1

    if condition:
        filters.append(f"(brief_title ILIKE ${i} OR eligibility_criteria_text ILIKE ${i})")
        args.append(f"%{condition}%")
        i += 1
    if status:
        filters.append(f"overall_status = ${i}")
        args.append(status.upper())
        i += 1
    if phase is not None:
        filters.append(f"phase_numeric = ${i}")
        args.append(phase)
        i += 1
    if sponsor_class:
        filters.append(f"lead_sponsor_class = ${i}")
        args.append(sponsor_class.upper())
        i += 1
    if has_prediction is not None:
        filters.append("completion_prob IS NOT NULL" if has_prediction else "completion_prob IS NULL")

    where = " AND ".join(filters)
    order = {
        "enrollment_count": "enrollment_count DESC NULLS LAST",
        "start_date": "start_date DESC NULLS LAST",
        "completion_prob": "completion_prob DESC NULLS LAST",
    }[sort_by]

    offset = (page - 1) * page_size

    async with db.acquire() as conn:
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM staging_marts.fact_trials WHERE {where}", *args
        )
        rows = await conn.fetch(
            f"""
            SELECT nct_id, brief_title, overall_status, outcome_label,
                   phase_numeric, phase_raw, enrollment_count,
                   lead_sponsor_name, lead_sponsor_class,
                   start_date::TEXT, completion_date::TEXT,
                   num_conditions, num_locations,
                   completion_prob, termination_prob
            FROM staging_marts.fact_trials
            WHERE {where}
            ORDER BY {order}
            LIMIT ${i} OFFSET ${i+1}
            """,
            *args, page_size, offset,
        )

    return PaginatedTrials(
        total=total,
        page=page,
        page_size=page_size,
        results=[TrialSummary(**dict(r)) for r in rows],
    )


@app.get("/trials/{nct_id}", response_model=TrialDetail, tags=["trials"])
async def get_trial(nct_id: str, db: asyncpg.Pool = Depends(get_db)):
    """Get full detail for a single trial."""
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM staging_marts.fact_trials WHERE nct_id = $1", nct_id.upper()
        )
    if not row:
        raise HTTPException(status_code=404, detail=f"Trial {nct_id} not found")
    return TrialDetail(**dict(row))


@app.get("/stats/by-phase", response_model=list[PhaseStats], tags=["analytics"])
async def stats_by_phase(db: asyncpg.Pool = Depends(get_db)):
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                phase_numeric,
                COUNT(*) AS count,
                ROUND(
                    100.0 * SUM(CASE WHEN outcome_label = 'completed' THEN 1 ELSE 0 END)
                    / NULLIF(COUNT(*), 0), 1
                ) AS completion_rate
            FROM staging_marts.fact_trials
            WHERE phase_numeric IS NOT NULL
            GROUP BY phase_numeric
            ORDER BY phase_numeric
        """)
    return [PhaseStats(**dict(r)) for r in rows]


@app.get("/stats/by-status", response_model=list[StatusStats], tags=["analytics"])
async def stats_by_status(db: asyncpg.Pool = Depends(get_db)):
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT overall_status, COUNT(*) AS count
            FROM staging_marts.fact_trials
            GROUP BY overall_status
            ORDER BY count DESC
            LIMIT 20
        """)
    return [StatusStats(**dict(r)) for r in rows]


@app.get("/stats/by-sponsor", response_model=list[SponsorStats], tags=["analytics"])
async def stats_by_sponsor(db: asyncpg.Pool = Depends(get_db)):
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                lead_sponsor_class,
                COUNT(*) AS count,
                ROUND(AVG(enrollment_count), 0) AS avg_enrollment
            FROM staging_marts.fact_trials
            GROUP BY lead_sponsor_class
            ORDER BY count DESC
        """)
    return [SponsorStats(**dict(r)) for r in rows]


@app.get("/stats/trends", tags=["analytics"])
async def stats_trends(db: asyncpg.Pool = Depends(get_db)):
    """Trials registered per year — for the time-series chart."""
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                EXTRACT(YEAR FROM first_submit_date)::INT AS year,
                COUNT(*) AS count,
                SUM(CASE WHEN outcome_label = 'completed' THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN outcome_label = 'terminated' THEN 1 ELSE 0 END) AS terminated
            FROM staging_marts.fact_trials
            WHERE first_submit_date IS NOT NULL
              AND EXTRACT(YEAR FROM first_submit_date) >= 2000
            GROUP BY year
            ORDER BY year
        """)
    return [dict(r) for r in rows]
