"""
Router: Gestión de sesiones de calibración.
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import sqlite3
import logging

from app.db import get_db
from app.models import CalibrationCreate, CalibrationOut, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calibrations", tags=["Calibrations"])


@router.post("/", response_model=CalibrationOut, status_code=201)
def create_calibration(data: CalibrationCreate, db: sqlite3.Connection = Depends(get_db)):
    """Crea una nueva sesión de calibración."""
    try:
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
                datetime.utcnow().isoformat(timespec="seconds"),
                "open",
            ),
        )
        db.commit()
        row = db.execute("SELECT * FROM calibrations WHERE id=?", (cur.lastrowid,)).fetchone()
        logger.info(f"Created calibration {cur.lastrowid} for machine {data.machine}")
        return dict(row)
    except sqlite3.Error as e:
        db.rollback()
        logger.error(f"Error creating calibration: {str(e)}")
        raise HTTPException(500, f"Error al crear calibración: {str(e)}")


@router.get("/", response_model=list[CalibrationOut])
def list_calibrations(db: sqlite3.Connection = Depends(get_db)):
    """Lista todas las calibraciones."""
    try:
        rows = db.execute("SELECT * FROM calibrations ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as e:
        logger.error(f"Error listing calibrations: {str(e)}")
        raise HTTPException(500, f"Error al listar calibraciones: {str(e)}")


@router.get("/{cal_id}", response_model=CalibrationOut)
def get_calibration(cal_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Obtiene una calibración específica."""
    try:
        row = db.execute("SELECT * FROM calibrations WHERE id=?", (cal_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Calibración no encontrada")
        return dict(row)
    except HTTPException:
        raise
    except sqlite3.Error as e:
        logger.error(f"Error getting calibration {cal_id}: {str(e)}")
        raise HTTPException(500, f"Error al obtener calibración: {str(e)}")


@router.delete("/{cal_id}", response_model=MessageResponse)
def delete_calibration(cal_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Elimina una calibración y todos sus datos asociados."""
    try:
        row = db.execute("SELECT id FROM calibrations WHERE id=?", (cal_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Calibración no encontrada")
        
        db.execute("BEGIN TRANSACTION")
        db.execute("DELETE FROM measurement_points WHERE calibration_id=?", (cal_id,))
        db.execute("DELETE FROM report_snapshots WHERE calibration_id=?", (cal_id,))
        db.execute("DELETE FROM calibrations WHERE id=?", (cal_id,))
        db.commit()
        
        logger.info(f"Deleted calibration {cal_id}")
        return {"message": "Calibración eliminada", "detail": f"ID {cal_id}"}
    
    except HTTPException:
        raise
    except sqlite3.Error as e:
        db.rollback()
        logger.error(f"Error deleting calibration {cal_id}: {str(e)}")
        raise HTTPException(500, f"Error al eliminar calibración: {str(e)}")
