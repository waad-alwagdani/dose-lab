# Dose Lab by WaadAlwagdani
# © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com
# All rights reserved. Not to be copied, reused or redistributed without written permission.

from ..models import CheckResult, Status
from .base import DoseChecker, fmt, register


@register("paracetamol")
class ParacetamolChecker(DoseChecker):
    name = "paracetamol"

    def check(self, r):
        w, f, mg = r.patient.weight_kg, r.prescription.frequency, r.mg_per_dose
        age_d, dur = r.patient.age_days, r.prescription.duration_days
        mgkg, daily_mg = mg / w, mg * f
        daily_kg = mgkg * f
        adult = age_d >= 4383 and w >= 50
        lo, hi = (500, 1000) if adult else (min(10 * w, 750), min(15 * w, 750))
        st = self.status_range(mg, lo, hi)
        head = {Status.LOW: "Below the usual range", Status.HIGH: "Above the usual range",
                Status.OK: "Within the usual range"}[st]
        actual = f"{fmt(mg)} mg per dose" if adult else f"{fmt(mgkg)} mg/kg/dose"
        ref = ("Reference range (≥12 years and ≥50 kg)" if adult else
               "Reference range for this weight (capped at 750 mg per dose)" if 15 * w > 750 else
               "Reference range for this weight")
        res = CheckResult(st, head, [f"Prescribed dose = {actual}",
            f"{ref}: {fmt(lo)}–{fmt(hi)} mg = {fmt(self.ml(r, lo))}–{fmt(self.ml(r, hi))} mL per dose"],
            gauge=(mg, lo, hi, "mg/dose"))

        W = r.warnings
        neo, infant = age_d < 28, 28 <= age_d < 365.25
        if adult:
            W.append(f"Daily total {fmt(daily_mg)} mg exceeds the 4 g/day maximum." if daily_mg > 4000
                     else f"Daily total {fmt(daily_mg)} mg (maximum 4 g/day).")
        elif neo or infant:
            grp = "neonates" if neo else "infants 1–12 months"
            W.append(f"Daily total {fmt(daily_kg)} mg/kg/day exceeds the maximum for {grp}: 60 mg/kg/day."
                     if daily_kg > 60 else f"Daily total {fmt(daily_kg)} mg/kg/day is within the limit for {grp}: ≤60 mg/kg/day.")
        elif daily_mg > 4000:
            W.append(f"Daily total {fmt(daily_mg)} mg exceeds 4 g/day.")
        elif daily_kg > 75:
            W.append(f"Daily total {fmt(daily_kg)} mg/kg/day exceeds the 75 mg/kg/day maximum.")
        elif daily_kg > 60:
            W.append(f"Daily total {fmt(daily_kg)} mg/kg/day is above the usual 60 and within the 75 mg/kg/day maximum.")
        else:
            W.append(f"Daily total {fmt(daily_kg)} mg/kg/day is within the usual limit (≤60; maximum 75 or 4 g).")

        if f > 4:
            W.append("Neonates: every 6–8 hours, maximum 4 doses in 24 hours." if neo
                     else "Frequency exceeds 4 doses in 24 hours; interval 4–6 hours, at least 4.")
        elif neo and f == 4:
            W.append("Neonates: usual interval 6–8 hours; 4 doses is the maximum.")
        if not adult and mg > 750:
            W.append(f"Single dose {fmt(mg)} mg exceeds the pediatric maximum of 750 mg.")
        elif mg > 1000:
            W.append(f"Single dose {fmt(mg)} mg exceeds 1 g.")
        if age_d >= 4383 and w < 50:
            W.append("≥12 years and under 50 kg: dose by weight, not the fixed adult dose.")
        if neo:
            W.append("Neonate (under 28 days)" + (", and under 10 days" if age_d < 10 else "")
                     + ": give only on medical direction using a neonatal reference.")
        elif age_d < 61:
            W.append("Under 2 months: give only on medical direction.")
        if w < 2:
            W.append("Weight under 2 kg: refer to the prescriber before dispensing.")
        if age_d < 730 and dur > 3:
            W.append("Child under 2 years: a course longer than 3 days needs medical direction.")
        if age_d >= 730 and dur > 5:
            W.append("Age 2 years and over: a course longer than 5 days needs medical direction.")
        W.append("Count paracetamol from all products; reduce the limit to 2–3 g/day with liver disease, "
                 "chronic alcohol use or malnutrition. Use the supplied graduated syringe.")
        return res
