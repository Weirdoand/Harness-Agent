# -*- coding: utf-8 -*-
"""Database helpers for the Notes API.

Keeps connection setup in one place so every caller gets:
  * SQLite's foreign-key enforcement turned on, and
  * row access by column name (``sqlite3.Row``).
"""
from __future__ import annotations

import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(HERE, "schema.sql")
DEFAULT_DB_PATH = os.path.join(HERE, "notes.db")


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
	"""Open a connection with the settings this schema requires."""
	conn = sqlite3.connect(db_path)
	conn.row_factory = sqlite3.Row
	conn.execute("PRAGMA foreign_keys = ON")
	return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
	"""Apply ``schema.sql`` and return a ready-to-use connection."""
	with open(SCHEMA_PATH, encoding="utf-8") as f:
		schema_sql = f.read()

	conn = get_connection(db_path)
	with conn:
		conn.executescript(schema_sql)
	return conn


def reset_db(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
	"""Drop every table, then re-apply the schema (handy for tests)."""
	if os.path.exists(db_path) and db_path != ":memory:":
		os.remove(db_path)
	return init_db(db_path)


if __name__ == "__main__":
	connection = reset_db()
	tables = [r["name"] for r in connection.execute(
		"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
	print("database ready:", DEFAULT_DB_PATH)
	print("tables:", tables)
