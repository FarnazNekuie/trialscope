import json, psycopg2
from pathlib import Path

conn = psycopg2.connect(
    host="postgres",
    dbname="trialscope",
    user="trialscope",
    password="TrialScope2024!"
)
cur = conn.cursor()

raw_dir = Path("/opt/airflow/raw/clinicaltrials")
count = 0
for f in raw_dir.glob("NCT*.json"):
    data = json.loads(f.read_text())
    cur.execute(
        "SELECT raw.upsert_trial(%s, %s, %s)",
        (data["nct_id"], data["condition_query"], json.dumps(data["raw"]))
    )
    count += 1

conn.commit()
conn.close()
print(f"Loaded {count} trials into PostgreSQL")
