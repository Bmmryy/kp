# FlowETL Developer & Contribution Guide

## 1. Local Environment Setup

1. Clone or navigate to the repository directory:
   ```bash
   cd flowetl
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 2. Running Unit Tests

Execute the pytest suite:
```bash
pytest tests/ -v
```

## 3. Adding a New Connector

1. Create a new module under `app/connectors/<connector_name>.py`.
2. Implement either `SourceConnector` or `DestinationConnector`.
3. Register the connector in `ConnectorRegistry`:
   ```python
   ConnectorRegistry.register_source("my_db", MyDBSource)
   ```
4. Add unit and integration tests under `tests/unit/test_<connector_name>.py`.

## 4. Adding a New Transformation

1. Create a class inheriting from `Transformer` under `app/transformations/`.
2. Implement `transform(dataset)` and `get_output_schema(input_schema)`.
3. Register it with `TransformationRegistry`:
   ```python
   TransformationRegistry.register("my_transformer", MyTransformer)
   ```
4. Write unit tests verifying input schema validation and output rows.
