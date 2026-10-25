# Dose Lab by WaadAlwagdani

**Oral Suspension Dispensing Calculator (Python)** — designed, clinically specified and built by **Waad Alwagdani, PharmD** (وعد الوقداني).

A pharmacist-built tool that turns a prescribed dose into the volume to draw up, counts the bottles to dispense, and checks pediatric doses for seven drugs against built-in references. It is the Python edition of the [Dose Lab web tool](#), with a command-line interface and a Streamlit web interface sharing one package.

> Dispensing support only. It does not replace the prescriber's decision or an approved clinical reference.

## What it does

- Converts a dose written as **mg/dose, mL/dose, mg/kg/dose or mg/kg/day** to mL, rounded to a measurable step
- Counts bottles by volume and flags courses longer than the in-use shelf life
- Runs drug-specific checks with age-group limits, single-dose and daily caps:

| Drug | Check |
|---|---|
| Paracetamol | 10–15 mg/kg/dose; daily limit by age group (60 / 75 mg/kg/day, 4 g); neonate and infant rules |
| Ibuprofen | 5–10 mg/kg (cap 400 mg), 40 mg/kg/day; adult OTC vs prescription limits; not under 6 months |
| Augmentin | Amoxicillin mg/kg/day vs q8h, q12h, high-dose or infant reference, plus 4:1 / 7:1 / 14:1 ratio match |
| Azithromycin | 3-day, 5-day (with full course plan), pharyngitis and single-dose regimens |
| Depakine | Starting dose 10–15, max 60 mg/kg/day, 3 g/day cap, 1 g per dose |
| Levetiracetam | Age-group limits (50 or 60 mg/kg/day), adult 500–3,000 mg/day |
| Cefuroxime | Indication dose (30 or 20 mg/kg/day) with indication caps |

- Prints a real dispensing label as a 100 × 70 mm PDF (Code 128 barcode, storage tags, use-before date) ready for label printers, saves custom product strengths, and keeps a dispensing log

## Run it

```bash
python -m doselab            # interactive menu
python -m doselab --demo     # sample Depakine case
pip install -r requirements.txt && streamlit run app.py   # web interface
python -m unittest discover -s tests -v                   # 24 tests
```

No third-party packages are needed for the CLI or the tests.

## Project structure

```
doselab/
├── __init__.py        package exports and version
├── __main__.py        `python -m doselab` entry point
├── models.py          dataclasses and Enums: Strength, Drug, Patient, Prescription, DoseResult
├── catalog.py         built-in drugs and strengths
├── calculator.py      dose → mL → bottles, formula lines, general alerts
├── label.py           text dispensing label
├── label_pdf.py       printable PDF label (ReportLab, Code 128 barcode)
├── storage.py         JSON strengths, CSV log, label export
├── cli.py             menus and input validation
└── checks/            one module per drug
    ├── base.py        abstract DoseChecker + @register decorator
    └── paracetamol.py, ibuprofen.py, augmentin.py, azithromycin.py,
        depakine.py, levetiracetam.py, cefuroxime.py
app.py                 Streamlit interface
tests/test_cases.py    reference cases from the source monographs
```

## Python fundamentals used

| Topic | Where |
|---|---|
| **Python basics** — variables, arithmetic, conditionals, loops, f-strings | `calculator.py`, every checker (`if/elif` decision trees), `cli.py` menu loop |
| **Data structures** — dict, list, tuple, frozenset, comprehensions | `catalog.py` (`CATALOG` dict built by comprehension, `DEFAULT_KG_DAY` tuple, `AGE_TABLE_DRUGS` frozenset), lookup dicts like `INTERVAL` and `FREQ_TEXT` |
| **Functions** — parameters, defaults, keyword args, type hints, return tuples, lambdas | `round_to`, `dose_to_mg_and_ml` (returns a tuple), `build_formula`, `calculate`; `fit = lambda need: ...` in `augmentin.py` |
| **OOP** — classes, dataclasses, properties, Enums, abstract base class, inheritance, polymorphism, decorators | `models.py` (`@dataclass`, `@property age_days`, `DoseMode`/`Status` Enums, `__post_init__` validation); `checks/base.py` (`DoseChecker(ABC)` with `@abstractmethod check`, each drug subclass overrides it; `@register` class decorator fills the registry) |
| **Modules & packages** — package layout, relative imports, `__init__`, `__main__`, `__all__` | `doselab/` package with a `checks/` sub-package; importing `checks` registers every checker |
| **File handling** — `pathlib`, JSON, CSV, text, encodings, error handling | `storage.py`: custom strengths saved to `~/.doselab/custom_strengths.json`, dispensing log appended to a CSV with a header written once, label export to `.txt`; a missing or broken JSON file is handled with `try/except` |
| **Errors and testing** | `ValueError` for invalid input, caught in the CLI and Streamlit app; `unittest` suite with temporary directories for file tests |

## Reference cases (from the tests)

| Case | Result |
|---|---|
| Depakine 15 mg/kg/day, 22 kg, q12h, 200 mg/mL | 165 mg = **0.83 mL** per dose, within starting dose |
| Levetiracetam 20 mg/kg/day, 16 kg, q12h, 100 mg/mL | 160 mg = **1.6 mL** per dose |
| Cefuroxime 30 mg/kg/day, 18 kg, q12h, 250 mg/5 mL | 270 mg = **5.4 mL** per dose, 3 × 50 mL bottles |
| Azithromycin 10 → 5 mg/kg, 15 kg, 200 mg/5 mL | 3.8 mL then 1.9 mL × 4 = 11.4 mL, 1 bottle |

---

© 2026 Waad Alwagdani, PharmD. All rights reserved. The concept, clinical logic, design and code are the author's own work and may not be copied, reused or redistributed without written permission.
