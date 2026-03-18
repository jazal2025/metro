"""
Metrology Pro — Database layer
SQLite con gestión de conexiones vía FastAPI Depends.
"""

import sqlite3
import os
from pathlib import Path
from typing import Generator

DB_DIR = Path(os.environ.get("METROLOGY_DB_DIR", "."))
DB_PATH = DB_DIR / "metrology_pro.db"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS calibrations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    machine         TEXT    NOT NULL,
    operator        TEXT    NOT NULL,
    temperature     REAL    DEFAULT 20.0,
    humidity        REAL    DEFAULT 50.0,
    standard_used   TEXT,
    mpe             REAL,
    notes           TEXT,
    created_at      TEXT    NOT NULL,
    status          TEXT    DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS measurement_points (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    calibration_id  INTEGER NOT NULL,
    nominal         REAL    NOT NULL,
    measured        REAL    NOT NULL,
    error           REAL    NOT NULL,
    axis            TEXT    NOT NULL DEFAULT 'X',
    direction       TEXT    NOT NULL DEFAULT 'forward',
    run             INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (calibration_id) REFERENCES calibrations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    calibration_id  INTEGER NOT NULL,
    generated_at    TEXT    NOT NULL,
    report_json     TEXT    NOT NULL,
    FOREIGN KEY (calibration_id) REFERENCES calibrations(id) ON DELETE CASCADE
);
"""


def init_db() -> None:
    """Crea las tablas si no existen."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(SCHEMA)
    conn.close()


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Dependency de FastAPI — abre y cierra conexión de forma segura."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()
