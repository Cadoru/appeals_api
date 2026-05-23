#!/usr/bin/env python3
"""Создаёт пустую БД из init-скриптов (без seed)."""
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "anonymous_feedback.db"
INIT_DIR = ROOT / "init"


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        for script in sorted(INIT_DIR.glob("*.sql")):
            sql = script.read_text(encoding="utf-8")
            conn.executescript(sql)
            print(f"Applied: {script.name}")
        conn.commit()
    finally:
        conn.close()

    print(f"Database created: {DB_PATH}")


if __name__ == "__main__":
    main()
