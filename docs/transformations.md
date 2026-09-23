# FlowETL Transformation Engine

## 1. Overview

Transformations in FlowETL operate purely on canonical `Dataset` instances, ensuring that transformation logic is completely agnostic to whether the source was a MySQL database, an Excel spreadsheet, or a MongoDB collection.

## 2. Transformer Contract

Each transformation step inherits from `Transformer`:

```python
class Transformer(ABC):
    def __init__(self, config: TransformerConfig) -> None:
        self.config = config

    @abstractmethod
    def transform(self, dataset: Dataset) -> Dataset:
        """Apply transformation rules to the incoming Dataset."""

    @abstractmethod
    def get_output_schema(self, input_schema: TableSchema) -> TableSchema:
        """Calculate resulting schema without needing to process rows."""

    def validate_input(self, dataset: Dataset) -> bool:
        """Verify preconditions (e.g. required columns exist)."""
        return True
```

## 3. Supported & Planned Transformation Categories

1. **Column Operations**:
   - `select_columns`: Keep only a specified subset of columns
   - `remove_columns`: Drop unwanted columns
   - `rename`: Rename columns from mapping dict
   - `reorder`: Reorder column order

2. **Data Cleansing**:
   - `cast`: Change canonical type of column
   - `trim`: Strip whitespace from string columns
   - `lowercase` / `uppercase`: Adjust text case
   - `fill_null`: Replace null values with defaults
   - `deduplicate`: Eliminate duplicate rows based on subset of key columns

3. **Row Filtering**:
   - `filter`: Evaluate conditions (e.g., `age >= 18`)

4. **Relational**:
   - `join`: Join two datasets on common keys
   - `aggregate`: Compute sums, counts, averages grouped by dimensions
