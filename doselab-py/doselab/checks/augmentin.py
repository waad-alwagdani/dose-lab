# Dose Lab by WaadAlwagdani
# © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com
# All rights reserved. Not to be copied, reused or redistributed without written permission.

from ..models import CheckResult, Status
from .base import DoseChecker, fmt, register


@register("augmentin")
class AugmentinChecker(DoseChecker):
    name = "Augmentin"
    REFS = {  # key: (title prefix, lo, hi, gauge max, needed ratio, frequency)
        "infant": ("infant reference dose", 28.5, 31.5, 60, 4, 2),
        "q8": ("standard q8h range", 20, 40, 60, 4, 3),
        "q12": ("standard q12h range", 25, 45, 70, 7, 2),
        "high": ("high-dose target", 85.5, 94.5, 130, 14, 2),
    }

    @staticmethod
    def auto_reference(f, age_d, ratio):
        if age_d is not None and age_d < 84:
            return "infant"
        if f == 3:
            return "q8"
        if f == 2:
            return "high" if (ratio or 0) >= 12 else "q12"
        return "auto"

    def check(self, r):
        s, p, w = r.strength, r.prescription, r.patient.weight_kg
        f, age_d = p.frequency, r.patient.age_days
        amox_dose = r.ml_per_dose * s.amox_mg / s.vol
        clav_dose = r.ml_per_dose * s.clav_mg / s.vol
        amox_daily, clav_daily = amox_dose * f / w, clav_dose * f / w
        ref = p.augmentin_reference if p.augmentin_reference != "auto" else self.auto_reference(f, age_d, s.ratio)
        af, rt = f"{fmt(s.amox_mg)}/{fmt(s.clav_mg)} mg per {fmt(s.vol)} mL", f"{s.ratio:g}:1"
        fit = lambda need: abs(s.ratio - need) <= need * 0.15
        W = r.warnings

        if ref not in self.REFS:
            res = CheckResult(Status.LOW, "Automatic reference not available",
                              ["Choose a reference manually; the frequency does not match q8h or q12h.",
                               f"The selected strength has a ratio of {rt}."])
        else:
            name, lo, hi, gmax, need, freq = self.REFS[ref]
            st = (self.status_target(amox_daily, 30) if ref == "infant" else
                  self.status_target(amox_daily, 90) if ref == "high" else
                  self.status_range(amox_daily, lo, hi))
            title = {Status.OK: f"Within the {name}", Status.LOW: f"Below the {name}", Status.HIGH: f"Above the {name}"}[st]
            match = (f"The selected strength {af} (ratio {rt}) matches this regimen." if fit(need) else
                     f"This regimen uses a {need}:1 formulation; the selected strength {af} has a ratio of {rt}.")
            res = CheckResult(st, title, [f"Actual prescribed dose: {fmt(amox_daily)} mg/kg/day amoxicillin.",
                f"Reference: {lo if ref not in ('infant','high') else (30 if ref=='infant' else 90)}"
                f"{'' if ref in ('infant','high') else f'–{hi}'} mg/kg/day amoxicillin.", match,
                f"Actual clavulanate: {fmt(clav_daily)} mg/kg/day."], gauge=(amox_daily, lo, hi, "mg/kg/day amoxicillin"))
            if f != freq:
                W.append(f"Compared with the {ref} reference, but the entered frequency is not {fmt(freq)} times daily.")
            if not fit(need) and ref in ("q12", "high"):
                W.append(f"Do not substitute the {rt} strength by changing the volume; this regimen needs {need}:1.")
            if ref == "infant" and age_d >= 84:
                W.append("The under-12-weeks reference does not match the entered age.")
        if age_d < 84 and ref != "infant":
            W.append("Under 12 weeks: usual reference is 30 mg/kg/day amoxicillin every 12 hours (4:1 formulation).")
        if w >= 40:
            W.append("Weight 40 kg or more: use adult dosing instead of pediatric weight-based tables.")
        if clav_daily > 10:
            W.append(f"Clavulanate {fmt(clav_daily)} mg/kg/day exceeds 10 mg/kg/day.")
        if p.mode.value == "direct" and p.augmentin_basis == "total":
            W.append(f"The prescribed mg was converted on the {fmt(s.mg)} mg/{fmt(s.vol)} mL total; "
                     f"the check uses the actual amoxicillin {fmt(s.amox_mg)} mg/{fmt(s.vol)} mL.")
        W.append("Augmentin strengths are not directly interchangeable; check the amoxicillin-to-clavulanate ratio.")
        r.extra = {"amox_per_dose_mg": amox_dose, "clav_per_dose_mg": clav_dose}
        return res
