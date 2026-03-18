"""
Metrology Pro — Pydantic schemas
Modelos de validación para la API REST.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class AxisEnum(str, Enum):
    X = "X"
    Y = "Y"
    Z = "Z"


class DirectionEnum(str, Enum):
    forward = "forward"
    backward = "backward"


# ── Calibration session ──────────────────────────────────────────────

class CalibrationCreate(BaseModel):
    machine: str = Field(..., min_length=1, max_length=120, examples=["CMM Zeiss Contura"])
    operator: str = Field(..., min_length=1, max_length=120, examples=["J. García"])
    temperature: Optional[float] = Field(20.0, ge=-10, le=60, description="Temp. ambiente °C")
    humidity: Optional[float] = Field(50.0, ge=0, le=100, description="Humedad relativa %")
    standard_used: Optional[str] = Field(None, max_length=200, description="Patrón utilizado")
    mpe: Optional[float] = Field(None, ge=0, description="MPE según fabricante (µm)")
    notes: Optional[str] = Field(None, max_length=500)


class CalibrationOut(BaseModel):
    id: int
    machine: str
    operator: str
    temperature: float
    humidity: float
    standard_used: Optional[str]
    mpe: Optional[float]
    notes: Optional[str]
    created_at: str
    status: str


# ── Measurement points ───────────────────────────────────────────────

class MeasurementPoint(BaseModel):
    nominal: float
    measured: float
    axis: AxisEnum = AxisEnum.X
    direction: DirectionEnum = DirectionEnum.forward
    run: int = Field(1, ge=1, description="Número de ciclo/repetición")


class PointOut(BaseModel):
    id: int
    calibration_id: int
    nominal: float
    measured: float
    error: float
    axis: str
    direction: str
    run: int


# ── ISO report ───────────────────────────────────────────────────────

class AxisReport(BaseModel):
    axis: str
    n_points: int
    nominal_range_mm: float
    errors_um: List[float]
    mean_error_um: float
    std_error_um: float
    max_error_um: float
    min_error_um: float
    range_error_um: float
    repeatability_um: float
    systematic_error_um: float
    expanded_uncertainty_um: float
    hysteresis_um: Optional[float] = None
    mpe_um: Optional[float] = None
    mpe_pass: Optional[bool] = None
    iso_euni: float = Field(description="E_UNI,MPE ISO 10360-2 span")


class CalibrationReport(BaseModel):
    calibration: CalibrationOut
    axes: List[AxisReport]
    overall_pass: Optional[bool] = None
    iso_standard: str = "ISO 10360-2:2009 / VDI/VDE 2617"


# ── Drift ────────────────────────────────────────────────────────────

class DriftPoint(BaseModel):
    calibration_id: int
    date: str
    machine: str
    axis: str
    E_span_um: float
    mean_error_um: float


# ── Generic responses ────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class UploadResponse(BaseModel):
    calibration_id: int
    points_inserted: int
    axes_detected: List[str]
    message: str
