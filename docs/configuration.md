# FlowETL Configuration Specification

## 1. Overview

FlowETL pipelines are declaratively defined in YAML or JSON, adhering to Pydantic models in `app.utils.config`.

## 2. YAML Pipeline Structure

```yaml
name: hospital_patient_sync
description: "Sync patient records from MySQL to PostgreSQL analytics warehouse"

source:
  type: mysql
  connection: production_mysql
  table: patients
  query: "SELECT * FROM patients WHERE is_active = 1"
  options:
    chunk_size: 5000

transformations:
  - type: select_columns
    params:
      columns:
        - patient_id
        - name
        - age
        - diagnosis
  - type: rename
    params:
      mapping:
        name: patient_name
  - type: filter
    params:
      condition: "age >= 18"

destination:
  type: postgresql
  connection: analytics_dw
  table: dim_patients
  mode: append # append | replace | truncate
```

## 3. Environment Variables

Sensitive secrets (passwords, connection URIs) are loaded through environment variables or `.env` files:
- `FLOWETL_ENV`
- `FLOWETL_LOG_LEVEL`
- `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`
- `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
