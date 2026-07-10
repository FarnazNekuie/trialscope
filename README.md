# TrialScope

A clinical trial intelligence platform for AI-driven drug discovery research.
Combines a production-grade data engineering pipeline with NLP, ML outcome prediction,
and knowledge graph–based drug repurposing.

> Built as a PhD research platform in Health Informatics. All components are reproducible
> via Docker. The dataset is publishable to HuggingFace; the ML models are tracked via MLflow.

---

## Quickstart — one command

```bash
git clone https://github.com/yourname/trialscope
cd trialscope
cp .env.example .env        # fill in your API keys
make up                     # builds and starts all services
make seed                   # fetches the first 1,000 trials
make dbt-run                # transforms raw data into the warehouse
```

| Service       | URL                          | Credentials     |
|---------------|------------------------------|-----------------|
| Airflow UI    | http://localhost:8080        | admin / admin   |
| JupyterLab    | http://localhost:8888        | no password     |
| MLflow        | http://localhost:5000        | —               |
| API docs      | http://localhost:8000/docs   | —               |
| App           | http://localhost:3000        | —               |
| Neo4j browser | http://localhost:7474        | neo4j / (env)   |

---

## Architecture

```
Data sources          Ingestion           Warehouse          Intelligence       App
─────────────────     ─────────────       ─────────────      ─────────────      ──────────
ClinicalTrials.gov ──▶ Airflow DAGs  ──▶  PostgreSQL   ──▶  XGBoost model ──▶  FastAPI
FDA FAERS          ──▶ Python        ──▶  dbt models   ──▶  GNN repurpose ──▶  React
PubMed abstracts   ──▶ extractors    ──▶  Feature      ──▶  NLP pipeline  ──▶  Explorer
OpenFDA labels     ──▶ Raw JSON      ──▶  store        ──▶  SHAP explain  ──▶  UI
```

All services run in Docker Compose on a single internal network (`trialscope-net`).

---

## Repository structure

```
trialscope/
├── pipeline/           # Airflow DAGs + API extractors
│   ├── dags/           # Airflow DAG definitions
│   └── extractors/     # ClinicalTrials, FAERS, PubMed clients
├── warehouse/          # dbt project (staging + mart models)
├── research/           # JupyterLab + ML notebooks
│   └── notebooks/      # 01_eda, 02_nlp, 03_prediction, 04_graph
├── api/                # FastAPI backend
├── frontend/           # React + Recharts explorer UI
└── docs/               # Thesis diagrams and paper drafts
```

---

## Research outputs

This platform is designed to produce four publishable contributions:

| # | Contribution | Target venue |
|---|---|---|
| 1 | Harmonized multi-source clinical trial dataset | Scientific Data (Nature) |
| 2 | NLP extraction of eligibility criteria at scale | JAMIA |
| 3 | Explainable ML for trial outcome prediction | npj Digital Medicine |
| 4 | Knowledge graph for drug repurposing via GNN | J. Biomedical Informatics |

The dataset will be published to HuggingFace Hub with a DOI minted via Zenodo.

---

## Common commands

```bash
make up           # start all services
make down         # stop all services
make seed         # fetch first 1,000 trials (quick test)
make seed-full    # trigger full Airflow ingestion DAG
make dbt-run      # run all dbt models
make dbt-test     # run dbt data quality tests
make dbt-docs     # serve dbt documentation at :8090
make test         # run all unit tests
make psql         # connect to PostgreSQL
make fernet       # generate an Airflow Fernet key
make reset-db     # ⚠️  delete all data and restart
```

---

## Environment variables

Copy `.env.example` to `.env` and fill in:

- `DB_USER` / `DB_PASS` — PostgreSQL credentials
- `AIRFLOW_FERNET_KEY` — generate with `make fernet`
- `PUBMED_API_KEY` — free key from https://www.ncbi.nlm.nih.gov/account/
- `NEO4J_PASS` — Neo4j password

The ClinicalTrials.gov API requires no key but please set a descriptive `CLINICALTRIALS_USER_AGENT`.

---

## Citation

If you use TrialScope in your research, please cite:

```bibtex
@software{trialscope2024,
  author  = {Your Name},
  title   = {TrialScope: A Clinical Trial Intelligence Platform},
  year    = {2024},
  url     = {https://github.com/yourname/trialscope},
  doi     = {10.5281/zenodo.XXXXXXX}
}
```

---

## License

MIT — free to use, modify, and build on. Attribution appreciated.
