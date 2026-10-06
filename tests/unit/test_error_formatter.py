"""Unit tests for user-friendly error formatting."""
import pytest
from app.utils.error_formatter import format_user_error


def test_format_incorrect_integer_error():
    raw = (
        "Failed to insert records into mysql table 'bidang': (pymysql.err.DataError) "
        "(1366, \"Incorrect integer value: '***' for column 'dept_Id' at row 1\") "
        "[SQL: INSERT INTO `bidang` (`dept_Id`, `dept_Name`) VALUES (%(dept_Id)s, %(dept_Name)s)] "
        "[parameters: [{'dept_Id': '***', 'dept_Name': 'CARDIOLOGY'}]] "
        "(Background on this error at: https://sqlalche.me/e/20/9h9h)"
    )
    result = format_user_error(raw)
    assert "Tipe Data Tidak Cocok" in result
    assert "dept_Id" in result
    assert "tidak dapat dimasukkan ke kolom angka" in result
    assert "[SQL:" not in result
    assert "Background on this error" not in result


def test_format_duplicate_primary_key_error():
    raw = (
        "Failed to insert records into mysql table 'divisi': (pymysql.err.IntegrityError) "
        "(1062, \"Duplicate entry '101' for key 'divisi.PRIMARY'\") "
        "[SQL: INSERT INTO `divisi` (`dept_Id`) VALUES (101)]"
    )
    result = format_user_error(raw)
    assert "Data Duplikat" in result
    assert "101" in result
    assert "[SQL:" not in result


def test_format_table_does_not_exist():
    raw = "(pymysql.err.ProgrammingError) (1146, \"Table 'tes.divisi' doesn't exist\")"
    result = format_user_error(raw)
    assert "Tabel Tidak Ditemukan" in result
    assert "tes.divisi" in result


def test_format_access_denied():
    raw = "(pymysql.err.OperationalError) (1045, \"Access denied for user 'root'@'localhost'\")"
    result = format_user_error(raw)
    assert "Akses Ditolak" in result


def test_format_connection_refused():
    raw = "(2003, \"Can't connect to MySQL server on '127.0.0.1' ([Errno 61] Connection refused)\")"
    result = format_user_error(raw)
    assert "Koneksi Gagal" in result
