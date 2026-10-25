from ..models import CheckResult, Status
from .base import DoseChecker, fmt, register


def cef_reference(w, age_d, regimen):
    cap = 500 if regimen == "phar" else 1000
    if w >= 40 or age_d >= 4748:
        return {"adult": True, "cap": cap, "grp": "≥13 years or ≥40 kg"}
    k = 20 if regimen == "phar" else 30
    return {"adult": False, "k": k, "cap": cap, "target": min(k * w, cap),
            "grp": "Pharyngitis" if regimen == "phar" else "Otitis / sinusitis"}


@register("cefuroxime")
class CefuroximeChecker(DoseChecker):
    name = "cefuroxime"

    def check(self, r):
        p, w, mg, f, age_d = r.prescription, r.patient.weight_kg, r.mg_per_dose, r.prescription.frequency, r.patient.age_days
        c = cef_reference(w, age_d, p.cef_regimen)
        daily = mg * f
        dk = daily / w
        head = "Oral form not approved under 3 months" if age_d < 91.3 else None
        st = Status.HIGH if head else None
        if c["adult"]:
            if not head:
                if mg > 500: st, head = Status.HIGH, "Single dose exceeds 500 mg"
                elif daily > c["cap"]: st, head = Status.HIGH, f"Exceeds the {fmt(c['cap'])} mg/day limit"
                elif mg < 250 - 1e-9: st, head = Status.LOW, "Below the minimum adult dose of 250 mg"
                else: st, head = Status.OK, "Within the adult dose"
            ref = f"Reference ({c['grp']}): 250–500 mg per dose every 12 hours, maximum {fmt(c['cap'])} mg/day."
            gauge = (mg, 250, 500, "mg/dose")
        else:
            lo, hi = c["target"] * 0.9, c["target"] * 1.1
            capped = f" (capped at {fmt(c['cap'])})" if c["k"] * w > c["cap"] else ""
            if not head:
                if mg > 500: st, head = Status.HIGH, "Single dose exceeds 500 mg"
                elif daily > c["cap"] + 1e-9: st, head = Status.HIGH, f"Exceeds the indication limit of {fmt(c['cap'])} mg/day"
                elif daily > hi: st, head = Status.HIGH, "Above the indication dose"
                elif daily < lo: st, head = Status.LOW, "Below the indication dose"
                else: st, head = Status.OK, "Within the indication dose"
            ref = (f"Reference ({c['grp']}): {c['k']} mg/kg/day = {fmt(c['target'])} mg/day"
                   f"{capped}"
                   f" = {fmt(self.ml(r, c['target'] / 2))} mL every 12 hours.")
            gauge = (daily, lo, hi, "mg/day")
        W = r.warnings
        if mg > 500 and "500 mg" not in head:
            W.append(f"Single dose {fmt(mg)} mg exceeds 500 mg.")
        if daily > c["cap"] + 1e-9 and "mg/day" not in head:
            W.append(f"Daily total {fmt(daily)} mg exceeds the {fmt(c['cap'])} mg/day limit.")
        if not c["adult"] and dk < 10 - 1e-9:
            W.append("Dose is below the pediatric minimum of 10 mg/kg/day.")
        if f != 2:
            W.append("The oral suspension is given every 12 hours (twice daily).")
        if p.duration_days > 14:
            W.append("Duration exceeds 14 days; usual is 7–10 days for acute infections.")
        elif p.duration_days < 7:
            W.append("Usual suspension course is 10 days for otitis, sinusitis and pharyngitis.")
        W.append("Give with food, refrigerate after reconstitution, discard after 10 days. Antacids and PPIs reduce absorption. "
                 "Check penicillin/cephalosporin allergy.")
        return CheckResult(st, head, [f"Prescribed: {fmt(mg)} mg × {fmt(f)} = {fmt(daily)} mg/day ({fmt(dk)} mg/kg/day).", ref], gauge=gauge)
