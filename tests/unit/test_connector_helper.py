"""Unit tests for connector_helper discovery endpoints (tables, columns)."""

import sqlite3
import tempfile
from pathlib import Path
from server.api.connector_helper import list_columns, list_tables


def test_list_tables_and_columns_sqlite():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE patients (id INTEGER PRIMARY KEY, full_name TEXT, age INT, phone TEXT)")
        cur.execute("CREATE TABLE appointments (id INTEGER PRIMARY KEY, patient_id INT, reason TEXT)")
        conn.commit()
        conn.close()

        # Test list_tables
        tables_res = list_tables(type="sqlite", path=db_path)
        assert "patients" in tables_res["tables"]
        assert "appointments" in tables_res["tables"]

        # Test list_columns for patients
        cols_res = list_columns(type="sqlite", path=db_path, table="patients")
        assert cols_res["table"] == "patients"
        col_names = [c["name"] for c in cols_res["columns"]]
        assert "id" in col_names
        assert "full_name" in col_names
        assert "age" in col_names
        assert "phone" in col_names
    finally:
        Path(db_path).unlink(missing_ok=True)


def test_list_columns_csv():
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tmp:
        tmp.write("PatientID,Name,Phone,City\n1,Budi,0812,Jakarta\n")
        csv_path = tmp.name

    try:
        cols_res = list_columns(type="csv", path=csv_path)
        col_names = [c["name"] for c in cols_res["columns"]]
        assert col_names == ["PatientID", "Name", "Phone", "City"]
    finally:
        Path(csv_path).unlink(missing_ok=True)
