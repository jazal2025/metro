"""
Router: Gestión de sesiones de calibración.
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import sqlite3

from app.db import get_db
from app.models import CalibrationCreate, CalibrationOut, MessageResponse

router = APIRouter(prefix="/api/calibrations", tags=["Calibrations"])


@router.post("/", response_model=CalibrationOut, status_code=201)
def create_calibration(data: CalibrationCreate, db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute(
        """INSERT INTO calibrations
           (machine, operator, temperature, humidity, standard_used, mpe, notes, created_at, status)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            data.machine,
            data.operator,
            data.temperature,
            data.humidity,
            data.standard_used,
            data.mpe,
            data.notes,
            datetime.now().isoformat(timespec="seconds"),
            "open",
        ),
    )
    db.commit()
    row = db.execute("SELECT * FROM calibrations WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row)


@router.get("/", response_model=list[CalibrationOut])
def list_calibrations(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM calibrations ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


@router.get("/{cal_id}", response_model=CalibrationOut)
def get_calibration(cal_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT * FROM calibrations WHERE id=?", (cal_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Calibración no encontrada")
    return dict(row)


@router.delete("/{cal_id}", response_model=MessageResponse)
def delete_calibration(cal_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT id FROM calibrations WHERE id=?", (cal_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Calibración no encontrada")
    db.execute("DELETE FROM measurement_points WHERE calibration_id=?", (cal_id,))
    db.execute("DELETE FROM report_snapshots WHERE calibration_id=?", (cal_id,))
    db.execute("DELETE FROM calibrations WHERE id=?", (cal_id,))
    db.commit()
    return {"message": "Calibración eliminada", "detail": f"ID {cal_id}"}
