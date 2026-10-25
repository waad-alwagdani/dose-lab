# Dose Lab by WaadAlwagdani
# © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com
# All rights reserved. Not to be copied, reused or redistributed without written permission.

"""Dose Lab — oral suspension dispensing calculator.

Converts a prescribed dose into millilitres, counts bottles, and checks
pediatric doses for seven drugs against built-in references.

Author: Waad Alwagdani, PharmD — © 2026. All rights reserved.
"""

from .models import Patient, Prescription, Strength, Drug, DoseResult, CheckResult
from .catalog import CATALOG, get_drug
from .calculator import calculate

__version__ = "1.0.0"
__author__ = "WaadAlwagdani (Waad Alwagdani, PharmD)"
__copyright__ = "© 2026 Waad Alwagdani. All rights reserved."
SIGNATURE = "Dose Lab by WaadAlwagdani"
__all__ = ["Patient", "Prescription", "Strength", "Drug", "DoseResult",
           "CheckResult", "CATALOG", "get_drug", "calculate"]
