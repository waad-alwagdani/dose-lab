from ..models import CheckResult, Status
from .base import DoseChecker, fmt, register


@register("depakine")
class DepakineChecker(DoseChecker):
    name = "Depakine"

    def check(self, r):
        w, f, mg, age_d = r.patient.weight_kg, r.prescription.frequency, r.mg_per_dose, r.patient.age_days
        daily = mg * f
        dk = daily / w
        if age_d < 182.6:
            st, head = Status.HIGH, "Not recommended under 6 months"
        elif dk > 60 + 1e-9:
            st, head = Status.HIGH, "Exceeds the 60 mg/kg/day maximum"
        elif daily > 3000:
            st, head = Status.HIGH, "Exceeds the 3,000 mg/day cap"
        elif mg > 1000:
            st, head = Status.HIGH, "Single dose exceeds 1,000 mg"
        elif dk < 10 - 1e-9:
            st, head = Status.LOW, "Below the usual starting dose"
        else:
            st, head = Status.OK, "Within the usual starting dose" if dk <= 15 else "Within the titration range"
        max_day = min(60 * w, 3000)
        lines = [f"Prescribed: {fmt(mg)} mg × {fmt(f)} = {fmt(daily)} mg/day ({fmt(dk)} mg/kg/day).",
                 f"Start for this weight: {fmt(10 * w)}–{fmt(15 * w)} mg/day; maximum {fmt(max_day)} mg/day = "
                 f"{fmt(self.ml(r, max_day / f))} mL per dose over {self.doses_word(f)}."]
        W = r.warnings
        if age_d < 182.6:
            W.append("Under 6 months: not recommended due to the risk of fatal hepatotoxicity.")
        elif age_d < 730.5:
            W.append("Under 2 years: high hepatotoxicity risk; monotherapy preferred with liver enzyme monitoring.")
        if mg > 1000 and "1,000" not in head:
            W.append(f"Single dose {fmt(mg)} mg exceeds 1,000 mg.")
        if f == 1:
            W.append("Immediate-release syrup is divided into 2–3 doses daily.")
        if f > 3:
            W.append("Usual syrup frequency is 2–3 times daily.")
        if age_d >= 4383:
            W.append("Females of childbearing potential: confirm no pregnancy and adherence to the SFDA pregnancy prevention programme.")
        W.append("57.64 mg/mL and 200 mg/mL differ by about 3.5×. Monitor serum level (50–100 mcg/mL), liver enzymes and platelets. "
                 "Key interactions: carbapenems, lamotrigine, aspirin, phenytoin, phenobarbital.")
        return CheckResult(st, head, lines, gauge=(dk, 10, 60, "mg/kg/day"))
