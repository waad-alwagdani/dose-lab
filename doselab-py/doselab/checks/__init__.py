# Dose Lab by WaadAlwagdani
# © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com
# All rights reserved. Not to be copied, reused or redistributed without written permission.

"""Drug-specific dose checks. Importing this package registers every checker."""

from . import augmentin, azithromycin, cefuroxime, depakine, ibuprofen, levetiracetam, paracetamol  # noqa: F401
from .base import REGISTRY, DoseChecker

__all__ = ["REGISTRY", "DoseChecker"]
