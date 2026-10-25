# Dose Lab by WaadAlwagdani
# © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com
# All rights reserved. Not to be copied, reused or redistributed without written permission.

"""Built-in drug catalog (data structures: list, dict, tuple, comprehension)."""

from .models import Drug, Strength

S = Strength

CATALOG: dict[str, Drug] = {d.id: d for d in [
    Drug("augmentin", "Augmentin", [
        S(156, 5, 100, 7, 125, 31.25, "156 mg/5 mL (125/31.25)"),
        S(228.5, 5, 70, 7, 200, 28.5, "228.5 mg/5 mL (200/28.5)"),
        S(457, 5, 70, 7, 400, 57, "457 mg/5 mL (400/57)"),
        S(642.9, 5, 100, 10, 600, 42.9, "ES 642.9 mg/5 mL (600/42.9)"),
    ]),
    Drug("amoxicillin", "Amoxicillin", [S(250, 5, 100), S(125, 5, 100), S(400, 5, 100)]),
    Drug("paracetamol", "Paracetamol", [S(160, 5, 145), S(120, 5, 100), S(250, 5, 100)]),
    Drug("ibuprofen", "Ibuprofen", [S(100, 5, 145), S(200, 5, 100), S(40, 1, 15, label="Drops 40 mg/mL")]),
    Drug("dextromethorphan", "Dextromethorphan", [S(15, 5, 120), S(7.5, 5, 120)]),
    Drug("diphenhydramine", "Diphenhydramine", [S(13.5, 5, 120), S(12.5, 5, 120)]),
    Drug("cefuroxime", "Cefuroxime", [S(250, 5, 50, 10), S(125, 5, 50, 10)]),
    Drug("metronidazole", "Metronidazole", [S(125, 5, 120), S(200, 5, 100)]),
    Drug("chlorpheniramine", "Chlorpheniramine", [S(2, 5, 100)]),
    Drug("depakine", "Depakine (valproate)", [S(57.64, 1, 150), S(200, 1, 40)]),
    Drug("carbamazepine", "Carbamazepine", [S(100, 5, 100)]),
    Drug("levetiracetam", "Levetiracetam", [S(100, 1, 150), S(100, 1, 300, label="100 mg/mL — 300 mL")]),
    Drug("azithromycin", "Azithromycin", [S(200, 5, 15), S(200, 5, 30, label="200 mg/5 mL — 30 mL"), S(100, 5, 15)]),
    Drug("risperidone", "Risperidone", [S(1, 1, 100)]),
    Drug("lactulose", "Lactulose", [S(10000, 15, 300, label="10 g/15 mL"), S(10000, 15, 200, label="10 g/15 mL — 200 mL")]),
]}

# Drugs whose inputs are usually mg/kg/day (immutable tuple)
DEFAULT_KG_DAY: tuple[str, ...] = ("depakine", "levetiracetam", "cefuroxime")
# Drugs dosed by age/product table rather than weight
AGE_TABLE_DRUGS: frozenset[str] = frozenset({"dextromethorphan", "diphenhydramine", "chlorpheniramine"})


def get_drug(drug_id: str) -> Drug:
    try:
        return CATALOG[drug_id]
    except KeyError:
        raise KeyError(f"Unknown drug '{drug_id}'. Options: {', '.join(CATALOG)}") from None
