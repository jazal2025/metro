"""
Metrology Pro — ISO Calculation Engine
Cálculos conformes a ISO 10360-2:2009 y VDI/VDE 2617.

Terminología:
  E_i         Error de indicación en el punto i  (measured − nominal)
  E_UNI       Rango de error unidireccional (span)
  E_BI        Rango de error bidireccional
  R           Repetibilidad (desviación estándar de errores)
  B           Error sistemático (media de errores)
  H           Histéresis (diferencia media forward − backward)
  U           Incertidumbre expandida (k=2, ~95 %)
  MPE         Error máximo permisible (del fabricante)
"""

from typing import List, Dict, Optional, Tuple
import numpy as np


def compute_errors(nominal: List[float], measured: List[float]) -> np.ndarray:
    """Calcula errores de indicación en µm."""
    nom = np.array(nominal)
    meas = np.array(measured)
    return (meas - nom) * 1000.0  # mm → µm


def axis_statistics(errors_um: np.ndarray) -> Dict:
    """Estadísticas básicas de un vector de errores (µm)."""
    return {
        "mean": float(np.mean(errors_um)),
        "std": float(np.std(errors_um, ddof=1)) if len(errors_um) > 1 else 0.0,
        "max": float(np.max(errors_um)),
        "min": float(np.min(errors_um)),
        "range": float(np.ptp(errors_um)),
        "n": len(errors_um),
    }


def compute_repeatability(errors_per_run: List[np.ndarray]) -> float:
    """
    Repetibilidad ISO: desviación estándar agrupada de las repeticiones
    en cada punto nominal.  Si solo hay un ciclo devuelve la std global.
    """
    if len(errors_per_run) <= 1:
        all_e = np.concatenate(errors_per_run) if errors_per_run else np.array([0.0])
        return float(np.std(all_e, ddof=1)) if len(all_e) > 1 else 0.0

    # Pooled std por punto nominal
    pooled_vars = []
    n_runs = len(errors_per_run)
    min_len = min(len(r) for r in errors_per_run)
    for i in range(min_len):
        vals = np.array([run[i] for run in errors_per_run])
        if len(vals) > 1:
            pooled_vars.append(float(np.var(vals, ddof=1)))
    if not pooled_vars:
        return 0.0
    return float(np.sqrt(np.mean(pooled_vars)))


def compute_hysteresis(
    fwd_nominal: List[float],
    fwd_measured: List[float],
    bwd_nominal: List[float],
    bwd_measured: List[float],
) -> Optional[float]:
    """
    Histéresis: diferencia media entre errores forward y backward
    en puntos nominales coincidentes (µm).
    """
    fwd_errors = dict(zip(fwd_nominal, compute_errors(fwd_nominal, fwd_measured)))
    bwd_errors = dict(zip(bwd_nominal, compute_errors(bwd_nominal, bwd_measured)))

    common = set(fwd_errors.keys()) & set(bwd_errors.keys())
    if not common:
        return None

    diffs = [abs(fwd_errors[n] - bwd_errors[n]) for n in sorted(common)]
    return float(np.mean(diffs))


def expanded_uncertainty(std_error: float, k: float = 2.0) -> float:
    """Incertidumbre expandida U = k · u  (simplificada GUM)."""
    return k * std_error


def check_mpe(e_span: float, mpe: Optional[float]) -> Optional[bool]:
    """Comprueba si el rango de error supera el MPE del fabricante."""
    if mpe is None or mpe <= 0:
        return None
    return e_span <= mpe


def full_axis_analysis(
    points: List[Dict],
    mpe: Optional[float] = None,
) -> Dict:
    """
    Análisis completo de un eje según ISO 10360-2.

    points: lista de dicts con keys {nominal, measured, direction, run}
    Todos los valores en mm.
    """
    if not points:
        return {}

    nominals = [p["nominal"] for p in points]
    measured = [p["measured"] for p in points]
    errors_um = compute_errors(nominals, measured)

    stats = axis_statistics(errors_um)

    # Separar por ciclo para repetibilidad
    runs = sorted(set(p["run"] for p in points))
    errors_by_run = []
    for r in runs:
        run_pts = [p for p in points if p["run"] == r]
        run_pts.sort(key=lambda p: p["nominal"])
        e = compute_errors(
            [p["nominal"] for p in run_pts],
            [p["measured"] for p in run_pts],
        )
        errors_by_run.append(e)

    rep = compute_repeatability(errors_by_run)

    # Histéresis (si hay datos bidireccionales)
    fwd = [p for p in points if p["direction"] == "forward"]
    bwd = [p for p in points if p["direction"] == "backward"]
    hyst = None
    if fwd and bwd:
        hyst = compute_hysteresis(
            [p["nominal"] for p in fwd],
            [p["measured"] for p in fwd],
            [p["nominal"] for p in bwd],
            [p["measured"] for p in bwd],
        )

    U = expanded_uncertainty(stats["std"])
    e_span = stats["range"]
    mpe_pass = check_mpe(e_span, mpe)

    nominal_range = max(nominals) - min(nominals) if nominals else 0.0

    return {
        "n_points": stats["n"],
        "nominal_range_mm": round(nominal_range, 4),
        "errors_um": [round(float(e), 3) for e in errors_um],
        "mean_error_um": round(stats["mean"], 3),
        "std_error_um": round(stats["std"], 3),
        "max_error_um": round(stats["max"], 3),
        "min_error_um": round(stats["min"], 3),
        "range_error_um": round(e_span, 3),
        "repeatability_um": round(rep, 3),
        "systematic_error_um": round(stats["mean"], 3),
        "expanded_uncertainty_um": round(U, 3),
        "hysteresis_um": round(hyst, 3) if hyst is not None else None,
        "mpe_um": round(mpe, 3) if mpe is not None else None,
        "mpe_pass": mpe_pass,
        "iso_euni": round(e_span, 3),
    }
