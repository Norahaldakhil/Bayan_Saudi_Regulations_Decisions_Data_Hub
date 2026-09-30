# BAYAN — Saudi Regulations & Decisions Data Hub

BAYAN (بيان) is a data engineering capstone project that collects, structures, versions, and prepares Saudi regulatory information for analysis.

The current implementation starts with regulations published by the **Saudi Bureau of Experts at the Council of Ministers (BOE)** and processes them through a layered pipeline:

**BOE → Bronze → Silver → Gold → Power BI**

## Project Team

- Norah Aldakhil
- Yaqeen Alhalal
- Shouq Alotaibi

**Program:** Saudi Digital Academy — Data Engineering Capstone Project  
**Partner:** WeCloudData

## Project Objective

BAYAN focuses on turning regulatory publications into structured, traceable, and analytics-ready data.

The platform is designed to support questions such as:

- What is the current regulation?
- What previous versions exist?
- Has a regulation or article changed?
- Which version is currently effective?
- How can regulatory information be analyzed as structured data?

## Current Scope

The current implementation includes:

- Regulatory extraction from the Saudi Bureau of Experts
- Raw source preservation in SeaweedFS
- Bronze, Silver, and Gold data layers
- Structured PostgreSQL storage
- Regulation and article version tracking
- Change detection using content hashes
- Automated orchestration with Apache Airflow
- Power BI dashboards for analysis and monitoring

## Architecture

### 1. Bronze — Raw Data

**Technology:** SeaweedFS

The Bronze layer preserves the collected source artifacts before transformation.

Examples include:

- `raw.txt`
- `translated.pdf` when an official translated document is available

The raw layer supports traceability, reproducibility, and reprocessing.

### 2. Silver — Clean and Structured Data

**Technology:** PostgreSQL

The Silver layer converts raw regulatory content into normalized relational data.

Main entities include:

- `silver.sources`
- `silver.status`
- `silver.laws`
- `silver.laws_versions`
- `silver.chapters`
- `silver.articles`
- `silver.articles_versions`
- `silver.law_version_extraction_status`
- `silver.processed_bronze_objects`

The transformation logic includes Arabic heading normalization, date handling, structured relationships, duplicate prevention, and version tracking.

### 3. Gold — Analytics-Ready Data

**Technology:** PostgreSQL

The Gold layer prepares curated data for reporting and downstream consumption.

Implemented Gold tables include:

- `gold.dim_regulations`
- `gold.dim_articles`
- `gold.dim_date`
- `gold.dim_change_type`
- `gold.fact_article_changes`

The Gold layer is refreshed using SQL and is consumed by Power BI.

## Version Tracking and Change Detection

BAYAN preserves historical versions instead of overwriting previous data.

The pipeline:

1. Collects a regulation again.
2. Normalizes relevant text.
3. Calculates a content fingerprint/hash.
4. Compares the new content with the existing version.
5. Keeps the current version if no change is detected.
6. Creates and preserves a new version when a change is detected.

This makes regulatory history traceable over time.

## Orchestration

**Technology:** Apache Airflow

The main DAG is:

`boe_pipeline`

It runs the pipeline in this order:

**Bronze → Silver → Gold**

The configured schedule is:

**Daily at 1:00 AM, Asia/Riyadh**

Airflow manages task order and pipeline execution.

## Main Technologies

- Python
- PostgreSQL
- SeaweedFS
- Apache Airflow
- Docker / Docker Compose
- SQL
- DBeaver
- Power BI

## Project Structure

```text
Bayan_Saudi_Regulations_Decisions_Data_Hub_Group01/
│
├── 01_proposal/
│   ├── Bayan_Project_Proposal.pdf
│   └── Bayan_Project_Proposal.pptx
│
└── 02_code/
    ├── 01_data/
    │   ├── bronze/
    │   └── bayan_dummy_bronze/
    │
    ├── 02_src/
    │   ├── bronze/
    │   │   └── extract_boe.py
    │   │
    │   ├── silver/
    │   │   ├── config.py
    │   │   ├── connections.py
    │   │   ├── extract.py
    │   │   ├── transform.py
    │   │   ├── load.py
    │   │   └── main.py
    │   │
    │   ├── gold/
    │   │   ├── main.py
    │   │   ├── refresh_gold.sql
    │   │   └── validate_gold.sql
    │   │
    │   ├── airflow/
    │   │   └── dags/
    │   │       └── boe_pipeline.py
    │   │
    │   └── scripts/
    │       └── upload_dummy_bronze.py
    │
    └── 03_assets/
        └── BAYAN_Dashboard.pdf
```

## Python Environment

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Recommended Python version:

```text
Python 3.11+
```

## Configuration

The Silver pipeline reads connection values from environment variables.

Expected configuration includes:

```text
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD

SEAWEEDFS_ENDPOINT
SEAWEEDFS_PORT
SEAWEEDFS_BUCKET

SOURCE_NAME
```

The BOE collector also supports:

```text
BOE_PROXY_URL       # optional
BOE_VERIFY_SSL      # optional, defaults to true
```

Do not commit passwords, access keys, private connection strings, or other secrets to a public repository.

## Running the Pipeline

### Bronze

```bash
python -m bronze.extract_boe
```

The Bronze collector retrieves BOE regulatory content and stores the raw artifacts in SeaweedFS.

### Silver

```bash
python -m silver.main
```

Silver reads Bronze objects, transforms the regulatory content, and loads the structured data into PostgreSQL.

### Gold

```bash
python -m gold.main
```

Gold executes `refresh_gold.sql` and refreshes the analytics-ready tables.

### Gold Validation

Run the SQL in:

```text
gold/validate_gold.sql
```

The validation checks include duplicate keys, orphan relationships, missing versions, invalid dates, duplicate change events, and Silver-to-Gold change-count consistency.

### Airflow

The production workflow is defined in:

```text
airflow/dags/boe_pipeline.py
```

Pipeline order:

```text
Bronze → Silver → Gold
```

Schedule:

```text
0 1 * * *
```

Timezone:

```text
Asia/Riyadh
```

## Analytics

The Gold layer is used by the Power BI dashboard to provide views such as:

- Total regulations
- Regulation status
- Publication trends
- Article counts
- Regulation register
- Change-monitoring indicators

## Current Limitations and Future Work

The current implementation focuses on the BOE source and the data engineering foundation.

Planned extensions include:

- Additional official regulatory sources
- Frontend regulatory portal
- Advanced search
- Detailed version comparison
- Regulatory alerts
- Saved regulations / watchlists
- Expanded analytics and downstream data services

## Notes

- Bronze data is preserved before transformation.
- Silver prioritizes normalization and relational integrity.
- Gold prioritizes analytics and reporting.
- The final implementation should be treated as the source of truth when it differs from earlier proposal material.
