"""
Router: Carga de puntos de medición vía CSV o JSON.

Formato CSV esperado (cabeceras obligatorias: nominal, measured):
  nominal,measured,axis,direction,run
  0,0.0012,X,forward,1
  50,50.0034,X,forward,1
  ...
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from io import StringIO
import csv
import sqlite3
import logging

from app.db import get_db
from app.models import MeasurementPoint, PointOut, UploadResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/points", tags=["Measurement Points"])

def _validate_csv_row(row: dict, idx: int) -> dict:
    """Valida y normaliza una fila del CSV."""
    errors = []
    if "nominal" not in row or "measured" not in row:
        raise HTTPException(400, f"Fila {idx}: faltan columnas 'nominal' y/o 'measured'.")
    try:
        nominal = float(row["nominal"])
    except (ValueError, TypeError):
        errors.append(f"Fila {idx}: 'nominal' no es numérico ({row['nominal']})")
    try:
        measured = float(row["measured"])
    except (ValueError, TypeError):
        errors.append(f"Fila {idx}: 'measured' no es numérico ({row['measured']})")
    if errors:
        raise HTTPException(400, detail="; ".join(errors))

    axis = row.get("axis", "X").strip().upper()
    if axis not in ("X", "Y", "Z"):
        axis = "X"

    direction = row.get("direction", "forward").strip().lower()
    if direction not in ("forward", "backward"):
        direction = "forward"

    run = 1
    if "run" in row:
        try:
            run = int(row["run"])
        except ValueError:
            run = 1

    return {
        "nominal": nominal,
        "measured": measured,
        "axis": axis,
        "direction": direction,
        "run": max(1, run),
    }


@router.post("/upload-csv/{cal_id}", response_model=UploadResponse)
async def upload_csv(
    cal_id: int,
    file: UploadFile = File(...),
    db: sqlite3.Connection = Depends(get_db),
):
    """Carga puntos de medición desde un archivo CSV con validación y manejo de transacciones."""
    
    try:
        # Verificar calibración existe y está abierta
        cal = db.execute(
            "SELECT id, status FROM calibrations WHERE id=?", (cal_id,)
        ).fetchone()
        if not cal:
            raise HTTPException(404, "Calibración no encontrada")
        
        if cal["status"] != "open":
            raise HTTPException(
                400, 
                f"Calibración en estado '{cal['status']}'. Solo se pueden cargar datos en calibraciones 'open'."
            )

        # Validar tipo de archivo
        if file.filename and not file.filename.lower().endswith(".csv"):
            raise HTTPException(400, "Solo se aceptan archivos .csv")

        content = await file.read()
        try:
            text = content.decode("utf-8-sig")  # Soporte BOM de Excel
        except UnicodeDecodeError:
            try:
                text = content.decode("latin-1")
            except Exception:
                raise HTTPException(400, "No se pudo decodificar el archivo.")

        # Detectar delimitador
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(text[:2048])
        except csv.Error:
            dialect = None

        reader = csv.DictReader(StringIO(text), dialect=dialect) if dialect else csv.DictReader(StringIO(text))

        count = 0
        axes_found = set()
        rows_to_insert = []

        # Validar todas las filas primero (no insertar parcialmente)
        for i, raw_row in enumerate(reader, start=2):
            row = _validate_csv_row(raw_row, i)
            rows_to_insert.append(row)
            axes_found.add(row["axis"])

        if count == 0 and not rows_to_insert:
            raise HTTPException(400, "El CSV no contiene filas válidas.")

        # Insertar con transacción explícita
        try:
            db.execute("BEGIN TRANSACTION")
            for row in rows_to_insert:
                db.execute(
                    """INSERT INTO measurement_points
                       (calibration_id, nominal, measured, axis, direction, run)
                       VALUES (?,?,?,?,?,?)""",
                    (cal_id, row["nominal"], row["measured"], row["axis"], row["direction"], row["run"]),
                )
                count += 1
            
            db.commit()
            logger.info(f"Uploaded {count} points for calibration {cal_id}")
            
        except sqlite3.Error as e:
            db.rollback()
            logger.error(f"Database error during upload: {str(e)}")
            raise HTTPException(
                500, 
                f"Error al insertar puntos en la base de datos: {str(e)}"
            )

        return UploadResponse(
            calibration_id=cal_id,
            points_inserted=count,
            axes_detected=sorted(axes_found),
            message=f"{count} puntos insertados correctamente.",
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during CSV upload: {str(e)}")
        raise HTTPException(500, f"Error inesperado: {str(e)}")


@router.get("/{cal_id}", response_model=list[PointOut])
def get_points(cal_id: int, axis: str = Query(None), db: sqlite3.Connection = Depends(get_db)):
    """Obtiene puntos de medición de una calibración."""
    sql = "SELECT id, calibration_id, nominal, measured, (measured - nominal) * 1000.0 as error, axis, direction, run FROM measurement_points WHERE calibration_id=?"
    params: list = [cal_id]
    if axis:
        sql += " AND axis=?"
        params.append(axis.upper())
    sql += " ORDER BY run, nominal"
    rows = db.execute(sql, params).fetchall()
    return [dict(r) for r in rows]

@router.delete("/{cal_id}")
def delete_points(cal_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Elimina todos los puntos de una calibración."""
    try:
        db.execute("BEGIN TRANSACTION")
        db.execute("DELETE FROM measurement_points WHERE calibration_id=?", (cal_id,))
        db.commit()
        logger.info(f"Deleted all points for calibration {cal_id}")
        return {"message": "Puntos eliminados", "calibration_id": cal_id}
    except sqlite3.Error as e:
        db.rollback()
        logger.error(f"Error deleting points: {str(e)}")
        raise HTTPException(500, f"Error al eliminar puntos: {str(e)}")