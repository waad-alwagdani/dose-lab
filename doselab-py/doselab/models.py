# Dose Lab by WaadAlwagdani
# © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com
# All rights reserved. Not to be copied, reused or redistributed without written permission.

"""Data models (OOP): dataclasses, properties, an Enum and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DoseMode(str, Enum):
    """How the prescriber wrote the dose."""
    MG_PER_DOSE = "direct"
    ML_PER_DOSE = "directMl"
    MG_KG_DOSE = "kgDose"
    MG_KG_DAY = "kgDay"


class Status(str, Enum):
    OK = "ok"
    LOW = "low"
    HIGH = "high"


@dataclass(frozen=True)
class Strength:
    """One product strength, e.g. 250 mg per 5 mL in a 100 mL bottle."""
    mg: float
    vol: float
    bottle: float
    shelf_days: Optional[int] = None
    amox_mg: Optional[float] = None     # Augmentin only
    clav_mg: Optional[float] = None     # Augmentin only
    label: Optional[str] = None
    custom: bool = False

    @property
    def mg_per_ml(self) -> float:
        return self.mg / self.vol

    @property
    def ratio(self) -> Optional[float]:
        if self.amox_mg and self.clav_mg:
            return round(self.amox_mg / self.clav_mg, 1)
        return None

    def describe(self) -> str:
        if self.label:
            return self.label
        vol = "" if self.vol == 1 else f"{self.vol:g} "
        return f"{self.mg:g} mg/{vol}mL"


@dataclass
class Drug:
    id: str
    name: str
    strengths: list[Strength] = field(default_factory=list)

    def __str__(self) -> str:
        return self.name


@dataclass
class Patient:
    weight_kg: Optional[float] = None
    age: Optional[float] = None
    age_unit: str = "years"             # "years" | "months" | "days"

    _DAYS = {"years": 365.25, "months": 30.44, "days": 1.0}

    def __post_init__(self) -> None:
        if self.age_unit not in self._DAYS:
            raise ValueError(f"age_unit must be one of {list(self._DAYS)}")
        if self.weight_kg is not None and self.weight_kg <= 0:
            raise ValueError("weight must be positive")

    @property
    def age_days(self) -> Optional[float]:
        if not self.age or self.age <= 0:
            return None
        return self.age * self._DAYS[self.age_unit]


@dataclass
class Prescription:
    drug_id: str
    strength: Strength
    dose: float
    mode: DoseMode = DoseMode.MG_PER_DOSE
    frequency: float = 3                # doses per day
    duration_days: float = 1
    rounding: Optional[float] = 0.1     # None = no rounding
    # drug-specific options
    augmentin_basis: str = "total"      # "total" | "amoxicillin"
    augmentin_reference: str = "auto"   # auto | q8 | q12 | high | infant
    azithro_regimen: str = "d3"         # d3 | d5 | strep | single
    azithro_day: str = "1"              # "1" | "2" (for d5)
    cef_regimen: str = "aom"            # aom | phar

    def __post_init__(self) -> None:
        if self.dose <= 0:
            raise ValueError("Enter the dose.")
        if self.frequency <= 0:
            raise ValueError("Enter the frequency.")
        if self.duration_days <= 0:
            raise ValueError("Enter the treatment duration.")
        self.mode = DoseMode(self.mode)


@dataclass
class CheckResult:
    status: Status
    title: str
    lines: list[str] = field(default_factory=list)
    gauge: Optional[tuple[float, float, float, str]] = None  # value, lo, hi, unit


@dataclass
class DoseResult:
    drug: Drug
    strength: Strength
    prescription: Prescription
    patient: Patient
    mg_per_dose: float
    exact_ml: float
    ml_per_dose: float
    daily_ml: float
    total_ml: float
    bottles: int
    formula: list[str] = field(default_factory=list)
    check: Optional[CheckResult] = None
    warnings: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    @property
    def dispensed_ml(self) -> float:
        return self.bottles * self.strength.bottle
