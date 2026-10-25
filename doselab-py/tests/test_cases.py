# Dose Lab by WaadAlwagdani
# © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com
# All rights reserved. Not to be copied, reused or redistributed without written permission.

"""Reference cases from the source monographs and the web version's test runs."""

import tempfile
import unittest
from pathlib import Path

from doselab import CATALOG, Patient, Prescription, calculate
from doselab import storage
from doselab.models import DoseMode, Status, Strength

KG_DAY = DoseMode.MG_KG_DAY


def run(drug, dose, weight=None, age=None, unit="years", freq=3, days=5, strength=0, mode=DoseMode.MG_PER_DOSE, **kw):
    s = CATALOG[drug].strengths[strength]
    rounding = kw.pop("rounding", 0.01 if drug == "depakine" else 0.1)
    return calculate(Prescription(drug, s, dose, mode, freq, days, rounding=rounding, **kw), Patient(weight, age, unit))


def has(r, text):
    return any(text in w for w in r.warnings)


class Core(unittest.TestCase):
    def test_amoxicillin_bottles(self):
        r = run("amoxicillin", 250, freq=3, days=7)
        self.assertEqual((r.ml_per_dose, r.total_ml, r.bottles), (5, 105, 2))
        self.assertIsNone(r.check)

    def test_rounding_half_up(self):
        self.assertEqual(run("depakine", 15, 22, 6, freq=2, days=30, strength=1, mode=KG_DAY).ml_per_dose, 0.83)

    def test_validation(self):
        with self.assertRaises(ValueError):
            run("paracetamol", 150)  # weight and age required
        with self.assertRaises(ValueError):
            Prescription("paracetamol", CATALOG["paracetamol"].strengths[0], 0)


class Paracetamol(unittest.TestCase):
    def test_usual(self):
        r = run("paracetamol", 150, 10, 1, freq=4, days=3)
        self.assertEqual(r.check.status, Status.OK)
        self.assertEqual(r.ml_per_dose, 4.7)

    def test_above_usual_daily(self):
        self.assertTrue(has(run("paracetamol", 180, 10, 2, freq=4, days=3), "above the usual 60"))

    def test_neonate(self):
        r = run("paracetamol", 45, 3, 20, "days", freq=5, days=2)
        self.assertTrue(has(r, "maximum for neonates"))
        self.assertTrue(has(r, "Neonate (under 28 days)"))

    def test_adult_fixed_dose(self):
        self.assertEqual(run("paracetamol", 1000, 60, 13, freq=4, days=3).check.status, Status.OK)

    def test_child_single_cap(self):
        self.assertTrue(has(run("paracetamol", 900, 60, 10, freq=4, days=3), "pediatric maximum of 750"))


class Ibuprofen(unittest.TestCase):
    def test_case1(self):
        self.assertEqual(run("ibuprofen", 100, 11, 18, "months", freq=4, days=3).check.status, Status.OK)

    def test_under_6_months(self):
        self.assertEqual(run("ibuprofen", 50, 6, 4, "months").check.status, Status.HIGH)

    def test_adolescent_otc(self):
        self.assertTrue(has(run("ibuprofen", 400, 45, 14, freq=6, days=3), "above the OTC limit"))


class Augmentin(unittest.TestCase):
    def test_q8(self):
        r = run("augmentin", 156, 15, 3, freq=3, days=7)
        self.assertEqual((r.check.status, r.ml_per_dose), (Status.OK, 5))
        self.assertIn("q8h", r.check.title)

    def test_es_high_dose_auto(self):
        self.assertIn("high-dose", run("augmentin", 900, 20, 4, freq=2, days=10, strength=3).check.title)


class Azithromycin(unittest.TestCase):
    def test_three_day(self):
        self.assertEqual(run("azithromycin", 250, 25, 5, freq=1, days=3).check.status, Status.OK)

    def test_five_day_plan(self):
        r = run("azithromycin", 150, 15, 3, freq=1, days=1, azithro_regimen="d5")
        self.assertTrue(any("Total 11.4 mL" in line for line in r.check.lines))

    def test_single_dose_cap(self):
        self.assertEqual(run("azithromycin", 1800, 60, 15, freq=1, days=1, azithro_regimen="single").check.status, Status.HIGH)


class Depakine(unittest.TestCase):
    def test_reference_case(self):
        r = run("depakine", 15, 22, 6, freq=2, days=30, strength=1, mode=KG_DAY)
        self.assertEqual(r.check.status, Status.OK)
        self.assertIn("Total daily dose = 22 kg × 15 mg/kg/day = 330 mg/day", r.formula[0])

    def test_over_60(self):
        self.assertEqual(run("depakine", 70, 30, 10, freq=3, days=30, strength=1, mode=KG_DAY).check.status, Status.HIGH)


class Levetiracetam(unittest.TestCase):
    def test_start(self):
        r = run("levetiracetam", 20, 16, 4, freq=2, days=30, mode=KG_DAY)
        self.assertEqual((r.check.status, r.ml_per_dose), (Status.OK, 1.6))

    def test_group_limit_50(self):
        self.assertIn("50 mg/kg/day", run("levetiracetam", 55, 12, 2, freq=2, days=30, mode=KG_DAY).check.title)


class Cefuroxime(unittest.TestCase):
    def test_reference_case(self):
        r = run("cefuroxime", 30, 18, 5, freq=2, days=10, mode=KG_DAY)
        self.assertEqual((r.check.status, r.ml_per_dose, r.bottles), (Status.OK, 5.4, 3))

    def test_pharyngitis_cap(self):
        self.assertEqual(run("cefuroxime", 20, 30, 10, freq=2, days=10, mode=KG_DAY, cef_regimen="phar").check.status, Status.HIGH)


class FileHandling(unittest.TestCase):
    def test_strengths_and_log_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            sp, lp = Path(tmp) / "s.json", Path(tmp) / "log.csv"
            storage.save_custom_strength("paracetamol", Strength(125, 5, 60), sp)
            self.assertEqual(storage.load_custom_strengths(sp)["paracetamol"][0].bottle, 60)
            self.assertTrue(storage.delete_custom_strength("paracetamol", 0, sp))
            storage.append_log(run("amoxicillin", 250, freq=3, days=7), lp)
            storage.append_log(run("amoxicillin", 250, freq=3, days=7), lp)
            self.assertEqual(len(storage.read_log(lp)), 2)

    def test_broken_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.json"
            p.write_text("{not json")
            self.assertEqual(storage.load_custom_strengths(p), {})


if __name__ == "__main__":
    unittest.main()
