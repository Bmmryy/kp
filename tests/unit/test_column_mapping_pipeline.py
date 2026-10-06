"""Integration test for column selection, transformation, and mapping to existing target table."""

import sqlite3
import tempfile
from pathlib import Path
from app.connectors.sqlite import SQLiteSource, SQLiteDestination
from app.connectors.base import ConnectorConfig
from app.core.pipeline import Pipeline
from app.transformations.base import TransformerConfig
from app.transformations.registry import TransformationRegistry
import app.transformations  # register all


def test_pipeline_with_column_mapping_to_existing_table():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # 1. Source table with 5 columns
        cur.execute("CREATE TABLE source_patients (id INT, full_name TEXT, phone_no TEXT, city_name TEXT, secret_code TEXT)")
        cur.execute("INSERT INTO source_patients VALUES (1, 'budi santoso', '081234567890', 'jakarta', 'SECRET_1')")
        cur.execute("INSERT INTO source_patients VALUES (2, 'siti aminah', '081987654321', 'bandung', 'SECRET_2')")

        # 2. Existing Target table with different column names (and an extra target column)
        cur.execute("CREATE TABLE target_rekap (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_pasien TEXT, kontak TEXT, domisili TEXT, catatan TEXT DEFAULT 'OK')")
        conn.commit()
        conn.close()

        # Connectors
        src = SQLiteSource(ConnectorConfig(name="src", connector_type="sqlite", options={"database": db_path}))
        dst = SQLiteDestination(ConnectorConfig(name="dst", connector_type="sqlite", options={"database": db_path}))

        # Transformations:
        # Step 1: UPPERCASE on full_name
        t1 = TransformationRegistry.create(TransformerConfig(type="uppercase", params={"columns": ["full_name"]}))
        # Step 2: Mask phone_no
        t2 = TransformationRegistry.create(TransformerConfig(type="mask", params={"columns": ["phone_no"], "mask_char": "*", "keep_start": 4, "keep_end": 3}))
        # Step 3: Column Mapping (source -> target columns, dropping unmapped secret_code and id)
        t3 = TransformationRegistry.create(TransformerConfig(
            type="column_mapping",
            params={
                "mapping": {
                    "full_name": "nama_pasien",
                    "phone_no": "kontak",
                    "city_name": "domisili",
                },
                "drop_unmapped": True,
                "target_table": "target_rekap",
            }
        ))

        pipeline = Pipeline(
            name="Test Task 1",
            source=src,
            destination=dst,
            source_table="source_patients",
            destination_table="target_rekap",
            load_mode="append",
            transformations=[t1, t2, t3],
        )

        ctx = pipeline.run()
        assert ctx.status.value == "SUCCESS"
        assert ctx.metrics.rows_extracted == 2
        assert ctx.metrics.rows_loaded == 2

        # Verify target table content in SQLite
        conn2 = sqlite3.connect(db_path)
        cur2 = conn2.cursor()
        rows = cur2.execute("SELECT nama_pasien, kontak, domisili, catatan FROM target_rekap ORDER BY id").fetchall()
        conn2.close()

        assert len(rows) == 2
        # Row 1: UPPERCASE applied, phone masked, city mapped, default column intact
        assert rows[0][0] == "BUDI SANTOSO"
        assert rows[0][1] == "0812*****890"
        assert rows[0][2] == "jakarta"
        assert rows[0][3] == "OK"

        # Row 2
        assert rows[1][0] == "SITI AMINAH"
        assert rows[1][1] == "0819*****321"
        assert rows[1][2] == "bandung"
        assert rows[1][3] == "OK"

    finally:
        Path(db_path).unlink(missing_ok=True)
