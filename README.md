# 🏥 Healthcare Data Project

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

## 📌 Overview

An end-to-end **data engineering pipeline** that ingests multi-source Healthcare EMR data, processes it through a **Medallion Architecture** (Landing → Bronze → Silver → Gold), and delivers actionable **Revenue Cycle KPI reporting** via Delta Lake gold tables — with full audit trails, SCD2 history, and Unity Catalog governance.

---

## 🎯 Business Goals

| KPI | Target | Description |
|-----|--------|-------------|
| **AR > 90 Days Ratio** | ≤ 20% | AR older than 90 days as % of total outstanding |
| **Days in AR** | ≤ 45 Days | Average days from service to payment |
| **Collection Rate @ 30d** | 93% | Probability of collecting full payment at 30 days |
| **Collection Rate @ 90d** | 73% | Probability drops sharply — urgency of AR follow-up |

---

## ⚠️ Problem Statement

Hospitals lose millions annually due to delayed billing, underpayments, and poor AR tracking. This pipeline solves:

- 💸 **Revenue Leakage** — No structured way to track paid, pending, or denied claims
- ⏳ **Aging AR Problem** — Payment probability drops from 93% → 73% between 30 and 90 days
- 🏥 **Multi-Hospital Data Silos** — Isolated systems across Hospital A & B, insurance files, and APIs
- 📋 **No Unified Reporting** — Finance teams lack consolidated KPI dashboards
- 🔄 **Manual Reconciliation** — Error-prone spreadsheet-based billing reconciliation
- 🔐 **Compliance & Security** — Healthcare data requires strict access control and audit trails

> **The Solution:** A unified Azure-based Medallion data pipeline that ingests, cleans, enriches, and models data from 4 source systems into a single Gold layer with full governance.

---

## 🛠️ Tech Stack

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

## 📥 Data Sources

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

## 🏛️ Architecture — Medallion Pattern

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

## ⚙️ ADF Pipeline — Step by Step

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

## 🥈 Silver Layer — SCD Type 2

| Table | Load Type | SCD2 Fields Added | Status |
|-------|-----------|-------------------|--------|
| `silver.patients` | Incremental | inserted_date, modified_date, is_current | ✅ SCD2 |
| `silver.transactions` | Incremental | inserted_date, modified_date, is_current | ✅ SCD2 |
| `silver.encounters` | Incremental | inserted_date, modified_date, is_current | ✅ SCD2 |
| `silver.providers` | Full Refresh | — | 🔄 FULL |
| `silver.departments` | Full Refresh | — | 🔄 FULL |
| `silver.claims` | Incremental | inserted_date, modified_date, is_current | ✅ SCD2 |

> Silver also applies **CDM (Common Data Model)** for consistent column naming across both hospitals, **quality checks** with an `is_quarantined` flag, and only passes `is_current = true AND is_quarantined = false` records to Gold.

---

## 📋 Metadata-Driven Config

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

## 🗂️ ADLS Gen2 Folder Layout

```
ttadlsdev/                         ← Storage Account
│
├── landing/                       ← Insurance CSV drops, CPT flat files
│   ├── claims/
│   └── cpt_codes/
│
├── bronze/                        ← Source of truth, Parquet format
│   ├── hosa/                      ← Hospital A
│   │   ├── encounters.parquet
│   │   ├── patients.parquet
│   │   ├── transactions.parquet
│   │   ├── providers.parquet
│   │   ├── departments.parquet
│   │   └── archive/YYYY/MM/DD/
│   ├── hosb/                      ← Hospital B
│   ├── claims/
│   ├── npi_codes/
│   └── icd_codes/
│
├── silver/                        ← Delta Tables, CDM, SCD2
│   ├── patients/
│   ├── providers/
│   ├── encounters/
│   ├── transactions/
│   ├── departments/
│   └── claims/
│
├── gold/                          ← Fact & Dimension Tables
│   ├── fact_transactions/
│   ├── dim_patients/
│   ├── dim_providers/
│   └── dim_departments/
│
└── configs/                       ← Metadata-driven pipeline config
    └── emr/
        └── load_config.csv
```

---

## 📊 Audit Table Schema

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

## 🔗 ADF Components

| Component | Details |
|-----------|---------|
| **Linked Services** | Azure SQL DB · ADLS Gen2 · Delta Lake · Azure Key Vault · Azure Databricks |
| **Datasets** | Azure SQL Table · Delimited Text (CSV config) · Parquet (ADLS) · Delta Lake |
| **Activities** | Lookup · ForEach · If Condition · Copy · Stored Procedure · Get Metadata · Delete |
| **Key Vault** | ADLS access keys · SQL connection strings · Databricks tokens (`tt-health-care-kv`) |

---

## 🚀 Production Enhancements

- **Unity Catalog Migration** — Migrated from Hive Metastore to Unity Catalog for `catalog.schema.table` three-level namespace and centralized governance
- **Sequential → Parallel Execution** — ADF ForEach converted to parallel, significantly reducing ingestion time for 10-table config
- **`is_active` Flag** — Enable/disable individual tables without touching pipeline logic — zero-downtime table exclusion
- **Retry Logic** — Retry policies on ADF Copy and Databricks notebook activities for transient API and network failures

---

## 📚 References

- [🌐 TrendyTech](https://trendytech.in) — Ultimate Data Engineering Program by Sumit Sir
- [📘 Azure Data Factory Docs](https://docs.microsoft.com/azure/data-factory/)
- [⚡ Azure Databricks Docs](https://docs.microsoft.com/azure/databricks/)
- [Δ Delta Lake](https://delta.io)

---

*Data generated using Python Faker · For educational purposes*
