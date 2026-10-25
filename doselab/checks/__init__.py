"""Drug-specific dose checks. Importing this package registers every checker."""

from . import augmentin, azithromycin, cefuroxime, depakine, ibuprofen, levetiracetam, paracetamol  # noqa: F401
from .base import REGISTRY, DoseChecker

__all__ = ["REGISTRY", "DoseChecker"]
