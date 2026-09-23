# FlowETL Architecture Guide

## 1. Architectural Philosophy

FlowETL adopts a **Modular Layered Architecture** with **Adapter/Plugin** and **Pipeline** design patterns. 

The fundamental rule of FlowETL is:
> **Never build tight pairwise translators between data sources.**

Instead of creating $N \times (N-1)$ bespoke connectors (e.g. MySQL-to-Postgres, Postgres-to-SQLite, CSV-to-MySQL), all data ingested into FlowETL is translated into a **Universal Canonical Intermediate Representation (IR)** before transformations or loads occur.

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Source DB / File│ ───▶  │ Source Connector│ ───▶  │ Canonical Model │
└─────────────────┘       └─────────────────┘       │    (Dataset)    │
                                                    └────────┬────────┘
                                                             │
                                                             ▼
                                                    ┌─────────────────┐
                                                    │  Transformation │
                                                    │     Engine      │
                                                    └────────┬────────┘
                                                             │
                                                             ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Target DB / File│ ◀───  │ Dest. Connector │ ◀───  │ Schema Mapping  │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

---

## 2. Core Components

### 2.1 Internal Data Model (`app.schema.models`)
- `DataType`: Enumeration of canonical types (`INTEGER`, `FLOAT`, `DECIMAL`, `STRING`, `BOOLEAN`, `DATE`, `DATETIME`, `TIME`, `JSON`, `BINARY`).
- `ColumnDefinition`: Metadata for a column including name, canonical data type, nullability, primary key constraints, and default values.
- `TableSchema`: An ordered collection of `ColumnDefinition` objects representing a table or dataset entity.
- `Dataset`: Encapsulates tabular row records alongside the corresponding `TableSchema`.

### 2.2 Base Connector Contract (`app.connectors.base`)
- `SourceConnector`: Abstract base class responsible for:
  - Connecting & testing credentials
  - Discovering available tables / collections
  - Extracting source schemas into `TableSchema`
  - Streaming data chunks as canonical `Dataset` instances
- `DestinationConnector`: Abstract base class responsible for:
  - Connecting & testing write permissions
  - Creating target tables/schemas from canonical `TableSchema`
  - Writing/loading canonical `Dataset` batches with configurable modes (`append`, `replace`, `truncate`)

### 2.3 Transformation Engine (`app.transformations.base`)
- `Transformer`: Pluggable component taking a `Dataset` and producing an altered `Dataset`, with pre-computed output schema capabilities (`get_output_schema`).

### 2.4 Pipeline Orchestrator (`app.core.pipeline`)
- Coordinates the complete lifecycle:
  `Connect -> Extract -> Transform -> Validate -> Load -> Close`.
- Automatically aggregates throughput metrics (`rows_extracted`, `rows_transformed`, `rows_loaded`, `duration`).
- Records step-by-step progress callbacks for real-time visualization in the UI.

### 2.5 Observability & Context (`app.core.context`)
- Every execution generates a unique `run_id`.
- Captures status transitions: `PENDING -> RUNNING -> SUCCESS / FAILED`.
- Collects structured timestamps, error contexts, and user-facing remediation advice.

### 2.6 Domain Exception System (`app.core.exceptions`)
- Implements `FlowETLError` with dedicated user-facing guidance.
- Masks low-level driver stack traces from non-technical users while recording detailed traces into technical logs.
