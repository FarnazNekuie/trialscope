FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir dbt-postgres==1.7.13

WORKDIR /dbt
COPY . .

ENTRYPOINT ["dbt"]
CMD ["--help"]
