"""Utilities for sanitizing technical database and pipeline exceptions into clear,
human-readable error messages for end users.
"""
from __future__ import annotations

import re
from typing import Any, Optional


def format_user_error(error: Any) -> str:
    """Converts raw exceptions and stack-trace-heavy SQL error messages into
    concise, human-readable explanations without internal code dumps or SQL statements.
    """
    if error is None:
        return "Terjadi kesalahan tidak diketahui."

    msg = str(error)

    # 1. Incorrect integer / numeric data error (MySQL 1366, Postgres 22P02, etc.)
    m = re.search(r"Incorrect (?:integer|numeric|decimal|double|float) value:\s*([^\s]+)\s*for column\s*([^\s]+)", msg, re.IGNORECASE)
    if m:
        val = m.group(1).strip("'\"`")
        col = m.group(2).strip("'\"`")
        return f"Tipe Data Tidak Cocok: Nilai '{val}' tidak dapat dimasukkan ke kolom angka '{col}'. Pastikan kolom angka tidak diubah menjadi teks atau disensor (masking)."

    m = re.search(r"invalid input syntax for (?:type )?(?:integer|numeric|smallint|bigint):\s*([^\s,]+)", msg, re.IGNORECASE)
    if m:
        val = m.group(1).strip("'\"`")
        return f"Tipe Data Tidak Cocok: Nilai '{val}' bukan angka yang valid untuk kolom database tujuan."

    # 2. Duplicate Primary Key / Unique Constraint (MySQL 1062, Postgres 23505, SQLite 19)
    m = re.search(r"Duplicate entry\s*('?[^']+?'?|\S+)\s*for key\s*([^\s)]+)", msg, re.IGNORECASE)
    if m:
        val = m.group(1).strip("'\"`")
        key = m.group(2).strip("'\"`)\\")
        return f"Data Duplikat (Primary Key): Nilai '{val}' sudah ada pada tabel tujuan (kunci: '{key}'). Kosongkan tabel atau gunakan tabel baru."

    m = re.search(r"duplicate key value violates unique constraint\s*([^\s]+)", msg, re.IGNORECASE)
    if m:
        key = m.group(1).strip("'\"`")
        return f"Data Duplikat: Data melanggar batasan unik (unique key: '{key}')."

    m = re.search(r"UNIQUE constraint failed:\s*([^\s]+)", msg, re.IGNORECASE)
    if m:
        col = m.group(1).strip("'\"`")
        return f"Data Duplikat: Nilai pada kolom '{col}' sudah terdaftar dan tidak boleh kembar."

    # 3. Table doesn't exist (MySQL 1146, Postgres 42P01, SQLite 1)
    m = re.search(r"Table\s*([^\s]+)\s*doesn't exist", msg, re.IGNORECASE)
    if m:
        tbl = m.group(1).strip("'\"`")
        return f"Tabel Tidak Ditemukan: Tabel '{tbl}' belum ada di database tujuan."

    m = re.search(r"relation\s*([^\s]+)\s*does not exist", msg, re.IGNORECASE)
    if m:
        tbl = m.group(1).strip("'\"`")
        return f"Tabel Tidak Ditemukan: Tabel '{tbl}' tidak ditemukan di PostgreSQL."

    m = re.search(r"no such table:\s*([^\s]+)", msg, re.IGNORECASE)
    if m:
        tbl = m.group(1).strip("'\"`")
        return f"Tabel Tidak Ditemukan: Tabel '{tbl}' tidak ditemukan."

    # 4. Unknown column / column not found (MySQL 1054, Postgres 42703)
    m = re.search(r"Unknown column\s*([^\s]+)\s*in", msg, re.IGNORECASE)
    if m:
        col = m.group(1).strip("'\"`")
        return f"Kolom Tidak Ditemukan: Kolom '{col}' tidak ada pada tabel tujuan. Periksa pemetaan kolom."

    m = re.search(r"column\s*([^\s]+)\s*does not exist", msg, re.IGNORECASE)
    if m:
        col = m.group(1).strip("'\"`")
        return f"Kolom Tidak Ditemukan: Kolom '{col}' tidak ada pada tabel tujuan."

    # 5. Column cannot be null / NOT NULL constraint (MySQL 1048, Postgres 23502, SQLite 19)
    m = re.search(r"Column\s*([^\s]+)\s*cannot be null", msg, re.IGNORECASE)
    if m:
        col = m.group(1).strip("'\"`")
        return f"Kolom Wajib Diisi: Kolom '{col}' tidak boleh kosong (NOT NULL). Pastikan kolom ini dipetakan dan memiliki nilai."

    m = re.search(r"null value in column\s*([^\s]+)\s*violates not-null constraint", msg, re.IGNORECASE)
    if m:
        col = m.group(1).strip("'\"`")
        return f"Kolom Wajib Diisi: Kolom '{col}' tidak boleh kosong (NOT NULL) di database tujuan."

    # 6. Data truncated / string length exceeded (MySQL 1265/1406)
    m = re.search(r"Data too long for column\s*([^\s]+)", msg, re.IGNORECASE)
    if m:
        col = m.group(1).strip("'\"`")
        return f"Data Terlalu Panjang: Panjang teks melebihi kapasitas kolom '{col}'."

    # 7. Connection & Authentication errors
    if "Access denied for user" in msg or "password authentication failed" in msg:
        return "Akses Ditolak: Username atau password database salah."

    if "Can't connect to MySQL server" in msg or "Connection refused" in msg or "Is the server running" in msg:
        return "Koneksi Gagal: Server database tidak dapat dihubungi. Pastikan database sedang aktif di host dan port yang ditentukan."

    # 8. Clean fallback: Strip raw SQL queries, params, and SQLAlchemy URLs
    cleaned = re.sub(r"\[SQL:.*?\]", "", msg, flags=re.DOTALL)
    cleaned = re.sub(r"\[parameters:.*?\]", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\(Background on this error at:.*?\)", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\(pymysql\.err\.\w+\)", "", cleaned)
    cleaned = re.sub(r"\(psycopg2\.\w+\)", "", cleaned)
    cleaned = re.sub(r"\(sqlite3\.\w+\)", "", cleaned)
    cleaned = re.sub(r"^\s*\(?\d+,\s*\"?", "", cleaned)
    cleaned = cleaned.rstrip(')" \t\n')
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()

    return cleaned if cleaned else "Terjadi kesalahan pada eksekusi pipeline."
