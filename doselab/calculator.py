"""Core dose → volume → bottles calculation (functions)."""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from .catalog import AGE_TABLE_DRUGS, get_drug
from .checks import REGISTRY
from .checks.base import fmt
from .models import DoseMode, DoseResult, Patient, Prescription

INTERVAL = {1: "q24h", 2: "q12h", 3: "q8h", 4: "q6h", 6: "q4h"}


def round_to(value: float, step: Optional[float]) -> float:
    """Round a volume to the nearest measurable step (None = no rounding)."""
    if not step:
        return value
    steps = (Decimal(repr(value)) / Decimal(repr(step))).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return float(steps * Decimal(repr(step)))


def dose_to_mg_and_ml(rx: Prescription, weight: Optional[float]) -> tuple[float, float, str]:
    """Return (mg per dose, exact mL per dose, mg basis label)."""
    s, d, f = rx.strength, rx.dose, rx.frequency
    is_aug = rx.drug_id == "augmentin"
    needs_weight = rx.mode in (DoseMode.MG_KG_DOSE, DoseMode.MG_KG_DAY)
    if needs_weight and not weight:
        raise ValueError("Weight is required for a mg/kg dose.")

    if rx.mode is DoseMode.ML_PER_DOSE:
        return d * s.mg / s.vol, d, "total product"
    if rx.mode is DoseMode.MG_PER_DOSE:
        mg = d
    elif rx.mode is DoseMode.MG_KG_DOSE:
        mg = d * weight
    else:
        mg = d * weight / f
    # Augmentin mg/kg doses (and "amoxicillin" basis) are on the amoxicillin component
    if is_aug and (needs_weight or rx.augmentin_basis == "amoxicillin"):
        return mg, mg * s.vol / s.amox_mg, "amoxicillin"
    return mg, mg * s.vol / s.mg, "total product"


def build_formula(r: DoseResult) -> list[str]:
    rx, s, w = r.prescription, r.strength, r.patient.weight_kg
    lines: list[str] = []
    if rx.mode is DoseMode.MG_KG_DAY:
        total = rx.dose * w
        lines += [f"Total daily dose = {fmt(w)} kg × {fmt(rx.dose)} mg/kg/day = {fmt(total, 3)} mg/day",
                  f"Dose per administration = {fmt(total, 3)} mg/day ÷ {fmt(rx.frequency)} = {fmt(r.mg_per_dose, 3)} mg per dose"
                  + (f" ({INTERVAL[rx.frequency]})" if rx.frequency in INTERVAL else "")]
        lines.append(f"Volume per dose = {fmt(r.mg_per_dose, 3)} mg ÷ {fmt(s.mg_per_ml, 3)} mg/mL = {fmt(r.ml_per_dose)} mL per dose"
                     + (f" (exact {fmt(r.exact_ml, 3)} mL)" if abs(r.ml_per_dose - r.exact_ml) > 1e-9 else ""))
    else:
        if rx.mode is DoseMode.MG_KG_DOSE:
            lines.append(f"{fmt(rx.dose)} mg/kg × {fmt(w)} kg = {fmt(r.mg_per_dose, 3)} mg per dose")
        if rx.mode is DoseMode.ML_PER_DOSE:
            lines.append(f"{fmt(rx.dose)} mL × {fmt(s.mg)} ÷ {fmt(s.vol)} = {fmt(r.mg_per_dose, 3)} mg per dose")
        else:
            lines.append(f"{fmt(r.mg_per_dose)} mg × {fmt(s.vol)} mL ÷ {fmt(s.mg)} mg = {fmt(r.exact_ml, 3)} mL per dose")
    lines.append(f"{fmt(r.ml_per_dose)} mL × {fmt(rx.frequency)} × {fmt(rx.duration_days)} = {fmt(r.total_ml)} mL course total")
    lines.append(f"{fmt(r.total_ml)} ÷ {fmt(s.bottle)} = {fmt(r.total_ml / s.bottle)} → {r.bottles} bottle(s) by volume")
    return lines


def calculate(rx: Prescription, patient: Optional[Patient] = None) -> DoseResult:
    """Run the full calculation and the drug-specific check, if any."""
    patient = patient or Patient()
    drug = get_drug(rx.drug_id)
    s = rx.strength
    checker = REGISTRY.get(rx.drug_id)

    mg, exact_ml, _basis = dose_to_mg_and_ml(rx, patient.weight_kg)
    ml = round_to(exact_ml, rx.rounding)
    daily_ml = ml * rx.frequency
    total_ml = daily_ml * rx.duration_days
    r = DoseResult(drug, s, rx, patient, mg, exact_ml, ml, daily_ml, total_ml,
                   bottles=math.ceil(total_ml / s.bottle - 1e-9))

    if checker:
        checker.validate(r)
    r.formula = build_formula(r)

    # general warnings
    if s.shelf_days and rx.duration_days > s.shelf_days:
        r.warnings.append(f"The {fmt(rx.duration_days)}-day course exceeds the in-use shelf life ({s.shelf_days} days); "
                          "bottles prepared the same day expire together.")
    if exact_ml > s.bottle:
        r.warnings.append("A single dose is larger than the bottle; review the inputs.")
    if exact_ml and abs(ml - exact_ml) / exact_ml > 0.1:
        r.warnings.append(f"Rounding changed the dose by more than 10%; exact value {fmt(exact_ml, 3)} mL.")
    if rx.drug_id in AGE_TABLE_DRUGS and rx.mode in (DoseMode.MG_KG_DOSE, DoseMode.MG_KG_DAY):
        r.warnings.append("This drug is usually dosed by age and the product table; confirm the mg/kg dose source.")

    if checker:
        r.check = checker.check(r)
    return r
