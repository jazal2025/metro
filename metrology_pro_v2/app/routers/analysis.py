"""
Router: Análisis de deriva (drift) entre calibraciones.
"""

from fastapi import APIRouter, Depends, Query
import sqlite3

from app.db import get_db
from app.models import DriftPoint
from app.iso import compute_errors, axis_statistics
import numpy as np

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.get("/drift", response_model=list[DriftPoint])
def drift(
    machine: str = Query(None),
    axis: str = Query(None),
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Devuelve la evolución del error (E_span y media) por calibración,
    opcionalmente filtrado por máquina y eje.
    """
    cals = db.execute(
        "SELECT * FROM calibrations ORDER BY created_at"
    ).fetchall()

    results = []
    for cal in cals:
        if machine and machine.lower() not in cal["machine"].lower():
            continue

        sql = "SELECT * FROM measurement_points WHERE calibration_id=?"
        params: list = [cal["id"]]
        if axis:
            sql += " AND axis=?"
            params.append(axis.upper())
        sql += " ORDER BY nominal"

        pts = db.execute(sql, params).fetchall()
        if not pts:
            continue

        # Agrupar por eje
        axes_in_pts = sorted(set(p["axis"] for p in pts))
        for ax in axes_in_pts:
            ax_pts = [p for p in pts if p["axis"] == ax]
            errors = compute_errors(
                [p["nominal"] for p in ax_pts],
                [p["measured"] for p in ax_pts],
            )
            stats = axis_statistics(errors)
            results.append(
                DriftPoint(
                    calibration_id=cal["id"],
                    date=cal["created_at"],
                    machine=cal["machine"],
                    axis=ax,
                    E_span_um=round(stats["range"], 3),
                    mean_error_um=round(stats["mean"], 3),
                )
            )

    return results
