.PHONY: up down restart logs seed dbt-run dbt-test dbt-docs test ci fernet

# ── Core ──────────────────────────────────────────────────────────
up:
	@echo "Starting TrialScope..."
	@cp -n .env.example .env 2>/dev/null || true
	docker compose up -d --build
	@echo ""
	@echo "  Airflow UI  → http://localhost:8080  (admin / admin)"
	@echo "  JupyterLab  → http://localhost:8888"
	@echo "  MLflow      → http://localhost:5000"
	@echo "  API docs    → http://localhost:8000/docs"
	@echo "  App         → http://localhost:3000"
	@echo "  Neo4j       → http://localhost:7474"

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f --tail=50

# ── Data ──────────────────────────────────────────────────────────
seed:
	@echo "Fetching first 1,000 trials (condition=cancer)..."
	docker compose exec airflow-webserver python /opt/airflow/extractors/clinicaltrials.py \
		--condition cancer --max-trials 1000

seed-full:
	@echo "Triggering full ingestion DAG..."
	docker compose exec airflow-webserver airflow dags trigger ingest_clinicaltrials

# ── dbt ──────────────────────────────────────────────────────────
dbt-run:
	docker compose --profile dbt run --rm dbt run

dbt-test:
	docker compose --profile dbt run --rm dbt test

dbt-docs:
	docker compose --profile dbt run --rm dbt docs generate
	docker compose --profile dbt run --rm dbt docs serve --port 8090
	@echo "dbt docs → http://localhost:8090"

# ── Testing ───────────────────────────────────────────────────────
test:
	docker compose exec api pytest tests/ -v
	$(MAKE) dbt-test

ci: test dbt-test
	@echo "All checks passed."

# ── Helpers ───────────────────────────────────────────────────────
fernet:
	@docker run --rm python:3.11-slim python -c \
		"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

psql:
	docker compose exec postgres psql -U $${DB_USER} -d trialscope

reset-db:
	@echo "WARNING: This will delete all data. Ctrl-C to cancel."
	@sleep 3
	docker compose down -v
	docker compose up -d postgres
