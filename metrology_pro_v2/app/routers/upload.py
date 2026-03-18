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

from app.db import get_db
from app.models import MeasurementPoint, PointOut, UploadResponse

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
    # Verificar calibración
    cal = db.execute("SELECT id, status FROM calibrations WHERE id=?", (cal_id,)).fetchone()
    if not cal:
        raise HTTPException(404, "Calibración no encontrada")

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
    for i, raw_row in enumerate(reader, start=2):
        row = _validate_csv_row(raw_row, i)
        error = row["measured"] - row["nominal"]
        db.execute(
            """INSERT INTO measurement_points
               (calibration_id, nominal, measured, error, axis, direction, run)
               VALUES (?,?,?,?,?,?,?)""",
            (cal_id, row["nominal"], row["measured"], error, row["axis"], row["direction"], row["run"]),
        )
        count += 1
        axes_found.add(row["axis"])

    if count == 0:
        raise HTTPException(400, "El CSV no contiene filas válidas.")

    db.commit()
    return UploadResponse(
        calibration_id=cal_id,
        points_inserted=count,
        axes_detected=sorted(axes_found),
        message=f"{count} puntos insertados correctamente.",
    )


@router.get("/{cal_id}", response_model=list[PointOut])
def get_points(cal_id: int, axis: str = Query(None), db: sqlite3.Connection = Depends(get_db)):
    sql = "SELECT * FROM measurement_points WHERE calibration_id=?"
    params: list = [cal_id]
    if axis:
        sql += " AND axis=?"
        params.append(axis.upper())
    sql += " ORDER BY run, nominal"
    rows = db.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


@router.delete("/{cal_id}")
def delete_points(cal_id: int, db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM measurement_points WHERE calibration_id=?", (cal_id,))
    db.commit()
    return {"message": "Puntos eliminados", "calibration_id": cal_id}
