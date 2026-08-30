from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import DB_PATH, SCHEMA_PATH


def init_db(db_path: Path = DB_PATH, schema_path: Path = SCHEMA_PATH) -> None:
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    ddl: str = schema_path.read_text(encoding="utf-8")
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(ddl)
        conn.commit()
        print(f"Initialized SQLite DB at: {db_path}")
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables: {tables}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
