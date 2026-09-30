
# بيان | BAYAN

### Saudi Regulations & Decisions Data Hub

> **Finding a regulation is easy. Understanding how it changed over time is a different problem.**

**BAYAN (بيان)** — meaning *clarity* — is a data engineering platform designed to transform Saudi regulatory publications into structured, version-aware, and analytics-ready data.

The current implementation starts with regulations published by the **Saudi Bureau of Experts at the Council of Ministers (BOE)** and processes them through an automated, layered data pipeline.

**BOE → Bronze → Silver → Gold → Power BI**

BAYAN was developed as a **Data Engineering Capstone Project** for the **Saudi Digital Academy**, in partnership with **WeCloudData**.

---

## The Problem

Regulatory information is publicly available, but analyzing it as data introduces several challenges.

Regulations may contain complex document structures, Arabic textual variations, multiple articles and chapters, different effective dates, and changes that occur over time.

Simply retrieving a regulation does not answer questions such as:

- What is the current version of this regulation?
- What previous versions existed?
- Which articles changed?
- When did a change become effective?
- How can regulatory information be analyzed across hundreds of regulations?

BAYAN addresses this by transforming regulatory publications into a structured and historically traceable data model.

---

## Our Solution

BAYAN implements an automated data pipeline that collects regulatory content, preserves the original source artifacts, transforms the content into structured relational data, tracks regulatory changes, and prepares curated datasets for analytics.

The pipeline follows a **Medallion Architecture**:

```text
Saudi Bureau of Experts (BOE)
              │
              ▼
        ┌───────────┐
        │  BRONZE   │
        │ SeaweedFS │
        └─────┬─────┘
              │
              ▼
        ┌────────────┐
        │   SILVER   │
        │ PostgreSQL │
        └─────┬──────┘
              │
              ▼
        ┌────────────┐
        │    GOLD    │
        │ PostgreSQL │
        └─────┬──────┘
              │
              ▼
        ┌──────────┐
        │ Power BI │
        └──────────┘
```

The complete workflow is orchestrated using **Apache Airflow** and containerized using **Docker**.

---

## Data Pipeline

### 🥉 Bronze — Raw Data

The Bronze layer preserves regulatory content as collected from the source before transformation.

**Technology:** SeaweedFS

Stored artifacts include raw regulatory text and associated source documents when available.

This layer provides:

- Source preservation
- Traceability
- Reproducibility
- Reprocessing capability

---

### 🥈 Silver — Structured Data

The Silver layer transforms raw regulatory content into normalized relational data.

**Technology:** PostgreSQL

The transformation process includes:

- Regulation metadata extraction
- Chapter and article parsing
- Arabic heading normalization
- Date normalization
- Regulation status handling
- Duplicate prevention
- Relational integrity
- Regulation version tracking
- Article version tracking
- Content-based change detection

The resulting model represents regulations, their versions, chapters, articles, and historical article versions as structured data.

---

### 🥇 Gold — Analytics-Ready Data

The Gold layer transforms the structured Silver data into curated analytical models.

**Technology:** PostgreSQL

The Gold model includes dimensions and facts designed for downstream analytics, including:

- Regulations
- Articles
- Dates
- Change types
- Article change events

The resulting datasets are consumed by **Power BI** for reporting and regulatory analysis.

---

## Version Tracking & Change Detection

One of BAYAN's core capabilities is preserving regulatory history instead of overwriting previously collected data.

When a regulation is processed again, the pipeline:

1. Collects the latest regulatory content.
2. Normalizes the relevant text.
3. Generates a content fingerprint/hash.
4. Compares it with the previously stored version.
5. Keeps the existing version when no change is detected.
6. Creates and preserves a new version when a change is detected.

This allows BAYAN to maintain a historical record of regulatory content and support analysis of changes over time.

---

## Orchestration

The end-to-end pipeline is orchestrated using **Apache Airflow**.

```text
Bronze
   │
   ▼
Silver
   │
   ▼
Gold
```

The primary DAG executes the complete pipeline automatically:

```text
boe_pipeline
```

The pipeline is scheduled to run:

**Daily at 1:00 AM — Asia/Riyadh**

This enables BAYAN to periodically collect new source data, process regulatory changes, and refresh analytics-ready datasets.

---

## Key Engineering Features

