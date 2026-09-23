# FlowETL

> **A generic, visual data integration and ETL platform designed with clean architecture, high modularity, type safety, and an Apple-inspired minimalist aesthetic.**

---

## 1. Overview

**FlowETL** is a modular ETL engine and upcoming visual platform designed to seamlessly extract, transform, map schemas, and load data across heterogeneous data sources without brittle pair-to-pair tightly coupled scripts.

Instead of writing specific pairwise translators (`MySQL -> PostgreSQL`, `PostgreSQL -> SQLite`, etc.), FlowETL mediates all data transfers through a strongly-typed **Internal Canonical Data Model**:

```
SOURCE CONNECTOR ───▶ CANONICAL DATA MODEL ───▶ TRANSFORM ENGINE ───▶ DESTINATION CONNECTOR
  (MySQL, Postgres,       (DataType, Schema,       (Select, Filter,     (Postgres, MySQL,
   CSV, Mongo, etc.)         Dataset Rows)           Cast, Rename)        SQLite, CSV, etc.)
```

---

## 2. Core Architectural Principles

- **Separation of Concerns**: Core pipeline logic is completely decoupled from UI and individual database dialects.
- **Open for Extension**: Adding a new connector or transformation only requires subclassing base interfaces and registering them.
- **Type Safety**: Strictly defined schema contracts (`DataType`, `ColumnDefinition`, `TableSchema`) validate data integrity.
- **Observability**: Execution runs automatically track metrics (`rows_extracted`, `rows_transformed`, `rows_loaded`, `duration`), structured timestamps, and lifecycle states.
- **Human-Centric Error Handling**: Detailed technical exceptions are cleanly mapped to helpful, actionable messages for end users while preserving deep logs for developers.

---

## 3. Project Structure

```
flowetl/
├── app/
│   ├── core/
│   │   ├── pipeline.py       # Core ETL execution orchestrator
│   │   ├── context.py        # Observability, metrics, and lifecycle state
│   │   └── exceptions.py     # Friendly domain exception hierarchy
│   ├── connectors/
│   │   ├── base.py           # SourceConnector & DestinationConnector ABCs
│   │   └── registry.py       # Pluggable connector registry
│   ├── transformations/
│   │   ├── base.py           # Transformer ABC and config models
│   │   └── registry.py       # Pluggable transformation registry
│   ├── schema/
│   │   └── models.py         # Canonical types, TableSchema, ColumnDefinition, Dataset
│   ├── utils/
│   │   ├── logging.py        # Structured, contextual logging
│   │   └── config.py         # Declarative YAML & dictionary configuration parser
│   ├── services/             # High-level application services
│   └── validation/           # Data quality rules & schema validators
├── configs/
│   └── pipelines/            # Declarative pipeline configurations
├── docs/                     # Architecture, connector, and developer guides
├── examples/                 # Sample pipeline YAML definitions
├── tests/
│   └── unit/                 # Pytest test suite
├── run.py                    # Runnable verification demo
├── requirements.txt          # Python dependencies
└── pyproject.toml            # Project packaging specification
```

---

## 4. Quickstart

### 4.1 Prerequisites
- Python 3.10+ (tested on Python 3.12, 3.14)

### 4.2 Setup Virtual Environment & Install Dependencies

```bash
cd flowetl
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4.3 Run Core Verification Demo

```bash
python3 run.py
```

### 4.4 Run Test Suite

```bash
pytest tests/
```

---

## 5. Visual Foundation & Color Palette

FlowETL adheres to a minimalist visual philosophy:

| Role | Color Hex | Usage |
| :--- | :--- | :--- |
| **Background** | `#F5F5F7` | Neutral canvas, clean workspace |
| **Primary Text** | `#1D1D1F` | High-contrast typography & headings |
| **Secondary Text** | `#AAAAAA` | Metadata, helpers, subtitles |
| **Accent / Action**| `#007AFF` | Primary buttons, active states, progress |

---

## 6. Development Roadmap

- [x] **STEP 1 — Project Foundation & Core Architecture** *(Current)*
- [ ] **STEP 2 — Internal Data Model & Registry Extensions**
- [ ] **STEP 3 — Connector Interface & Local Connectors (CSV, JSON)**
- [ ] **STEP 4 — Relational Connectors (MySQL, PostgreSQL, SQLite)**
- [ ] **STEP 5 — Transformation Engine (Select, Rename, Filter, Cast, Deduplicate)**
- [ ] **STEP 6 — Schema Mapping Engine (Source Type -> Canonical -> Target Type)**
- [ ] **STEP 7 — Data Quality & Validation Engine**
- [ ] **STEP 8 — Streamlit Visual Builder UI**
- [ ] **STEP 9 — Hospital Management System End-to-End Migration Test**
