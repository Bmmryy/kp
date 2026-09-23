# FlowETL Pipeline Lifecycle & Execution

## 1. Execution Lifecycle

When `Pipeline.run()` is invoked, it traverses the following ordered phases:

```
[INIT] ──▶ [CONNECT SOURCE] ──▶ [CONNECT DESTINATION] ──▶ [EXTRACT] ──▶ [TRANSFORM] ──▶ [VALIDATE] ──▶ [LOAD] ──▶ [FINALIZE]
```

1. **Connect**: Establishes sessions and validates access credentials on both source and destination.
2. **Extract**: Streams data from the source in batches (`Dataset`), recording `rows_extracted`.
3. **Transform**: Sequentially applies configured `Transformer` instances, recording `rows_transformed`.
4. **Validate**: Enforces schema and quality rules (null checks, range constraints).
5. **Load**: Verifies target table existence (or invokes `create_schema`), then writes records via the destination connector, recording `rows_loaded`.
6. **Finalize**: Safely closes network sessions and updates execution duration and completion status.

## 2. Progress Callbacks

The pipeline engine supports real-time progress notification hooks:

```python
def on_progress(step: str, percentage: float) -> None:
    print(f"Step: {step}, Progress: {percentage * 100:.1f}%")

context = pipeline.run(progress_callback=on_progress)
```
