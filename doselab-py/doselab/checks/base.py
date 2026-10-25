# Dose Lab by WaadAlwagdani
# © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com
# All rights reserved. Not to be copied, reused or redistributed without written permission.

"""Abstract base class and registry for drug-specific dose checks (OOP: inheritance, polymorphism)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

from ..models import CheckResult, Status

if TYPE_CHECKING:
    from ..models import DoseResult

REGISTRY: dict[str, "DoseChecker"] = {}


def register(drug_id: str) -> Callable[[type], type]:
    """Class decorator: registers a checker instance for a drug id."""
    def wrap(cls: type) -> type:
        REGISTRY[drug_id] = cls()
        return cls
    return wrap


def fmt(v: float, d: int = 2) -> str:
    """Format like the web tool: up to d decimals, thousands separator."""
    return f"{round(v, d):,.{d}f}".rstrip("0").rstrip(".")


class DoseChecker(ABC):
    """Every drug check needs weight and age, then runs its own rules."""
    name = "drug"
    needs_weight = True
    needs_age = True

    def validate(self, r: "DoseResult") -> None:
        if self.needs_weight and not r.patient.weight_kg:
            raise ValueError(f"Weight is required to check the {self.name} dose.")
        if self.needs_age and not r.patient.age_days:
            raise ValueError(f"Age is required to check the {self.name} dose.")

    @abstractmethod
    def check(self, r: "DoseResult") -> CheckResult:
        """Return the check and append warnings to r.warnings."""

    # shared helpers
    @staticmethod
    def doses_word(f: float) -> str:
        return "one dose" if f == 1 else "two doses" if f == 2 else f"{fmt(f)} doses"

    @staticmethod
    def ml(r: "DoseResult", mg: float) -> float:
        return mg * r.strength.vol / r.strength.mg

    @staticmethod
    def status_range(v: float, lo: float, hi: float) -> Status:
        return Status.LOW if v < lo - 1e-9 else Status.HIGH if v > hi + 1e-9 else Status.OK

    @staticmethod
    def status_target(v: float, target: float, tol: float = 0.05) -> Status:
        return DoseChecker.status_range(v, target * (1 - tol), target * (1 + tol))
