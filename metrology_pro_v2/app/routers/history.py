"""
Router: Historial de calibraciones.
"""

from fastapi import APIRouter, Depends, Query
import sqlite3

from app.db import get_db
from app.models import CalibrationOut

router = APIRouter(prefix="/api/history", tags=["History"])


@router.get("/", response_model=list[CalibrationOut])
def history(
    machine: str = Query(None),
    status: str = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: sqlite3.Connection = Depends(get_db),
):
    sql = "SELECT * FROM calibrations WHERE 1=1"
    params: list = []
    if machine:
        sql += " AND machine LIKE ?"
        params.append(f"%{machine}%")
    if status:
        sql += " AND status=?"
        params.append(status)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = db.execute(sql, params).fetchall()
    return [dict(r) for r in rows]
