"""
Router: Generación de informes ISO 10360-2.
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import sqlite3
import json

from app.db import get_db
from app.iso import full_axis_analysis
from app.models import CalibrationReport, CalibrationOut, AxisReport

router = APIRouter(prefix="/api/report", tags=["Report"])


@router.post("/{cal_id}", response_model=CalibrationReport)
def generate_report(cal_id: int, db: sqlite3.Connection = Depends(get_db)):
    # Obtener calibración
    cal_row = db.execute("SELECT * FROM calibrations WHERE id=?", (cal_id,)).fetchone()
    if not cal_row:
        raise HTTPException(404, "Calibración no encontrada")
    cal = dict(cal_row)
    mpe = cal.get("mpe")

    # Obtener puntos
    points = db.execute(
        "SELECT * FROM measurement_points WHERE calibration_id=? ORDER BY axis, run, nominal",
        (cal_id,),
    ).fetchall()
    if not points:
        raise HTTPException(400, "No hay puntos de medición para esta calibración.")

    points_list = [dict(p) for p in points]

    # Agrupar por eje
    axes = sorted(set(p["axis"] for p in points_list))
    axis_reports = []
    all_pass = True

    for ax in axes:
        ax_points = [p for p in points_list if p["axis"] == ax]
        result = full_axis_analysis(ax_points, mpe=mpe)
        if not result:
            continue
        report = AxisReport(axis=ax, **result)
        axis_reports.append(report)
        if report.mpe_pass is False:
            all_pass = False

    overall_pass = all_pass if mpe else None

    # Actualizar estado
    new_status = "pass" if overall_pass else ("fail" if overall_pass is False else "reported")
    db.execute("UPDATE calibrations SET status=? WHERE id=?", (new_status, cal_id))

    # Guardar snapshot
    report_out = CalibrationReport(
        calibration=CalibrationOut(**cal, status=new_status),
        axes=axis_reports,
        overall_pass=overall_pass,
    )
    db.execute(
        "INSERT INTO report_snapshots (calibration_id, generated_at, report_json) VALUES (?,?,?)",
        (cal_id, datetime.now().isoformat(timespec="seconds"), report_out.model_dump_json()),
    )
    db.commit()

    return report_out


@router.get("/{cal_id}", response_model=CalibrationReport)
def get_latest_report(cal_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute(
        "SELECT report_json FROM report_snapshots WHERE calibration_id=? ORDER BY generated_at DESC LIMIT 1",
        (cal_id,),
    ).fetchone()
    if not row:
        raise HTTPException(404, "No hay informe generado para esta calibración.")
    return json.loads(row["report_json"])
