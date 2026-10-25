import math

from ..models import CheckResult, Status
from .base import DoseChecker, fmt, register


@register("azithromycin")
class AzithromycinChecker(DoseChecker):
    name = "azithromycin"

    def regimen(self, reg, day):
        return {"d3": (10, 500, 3, "10 mg/kg × 3 days"),
                "d5": (10 if day == "1" else 5, 500 if day == "1" else 250, 5,
                       "10 mg/kg day 1" if day == "1" else "5 mg/kg days 2–5"),
                "strep": (12, 500, 5, "12 mg/kg × 5 days"),
                "single": (30, 1500, 1, "30 mg/kg single dose")}[reg]

    def check(self, r):
        p, w, mg, f = r.prescription, r.patient.weight_kg, r.mg_per_dose, r.prescription.frequency
        age_d, dur = r.patient.age_days, p.duration_days
        k, cap, days, name = self.regimen(p.azithro_regimen, p.azithro_day)
        big = w >= 45
        target = cap if big else min(k * w, cap)
        lo, hi = target * 0.9, target * 1.1
        st = self.status_range(mg, lo, hi)
        lines = [f"Prescribed: {fmt(mg)} mg ({fmt(mg / w)} mg/kg).",
                 f"Reference: {'adult dose for 45 kg and above' if big else name} = {fmt(target)} mg"
                 f"{f' (capped at {fmt(cap)} mg)' if not big and k * w > cap else ''} = {fmt(self.ml(r, target))} mL once daily."]
        W = r.warnings
        if p.azithro_regimen == "d5":
            d1, d2 = (500, 250) if big else (min(10 * w, 500), min(5 * w, 250))
            from ..calculator import round_to
            v1, v2 = (round_to(self.ml(r, x), p.rounding) for x in (d1, d2))
            tot = v1 + 4 * v2
            n = math.ceil(tot / r.strength.bottle)
            lines.append(f"Course plan: day 1 {fmt(v1)} mL ({fmt(d1)} mg), then {fmt(v2)} mL "
                         f"({fmt(d2)} mg) daily on days 2–5. Total {fmt(tot)} mL = {n} bottle{'s' * (n != 1)}.")
            W.append("For the day 1 then days 2–5 regimen, use the bottle count from the course plan.")
        title = {Status.OK: "Within the selected regimen dose", Status.LOW: "Below the selected regimen dose",
                 Status.HIGH: "Above the selected regimen dose"}[st]
        if f != 1:
            W.append("Azithromycin is given once daily.")
        if age_d < 182.6:
            W.append("Under 6 months: the dose is individualized by the prescriber.")
        if p.azithro_regimen == "strep" and age_d < 730.5:
            W.append("The 12 mg/kg pharyngitis regimen is approved from 2 years of age.")
        if p.azithro_regimen != "d5" and dur != days:
            W.append(f"The selected regimen lasts {'a single dose' if days == 1 else f'{days} days'}; the entered duration is {fmt(dur)}.")
        if p.azithro_regimen != "single" and mg * f > 500:
            W.append(f"Daily dose {fmt(mg * f)} mg exceeds 500 mg/day.")
        course = mg * f * dur
        if p.azithro_regimen not in ("d5", "strep") and course > 1500:
            W.append(f"Course total {fmt(course)} mg exceeds 1,500 mg.")
        W.append("Use the current measured weight, complete the course, and review interactions, heart rhythm disorders and liver disease.")
        return CheckResult(st, title, lines, gauge=(mg, lo, hi, "mg/dose"))
