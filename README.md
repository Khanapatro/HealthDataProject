#  Healthcare Data Project

> An end-to-end Azure Data Engineering pipeline for Healthcare Revenue Cycle Management — from raw EMR records to analytical gold-layer fact & dimension tables, enabling real-time AR tracking and financial KPI reporting.

---

![Azure Data Factory](https://img.shields.io/badge/Azure%20Data%20Factory-0089D6?style=for-the-badge&logo=microsoftazure&logoColor=white)
![Azure Databricks](https://img.shields.io/badge/Azure%20Databricks-FF3621?style=for-the-badge&logo=databricks&logoColor=white)
![ADLS Gen2](https://img.shields.io/badge/ADLS%20Gen2-00A4EF?style=for-the-badge&logo=microsoftazure&logoColor=white)
![Delta Lake](https://img.shields.io/badge/Delta%20Lake-F7C948?style=for-the-badge&logo=delta&logoColor=black)
![Apache Spark](https://img.shields.io/badge/Apache%20Spark-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)
![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=black)
![Unity Catalog](https://img.shields.io/badge/Unity%20Catalog-A855F7?style=for-the-badge&logo=databricks&logoColor=white)
![Key Vault](https://img.shields.io/badge/Key%20Vault-7FBA00?style=for-the-badge&logo=microsoftazure&logoColor=white)

![Pipeline Layers](https://img.shields.io/badge/Pipeline%20Layers-4-blueviolet)
![Architecture](https://img.shields.io/badge/Architecture-Medallion-gold)
![SCD Type](https://img.shields.io/badge/SCD-Type%202-cyan)
![License](https://img.shields.io/badge/License-MIT-green)

---

##  Overview

An end-to-end **data engineering pipeline** that ingests multi-source Healthcare EMR data, processes it through a **Medallion Architecture** (Landing → Bronze → Silver → Gold), and delivers actionable **Revenue Cycle KPI reporting** via Delta Lake gold tables — with full audit trails, SCD2 history, and Unity Catalog governance.

---

##  Business Goals

| KPI | Target | Description |
|-----|--------|-------------|
| **AR > 90 Days Ratio** | ≤ 20% | AR older than 90 days as % of total outstanding |
| **Days in AR** | ≤ 45 Days | Average days from service to payment |
| **Collection Rate @ 30d** | 93% | Probability of collecting full payment at 30 days |
| **Collection Rate @ 90d** | 73% | Probability drops sharply — urgency of AR follow-up |

---

##  Problem Statement

Hospitals lose millions annually due to delayed billing, underpayments, and poor AR tracking. This pipeline solves:

-  **Revenue Leakage** — No structured way to track paid, pending, or denied claims
-  **Aging AR Problem** — Payment probability drops from 93% → 73% between 30 and 90 days
-  **Multi-Hospital Data Silos** — Isolated systems across Hospital A & B, insurance files, and APIs
-  **No Unified Reporting** — Finance teams lack consolidated KPI dashboards
-  **Manual Reconciliation** — Error-prone spreadsheet-based billing reconciliation
-  **Compliance & Security** — Healthcare data requires strict access control and audit trails

> **The Solution:** A unified Azure-based Medallion data pipeline that ingests, cleans, enriches, and models data from 4 source systems into a single Gold layer with full governance.

---

##  Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Orchestration | Azure Data Factory | Metadata-driven pipeline orchestration |
| Compute | Azure Databricks + Apache Spark | Distributed data processing |
| Storage | ADLS Gen2 | Medallion lakehouse storage |
| Table Format | Delta Lake | ACID transactions, time travel |
| File Format | Apache Parquet | Bronze layer columnar storage |
| Governance | Unity Catalog | 3-level namespace, access control |
| Secrets | Azure Key Vault | Secure credential management |
| Language | PySpark / Python | Transformation and enrichment logic |
| Database | Azure SQL Database | EMR source system |

---

##  Data Sources

```
4 Source Systems → 1 Unified Pipeline
```

| Source | Type | Tables / Files |
|--------|------|---------------|
| **EMR — Hospital A** | Azure SQL DB | Patients, Providers, Departments, Transactions, Encounters |
| **EMR — Hospital B** | Azure SQL DB | Patients, Providers, Departments, Transactions, Encounters |
| **Insurance Claims** | Flat Files (CSV) | Claims CSV, CPT billing codes (monthly batch) |
| **NPI + ICD APIs** | Public REST APIs | National Provider IDs, ICD diagnosis code lookup |

---

##  Architecture — Medallion Pattern

```
Landing  ──►  Bronze  ──►  Silver  ──►  Gold
 (CSV)      (Parquet)    (Delta)      (Delta)
```

| Layer | Format | Consumers | Purpose |
|-------|--------|-----------|---------|
| **Landing** | CSV / Raw files | Pipeline only | Insurance flat file drops, CPT code files |
| **Bronze** | Parquet | Data Engineers | Source of truth — raw, immutable, no transforms |
| **Silver** | Delta Tables | Data Scientists, ML Engineers | Cleaned, CDM-aligned, SCD2, quality-checked |
| **Gold** | Delta Tables | Business Users, Finance | Fact & Dimension tables, KPI-ready aggregations |

---

##  ADF Pipeline — Step by Step

```
Lookup Config ──► ForEach Tables ──► Archive Check ──► Full/Incremental Copy ──► Audit Log
```

**Step 01 — Lookup Config File**
ADF reads `configs/emr/load_config.csv` from ADLS Gen2 to determine which tables to load, load type (Full/Incremental), watermark column, and target path.

**Step 02 — ForEach: Iterate Tables**
Iterates all 10 active config entries (5 per hospital) in parallel. The `is_active` flag controls which entries are processed.

**Step 03 — Archive Check + File Move**
If a Parquet file already exists in the bronze target folder, it is moved to `bronze/<path>/archive/YYYY/MM/DD/` before overwriting.

**Step 04 — Full Load Copy Activity**
Executes `SELECT * FROM <table>` and writes all rows as Parquet to the bronze container. Used for Providers and Departments.

**Step 05 — Watermark Fetch + Incremental Copy**
Queries the audit Delta table for the last load date, then selects only rows where the watermark column (e.g. `ModifiedDate`) is >= that date.

**Step 06 — Audit Log Insert**
After each copy, inserts a record into `audit.load_logs` Delta table with source, table name, rows copied, watermark column, and UTC timestamp.

---

##  Silver Layer — SCD Type 2

| Table | Load Type | SCD2 Fields Added | Status |
|-------|-----------|-------------------|--------|
| `silver.patients` | Incremental | inserted_date, modified_date, is_current |  SCD2 |
| `silver.transactions` | Incremental | inserted_date, modified_date, is_current |  SCD2 |
| `silver.encounters` | Incremental | inserted_date, modified_date, is_current |  SCD2 |
| `silver.providers` | Full Refresh | — |  FULL |
| `silver.departments` | Full Refresh | — |  FULL |
| `silver.claims` | Incremental | inserted_date, modified_date, is_current |  SCD2 |

> Silver also applies **CDM (Common Data Model)** for consistent column naming across both hospitals, **quality checks** with an `is_quarantined` flag, and only passes `is_current = true AND is_quarantined = false` records to Gold.

---

##  Metadata-Driven Config

A single CSV drives the entire EMR ingestion pipeline — no hardcoded table names or logic in ADF.

```csv
# configs/emr/load_config.csv
database              ,datasource,tablename          ,loadtype   ,watermark    ,is_active,targetpath
trendytech-hospital-a ,hos-a     ,dbo.encounters     ,Incremental,ModifiedDate ,1        ,hosa
trendytech-hospital-a ,hos-a     ,dbo.patients       ,Incremental,ModifiedDate ,1        ,hosa
trendytech-hospital-a ,hos-a     ,dbo.transactions   ,Incremental,ModifiedDate ,1        ,hosa
trendytech-hospital-a ,hos-a     ,dbo.providers      ,Full       ,             ,1        ,hosa
trendytech-hospital-a ,hos-a     ,dbo.departments    ,Full       ,             ,1        ,hosa
trendytech-hospital-b ,hos-b     ,dbo.encounters     ,Incremental,ModifiedDate ,1        ,hosb
trendytech-hospital-b ,hos-b     ,dbo.patients       ,Incremental,Updated_Date ,1        ,hosb
trendytech-hospital-b ,hos-b     ,dbo.transactions   ,Incremental,ModifiedDate ,1        ,hosb
trendytech-hospital-b ,hos-b     ,dbo.providers      ,Full       ,             ,1        ,hosb
trendytech-hospital-b ,hos-b     ,dbo.departments    ,Full       ,             ,1        ,hosb
```

---

##  Repository Structure

> ADF is connected to this GitHub repo — `dataset/`, `factory/`, `linkedService/`, and `pipeline/` folders are **auto-managed by Azure Data Factory** via Git integration.

```
HealthDataProject/
│
├──  API Extract/                          ← Databricks notebooks: REST API ingestion
│   ├── ICD Code API extract.ipynb           ← Fetches ICD diagnosis codes → bronze/icd_codes/
│   └── NPI API extract.ipynb                ← Fetches National Provider IDs → bronze/npi_codes/
│
├──  Gold/                                 ← Databricks scripts: Gold layer transformations
│   ├── dim_cpt_code.py                      ← Dimension: CPT procedure codes
│   ├── dim_department.py                    ← Dimension: Hospital departments
│   ├── dim_icd_code.ipynb                   ← Dimension: ICD diagnosis codes
│   ├── dim_npi.ipynb                        ← Dimension: National Provider identifiers
│   ├── dim_patient.py                       ← Dimension: Patient master data
│   └── fact_transaction.sql                 ← Fact: Transactions (AR core table)
│
├──  ProjectDataset/                       ← Source data files (CSV) for pipeline input
│   ├──  EMR/
│   │   ├──  Hospital-A/                   ← Hospital A raw EMR data
│   │   │   ├── departments.csv
│   │   │   ├── encounters.csv
│   │   │   ├── patients.csv
│   │   │   ├── providers.csv
│   │   │   └── transactions.csv
│   │   └──  Hospital-B/                   ← Hospital B raw EMR data (same schema)
│   │       ├── departments.csv
│   │       ├── encounters.csv
│   │       ├── patients.csv
│   │       ├── providers.csv
│   │       └── transactions.csv
│   ├──  Claims/
│   │   ├── hospital1_claim_data.csv         ← Insurance claims — Hospital A
│   │   └── hospital2_claim_data.csv         ← Insurance claims — Hospital B
│   ├──  cptcodes/
│   │   └── cptcodes.csv                     ← CPT procedure code reference data
│   └── load_config.csv                      ← Metadata config driving ADF pipeline
│
├──  Set up/                               ← Environment bootstrap scripts
│   └── adls_mount.py                        ← Mounts ADLS Gen2 container in Databricks
│
├──  SilverLayer/                          ← Databricks scripts: Silver layer transformations
│   ├── Claims.py                            ← SCD2 + CDM for claims data
│   ├── Department.py                        ← Full refresh for departments
│   ├── ICD Code.ipynb                       ← SCD2 for ICD codes
│   ├── NPI.ipynb                            ← SCD2 for NPI provider data
│   ├── Patient.py                           ← SCD2 + CDM for patients
│   ├── Providers.py                         ← Full refresh for providers
│   ├── Transactions.py                      ← SCD2 + CDM for transactions
│   └── cptcode.py                           ← SCD2 for CPT codes
│
│   ── ADF Git Integration (auto-synced by Azure Data Factory) ──────────────────
│
├──  dataset/                              ← ADF Dataset definitions (JSON)
│   ├── AzureDatabricksDeltaLakeDataset.json ← Delta Lake dataset
│   ├── adls_flat_file.json                  ← Delimited text (CSV) on ADLS
│   ├── adls_parquet.json                    ← Parquet files on ADLS
│   └── generic_sql_db.json                  ← Azure SQL Database tables
│
├──  factory/                              ← ADF Factory-level config (JSON)
│
├──  linkedService/                        ← ADF Linked Service definitions (JSON)
│   │                                           Azure SQL DB · ADLS Gen2 · Delta Lake
│   │                                           Azure Key Vault · Azure Databricks
│
├──  pipeline/                             ← ADF Pipeline definitions (JSON)
│   └── pipeline1.json                       ← Metadata-driven EMR ingestion pipeline
│                                               (Lookup → ForEach → Archive → Copy → Audit)
│
│   ── Root Files ────────────────────────────────────────────────────────────────
│
├──  audit_table_ddl.txt                   ← DDL for audit.load_logs Delta table
├──  publish_config.json                   ← ADF publish config (Git integration)
├──  LICENSE                               ← MIT License
└──  README.md                             ← This file
```

### ADLS Gen2 Storage Layout (`ttadlsdev`)

```
ttadlsdev/
├── landing/          ← Insurance CSV drops, CPT flat files
├── bronze/           ← Parquet, source of truth (immutable)
│   ├── hosa/         ← Hospital A (encounters, patients, transactions, providers, departments)
│   │   └── archive/YYYY/MM/DD/
│   ├── hosb/         ← Hospital B (same tables)
│   ├── claims/       ← hospital1_claim_data, hospital2_claim_data
│   ├── npi_codes/    ← Written by NPI API extract.ipynb
│   └── icd_codes/    ← Written by ICD Code API extract.ipynb
├── silver/           ← Delta Tables (CDM standardized + SCD2)
│   ├── patients/ · providers/ · encounters/
│   ├── transactions/ · departments/ · claims/
│   ├── npi/ · icd_codes/ · cpt_codes/
├── gold/             ← Fact & Dimension Delta Tables
│   ├── fact_transaction/
│   ├── dim_patient/ · dim_department/
│   ├── dim_npi/ · dim_icd_code/ · dim_cpt_code/
└── configs/
    └── emr/load_config.csv
```

---

##  Audit Table Schema

```sql
-- audit.load_logs (Delta Table in Databricks)
CREATE TABLE IF NOT EXISTS audit.load_logs (
  id                   BIGINT GENERATED ALWAYS AS IDENTITY,
  data_source          STRING,      -- hos-a / hos-b
  tablename            STRING,      -- dbo.patients etc.
  numberofrowscopied   INT,         -- rows from copy activity
  watermarkcolumnname  STRING,      -- ModifiedDate / Updated_Date
  loaddate             TIMESTAMP    -- UTC timestamp of run
);
```

---

##  ADF Components

| Component | Details |
|-----------|---------|
| **Linked Services** | Azure SQL DB · ADLS Gen2 · Delta Lake · Azure Key Vault · Azure Databricks |
| **Datasets** | Azure SQL Table · Delimited Text (CSV config) · Parquet (ADLS) · Delta Lake |
| **Activities** | Lookup · ForEach · If Condition · Copy · Stored Procedure · Get Metadata · Delete |
| **Key Vault** | ADLS access keys · SQL connection strings · Databricks tokens (`tt-health-care-kv`) |

---

##  Production Enhancements

- **Unity Catalog Migration** — Migrated from Hive Metastore to Unity Catalog for `catalog.schema.table` three-level namespace and centralized governance
- **Sequential → Parallel Execution** — ADF ForEach converted to parallel, significantly reducing ingestion time for 10-table config
- **`is_active` Flag** — Enable/disable individual tables without touching pipeline logic — zero-downtime table exclusion
- **Retry Logic** — Retry policies on ADF Copy and Databricks notebook activities for transient API and network failures

---

##  Getting Started — Clone & Set Up

Follow these steps to clone the repo and get the project running locally or in your Azure environment.

---

### Step 1 — Prerequisites

Make sure you have the following installed and configured before cloning:

| Tool | Purpose | Install |
|------|---------|---------|
| **Git** | Clone the repository | [git-scm.com](https://git-scm.com/downloads) |
| **Python 3.8+** | Run setup and Silver/Gold scripts locally | [python.org](https://www.python.org/downloads/) |
| **Azure CLI** | Interact with Azure resources from terminal | [docs.microsoft.com/cli/azure](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) |
| **Azure Databricks Workspace** | Run `.py` and `.ipynb` notebooks | Azure Portal |
| **Azure Data Factory** | Orchestrate pipelines | Azure Portal |
| **ADLS Gen2 Storage Account** | Medallion lakehouse storage (`ttadlsdev`) | Azure Portal |

---

### Step 2 — Clone the Repository

Open your terminal (Git Bash, PowerShell, or Mac/Linux terminal) and run:

```bash
# Clone the repository
git clone https://github.com/Khanapatro/HealthDataProject.git

# Move into the project folder
cd HealthDataProject
```

You should now see this folder structure locally:

```
HealthDataProject/
├── API Extract/
├── Gold/
├── ProjectDataset/
├── Set up/
├── SilverLayer/
├── dataset/
├── factory/
├── linkedService/
├── pipeline/
├── audit_table_ddl.txt
├── publish_config.json
├── LICENSE
└── README.md
```

---

### Step 3 — Mount ADLS Gen2 in Databricks

Upload and run `Set up/adls_mount.py` in your Databricks workspace. This script mounts the ADLS Gen2 storage account so all notebooks can read/write to the lakehouse.

```bash
# File location in repo
Set up/adls_mount.py
```

>  Before running, update the storage account name, container names, and Key Vault secret name inside `adls_mount.py` to match your Azure environment.

---

### Step 4 — Create the Audit Table

Run the DDL from `audit_table_ddl.txt` in a Databricks SQL cell or notebook to create the audit log Delta table:

```sql
-- Copy contents of audit_table_ddl.txt and run in Databricks
CREATE TABLE IF NOT EXISTS audit.load_logs (
  id                   BIGINT GENERATED ALWAYS AS IDENTITY,
  data_source          STRING,
  tablename            STRING,
  numberofrowscopied   INT,
  watermarkcolumnname  STRING,
  loaddate             TIMESTAMP
);
```

---

### Step 5 — Upload Source Data to ADLS

Upload the CSV files from `ProjectDataset/` to your ADLS Gen2 container:

```
ProjectDataset/EMR/Hospital-A/*.csv    →  bronze/hosa/
ProjectDataset/EMR/Hospital-B/*.csv    →  bronze/hosb/
ProjectDataset/Claims/*.csv            →  landing/claims/
ProjectDataset/cptcodes/cptcodes.csv   →  landing/cpt_codes/
ProjectDataset/load_config.csv         →  configs/emr/load_config.csv
```

You can upload via **Azure Storage Explorer**, **Azure Portal**, or Azure CLI:

```bash
# Example using Azure CLI
az storage blob upload-batch \
  --account-name ttadlsdev \
  --destination bronze/hosa \
  --source "./ProjectDataset/EMR/Hospital-A"
```

---

### Step 6 — Connect ADF to GitHub (Git Integration)

> This repo already contains the ADF pipeline, dataset, linkedService, and factory folders — you just need to point ADF to this repo.

1. Open **Azure Data Factory Studio** → Click **Manage** (wrench icon)
2. Go to **Git configuration** → Click **Configure**
3. Fill in the details:

```
Repository type   : GitHub
GitHub account    : Khanapatro
Repository name   : HealthDataProject
Collaboration branch : main
Publish branch    : adf_publish
Root folder       : /
```

4. Click **Apply** — ADF will automatically load all pipelines, datasets, and linked services from the repo.

---

### Step 7 — Configure Linked Services & Key Vault

In ADF Studio → **Manage** → **Linked Services**, update the connection details for:

| Linked Service | What to update |
|---------------|----------------|
| Azure SQL DB | Server name, database name, credentials |
| ADLS Gen2 | Storage account name (`ttadlsdev`) |
| Azure Databricks | Workspace URL, cluster ID |
| Azure Key Vault | Key Vault URL (`tt-health-care-kv`) |

>  Store all passwords and access keys in **Azure Key Vault** — never hardcode them in linked service JSON files.

---

### Step 8 — Run the Pipeline

1. In ADF Studio → **Author** → **Pipelines** → Open `pipeline1`
2. Click **Debug** to run a test, or click **Add Trigger → Trigger Now** for a full run
3. Monitor progress under **Monitor** tab → **Pipeline runs**

---

### Step 9 — Run Silver & Gold Notebooks in Databricks

After the ADF bronze pipeline completes, run the transformation notebooks in order:

```
1. SilverLayer/Patient.py
2. SilverLayer/Transactions.py
3. SilverLayer/Claims.py
4. SilverLayer/Department.py
5. SilverLayer/Providers.py
6. SilverLayer/ICD Code.ipynb
7. SilverLayer/NPI.ipynb
8. SilverLayer/cptcode.py
     ↓
9. Gold/dim_patient.py
10. Gold/dim_department.py
11. Gold/dim_cpt_code.py
12. Gold/dim_icd_code.ipynb
13. Gold/dim_npi.ipynb
14. Gold/fact_transaction.sql
```

>  Gold layer is now ready for KPI reporting — AR > 90 Days, Days in AR, Collection Rate dashboards.

---

### Quick Reference — Git Commands

```bash
# Clone the repo
git clone https://github.com/Khanapatro/HealthDataProject.git

# Check status of your changes
git status

# Pull latest changes from GitHub
git pull origin main

# Stage and commit your changes
git add .
git commit -m "your message here"

# Push changes to GitHub
git push origin main

# Create and switch to a new branch
git checkout -b feature/your-feature-name

# Switch back to main
git checkout main
```

---

##  References

- [ Azure Data Factory Docs](https://docs.microsoft.com/azure/data-factory/)
- [ Azure Databricks Docs](https://docs.microsoft.com/azure/databricks/)
- [ Delta Lake](https://delta.io)
