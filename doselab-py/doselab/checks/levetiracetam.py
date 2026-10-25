# Dose Lab by WaadAlwagdani
# © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com
# All rights reserved. Not to be copied, reused or redistributed without written permission.

from ..models import CheckResult, Status
from .base import DoseChecker, fmt, register


def lev_ceiling(w, age_d):
    """Return the age-group limits as a dict."""
    if w >= 50 or age_d >= 5844:
        return {"adult": True, "mg": 3000, "grp": "≥16 years or ≥50 kg"}
    kg, single = 60, 30
    if age_d < 30.44:
        grp = "Neonates"
    elif age_d < 182.6:
        grp = "Infants 1–6 months"
    elif age_d < 1461:
        kg, single, grp = 50, 25, "6 months to 3 years"
    else:
        grp = "4 to 15 years"
    return {"adult": False, "kg": kg, "single_kg": single, "mg": min(kg * w, 3000), "grp": grp}


@register("levetiracetam")
class LevetiracetamChecker(DoseChecker):
    name = "levetiracetam"

    def check(self, r):
        w, f, mg, age_d = r.patient.weight_kg, r.prescription.frequency, r.mg_per_dose, r.patient.age_days
        c = lev_ceiling(w, age_d)
        daily = mg * f
        dk = daily / w
        if c["adult"]:
            if daily > 3000: st, head = Status.HIGH, "Exceeds the 3,000 mg/day cap"
            elif mg > 1500: st, head = Status.HIGH, "Single dose exceeds 1,500 mg"
            elif daily < 500: st, head = Status.LOW, "Below the minimum adult dose of 500 mg/day"
            else: st, head = Status.OK, "Within the adult starting dose" if daily <= 1000 else "Within the adult maintenance range"
            ref = f"Reference ({c['grp']}): 500–3,000 mg/day, single dose up to 1,500 mg."
            gauge = (daily, 500, 3000, "mg/day")
        else:
            if dk > c["kg"] + 1e-9: st, head = Status.HIGH, f"Exceeds the group limit of {c['kg']} mg/kg/day"
            elif daily > 3000: st, head = Status.HIGH, "Exceeds the 3,000 mg/day cap"
            elif mg > 1500: st, head = Status.HIGH, "Single dose exceeds 1,500 mg"
            elif mg / w > c["single_kg"] + 1e-9: st, head = Status.HIGH, f"Single dose exceeds {c['single_kg']} mg/kg"
            elif dk < 10 - 1e-9: st, head = Status.LOW, "Below the minimum of 10 mg/kg/day"
            else: st, head = Status.OK, "Within the starting dose" if dk <= 20 else "Within the maintenance range"
            ref = (f"Reference ({c['grp']}): start {fmt(20 * w)} mg/day; limit {fmt(c['mg'])} mg/day = "
                   f"{fmt(self.ml(r, c['mg'] / f))} mL per dose over {self.doses_word(f)}.")
            gauge = (dk, 10, c["kg"], "mg/kg/day")
        W = r.warnings
        if mg > 1500 and "1,500" not in head:
            W.append(f"Single dose {fmt(mg)} mg exceeds 1,500 mg.")
        if not c["adult"] and mg / w > c["single_kg"] + 1e-9 and f"{c['single_kg']} mg/kg" not in head:
            W.append(f"Single dose {fmt(mg / w)} mg/kg exceeds {c['single_kg']} mg/kg per dose.")
        if f != 2:
            W.append("The immediate-release solution is given every 12 hours (twice daily).")
        if age_d < 182.6:
            W.append("Under 6 months: titrate by 10 mg/kg/day weekly with close monitoring.")
        W.append("Renal: CrCl 50–80 500–1,000 mg q12h; 30–49 250–750 mg; <30 250–500 mg." if c["adult"]
                 else "In renal impairment, reduce the maintenance dose in proportion.")
        W.append("Monitor behaviour, mood and somnolence. Taper gradually. In obesity, dose on ideal body weight.")
        return CheckResult(st, head, [f"Prescribed: {fmt(mg)} mg × {fmt(f)} = {fmt(daily)} mg/day ({fmt(dk)} mg/kg/day).", ref], gauge=gauge)
