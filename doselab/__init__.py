"""Dose Lab — oral suspension dispensing calculator.

Converts a prescribed dose into millilitres, counts bottles, and checks
pediatric doses for seven drugs against built-in references.

Author: Waad Alwagdani, PharmD — © 2026. All rights reserved.
"""

from .models import Patient, Prescription, Strength, Drug, DoseResult, CheckResult
from .catalog import CATALOG, get_drug
from .calculator import calculate

__version__ = "1.0.0"
__all__ = ["Patient", "Prescription", "Strength", "Drug", "DoseResult",
           "CheckResult", "CATALOG", "get_drug", "calculate"]