- Automated regulatory data collection
- Medallion data architecture
- Raw source preservation
- Incremental data processing
- Content-hash change detection
- Regulation version tracking
- Article-level version tracking
- Historical data preservation
- Arabic regulatory text normalization
- Relational data modeling
- Dimensional data modeling
- Data quality validation
- Duplicate prevention
- Automated Airflow orchestration
- Containerized infrastructure
- Analytics-ready data marts

---

## Technology Stack

| Area                 | Technologies           |
| -------------------- | ---------------------- |
| Data Collection      | Python                 |
| Object Storage       | SeaweedFS              |
| Data Transformation  | Python, SQL            |
| Relational Database  | PostgreSQL             |
| Orchestration        | Apache Airflow         |
| Containerization     | Docker, Docker Compose |
| Analytics            | Power BI               |
| Database Development | DBeaver                |
| Version Control      | Git, GitHub            |

---

## Analytics

BAYAN's Gold layer feeds a Power BI dashboard designed to provide analytical views of the collected regulatory data.

The current dashboard includes indicators and views such as:

- Total regulations
- Regulation status distribution
- Publication trends
- Article counts
- Regulation register
- Regulatory change-monitoring indicators

Dashboard materials and demonstrations are available in the [`03_assets/`](./02_code/03_assets/) and  [`04_presentation/`](./04_presentation/) directories.

---

## Current Scope

The current implementation focuses on regulations published by the **Saudi Bureau of Experts at the Council of Ministers**.

The architecture was designed so that additional official regulatory sources can be incorporated in future iterations without redesigning the complete pipeline.

Potential extensions include:

- Additional official Saudi regulatory sources
- Detailed regulation-version comparison
- Advanced regulatory search
- Regulatory alerts
- Saved regulations and watchlists
- Frontend regulatory portal
- Expanded analytical capabilities
- Additional downstream data services

---

## Repository Structure

```text
Bayan_Saudi_Regulations_Decisions_Data_Hub_Group01/
│
├── 01_proposal/
│   └── Project proposal and initial design
│
├── 02_code/
│   ├── 01_data/
│   ├── 02_src/
│   ├── 03_assets/
│   └── README.md
│
├── 03_project_report/
│   └── Final project report
│
├── 04_presentation/
│   └── Presentation, dashboard demo, and project video
│
├── postgres/
│   └── init/
│
├── .dockerignore
├── .gitignore
├── Dockerfile.airflow
├── docker-compose.yml
└── README.md
```

For technical documentation, environment configuration, pipeline execution, and implementation details, see:

**[`02_code/README.md`](./02_code/README.md)**

---

## Project Deliverables

All major project deliverables are included directly in this repository.

### 📄 Project Proposal

The original project proposal and initial design materials are available in:

**[`01_proposal/`](./01_proposal/)**

### 💻 Source Code & Technical Documentation

The implementation and detailed technical documentation are available in:

**[`02_code/`](./02_code/)**

For setup and execution instructions:

**[`02_code/README.md`](./02_code/README.md)**

### 📑 Final Project Report

The complete project report, including the methodology, architecture, implementation, and project findings, is available in:

**[`03_project_report/`](./03_project_report/)**

### 🎬 Presentation & Project Demo

The final presentation, dashboard demonstration, and project video are available in:

**[`04_presentation/`](./04_presentation/)**

---

## Project Team

BAYAN was developed by:

**Norah Aldakhil** | Nourasuliman.a@gmail.com
[LinkedIn](https://www.linkedin.com/in/norah-aldakhil-?utm_source=share_via&utm_content=profile&utm_medium=member_ios)

**Yaqeen Alhalal** | YaqeenAlhalal@outlook.sa
[LinkedIn](https://www.linkedin.com/in/yaqeen-alhalal-8388541a3/)

**Shouq Alotaibi** | Shouqmg1@gmail.com
[LinkedIn](https://www.linkedin.com/in/shouq-alotaibi-389980253?utm_source=share_via&utm_content=profile&utm_medium=member_ios)

### Program

**Saudi Digital Academy — Data Engineering Capstone Project**

In partnership with **WeCloudData**

Additional team and contact information can be found here:

[Team &amp; Contact Information](https://bayan-team.carrd.co)

---

## About BAYAN

**بيان** means *clarity*.

The project was built around a simple idea:

> Regulatory data should not only be accessible — it should be structured, traceable, and understandable over time.

BAYAN turns regulatory publications into data that can be processed, versioned, analyzed, and extended for future regulatory intelligence applications.

Watch out for future updates 👀
