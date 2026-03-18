"""
Router: Generación de informes ISO 10360-2.
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import sqlite3
import json
import logging

from app.db import get_db
from app.iso import full_axis_analysis
from app.models import CalibrationReport, CalibrationOut, AxisReport

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/report", tags=["Report"])


@router.post("/{cal_id}", response_model=CalibrationReport)
def generate_report(cal_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Genera informe ISO 10360-2 para una calibración."""
    try:
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
            try:
                result = full_axis_analysis(ax_points, mpe=mpe)
                if not result:
                    logger.warning(f"No analysis result for axis {ax} in calibration {cal_id}")
                    continue
                report = AxisReport(axis=ax, **result)
                axis_reports.append(report)
                if report.mpe_pass is False:
                    all_pass = False
            except Exception as e:
                logger.error(f"Error analyzing axis {ax}: {str(e)}")
                raise HTTPException(
                    500, 
                    f"Error al analizar eje {ax}: {str(e)}"
                )

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
            (cal_id, datetime.utcnow().isoformat(timespec="seconds"), report_out.model_dump_json()),
        )
        db.commit()
        
        logger.info(f"Report generated for calibration {cal_id}: status={new_status}")

        return report_out
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating report: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Error inesperado: {str(e)}")


@router.get("/{cal_id}", response_model=CalibrationReport)
def get_latest_report(cal_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Obtiene el último informe generado."""
    try:
        row = db.execute(
            "SELECT report_json FROM report_snapshots WHERE calibration_id=? ORDER BY generated_at DESC LIMIT 1",
            (cal_id,),
        ).fetchone()
        if not row:
            raise HTTPException(404, "No hay informe generado para esta calibración.")
        return json.loads(row["report_json"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report: {str(e)}")
        raise HTTPException(500, f"Error al recuperar informe: {str(e)}")
