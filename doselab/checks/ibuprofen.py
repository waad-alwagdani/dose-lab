from ..models import CheckResult, Status
from .base import DoseChecker, fmt, register


@register("ibuprofen")
class IbuprofenChecker(DoseChecker):
    name = "ibuprofen"

    def check(self, r):
        w, f, mg = r.patient.weight_kg, r.prescription.frequency, r.mg_per_dose
        age_d, dur = r.patient.age_days, r.prescription.duration_days
        adult = age_d >= 4383 or w >= 50
        daily = mg * f
        lo, hi = (200, 800) if adult else (min(5 * w, 400), min(10 * w, 400))
        under6m = age_d < 182.6
        st = Status.HIGH if under6m else self.status_range(mg, lo, hi)
        title = ("Not recommended under 6 months" if under6m else
                 {Status.OK: "Within the usual range", Status.LOW: "Below the usual range",
                  Status.HIGH: "Above the usual range"}[st])
        ref = "≥12 years or ≥50 kg" if adult else "5–10 mg/kg for this weight" + (" (capped at 400 mg)" if 10 * w > 400 else "")
        res = CheckResult(st, title, [f"Prescribed: {fmt(mg)} mg ({fmt(mg / w)} mg/kg).",
            f"Reference: {ref} = {fmt(lo)}–{fmt(hi)} mg = {fmt(self.ml(r, lo))}–{fmt(self.ml(r, hi))} mL per dose."],
            gauge=(mg, lo, hi, "mg/dose"))
        W = r.warnings
        if under6m:
            W.append("Under 6 months: ibuprofen is not used due to the risk of renal toxicity and GI bleeding.")
        if adult:
            if daily > 3200:
                W.append(f"Daily total {fmt(daily)} mg exceeds the prescription maximum of 3,200 mg/day.")
            elif daily > 1200:
                W.append(f"Daily total {fmt(daily)} mg is above the OTC limit of 1,200 mg and within the prescription limit of 3,200 mg.")
            else:
                W.append(f"Daily total {fmt(daily)} mg is within the limit (1,200 mg OTC, 3,200 mg on prescription).")
            if f > 6:
                W.append("Frequency exceeds 6 doses daily; minimum interval 4 hours.")
            if dur > 10:
                W.append("Duration exceeds 10 days for pain or 3 days for fever; needs medical review.")
        else:
            dk = daily / w
            if daily > 2400:
                W.append(f"Daily total {fmt(daily)} mg exceeds the 2,400 mg/day cap.")
            elif dk > 40:
                W.append(f"Daily total {fmt(dk)} mg/kg/day exceeds the 40 mg/kg/day maximum.")
            else:
                W.append(f"Daily total {fmt(dk)} mg/kg/day is within the limit (≤40 mg/kg/day).")
            if f > 4:
                W.append("Children: every 6–8 hours, maximum 4 doses in 24 hours.")
            if dur > 3:
                W.append("Fever lasting more than 3 days needs medical review.")
        W.append("Give with food and keep hydrated. Avoid with active ulcer, severe renal impairment and pregnancy from 20 weeks. "
                 "Infant drops (40 mg/mL) are twice the strength of the syrup (20 mg/mL).")
        return res
