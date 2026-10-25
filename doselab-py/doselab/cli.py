# Dose Lab by WaadAlwagdani
# © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com
# All rights reserved. Not to be copied, reused or redistributed without written permission.

"""Interactive command-line interface (menus, loops, input validation)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import storage
from .calculator import calculate
from .catalog import CATALOG, DEFAULT_KG_DAY
from .label import make_label
from .models import DoseMode, Patient, Prescription, Strength

COLORS = {"ok": "\033[32m", "low": "\033[33m", "high": "\033[31m", "end": "\033[0m", "bold": "\033[1m"}


def ask_float(prompt: str, default: float | None = None, allow_blank: bool = False) -> float | None:
    while True:
        raw = input(f"{prompt}{f' [{default:g}]' if default is not None else ''}: ").strip()
        if not raw:
            if default is not None:
                return default
            if allow_blank:
                return None
        try:
            value = float(raw)
            if value <= 0:
                raise ValueError
            return value
        except ValueError:
            print("  Enter a positive number.")


def choose(prompt: str, options: list[str], default: int = 0) -> int:
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        raw = input(f"{prompt} [{default + 1}]: ").strip()
        if not raw:
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print(f"  Choose 1–{len(options)}.")


def strengths_for(drug_id: str) -> list[Strength]:
    return CATALOG[drug_id].strengths + storage.load_custom_strengths().get(drug_id, [])


def print_result(r) -> None:
    c = COLORS
    print(f"\n{c['bold']}{r.drug.name} {r.strength.describe()}{c['end']}")
    print(f"  Volume per dose : {c['bold']}{r.ml_per_dose:g} mL{c['end']}")
    print(f"  Dose            : {r.mg_per_dose:g} mg")
    print(f"  Daily / course  : {r.daily_ml:g} mL/day · {r.total_ml:g} mL")
    print(f"  Bottles         : {r.bottles} ({r.dispensed_ml:g} mL dispensed)")
    print("\nFormula")
    for line in r.formula:
        print("  " + line)
    if r.check:
        col = c[r.check.status.value]
        print(f"\nCheck: {col}{r.check.title}{c['end']}")
        for line in r.check.lines:
            print("  " + line)
    if r.warnings:
        print("\nAlerts")
        for w in r.warnings:
            print("  • " + w)
    print("\n" + make_label(r))


def run_calculation() -> None:
    ids = list(CATALOG)
    i = choose("Drug", [CATALOG[k].name for k in ids])
    drug_id = ids[i]
    sts = strengths_for(drug_id)
    s = sts[choose("Strength", [x.describe() + (" (added)" if x.custom else "") for x in sts])]
    modes = list(DoseMode)
    labels = ["mg per dose", "mL per dose", "mg/kg per dose", "mg/kg/day"]
    mode = modes[choose("Dose entered as", labels, default=3 if drug_id in DEFAULT_KG_DAY else 0)]
    dose = ask_float("Dose")
    freq = ask_float("Doses per day", 2 if drug_id in DEFAULT_KG_DAY else 1 if drug_id == "azithromycin" else 3)
    days = ask_float("Duration (days)", 5)
    weight = ask_float("Weight kg (blank to skip)", allow_blank=True)
    age = ask_float("Age (blank to skip)", allow_blank=True)
    unit = ["years", "months", "days"][choose("Age unit", ["years", "months", "days"])] if age else "years"
    extra = {}
    if drug_id == "azithromycin":
        extra["azithro_regimen"] = ["d3", "d5", "strep", "single"][choose("Regimen", [
            "10 mg/kg × 3 days", "10 mg/kg day 1 then 5 mg/kg days 2–5", "12 mg/kg × 5 days", "30 mg/kg single dose"])]
        if extra["azithro_regimen"] == "d5":
            extra["azithro_day"] = ["1", "2"][choose("Entered dose is for", ["Day 1", "Days 2–5"])]
    if drug_id == "cefuroxime":
        extra["cef_regimen"] = ["aom", "phar"][choose("Indication", ["Otitis / sinusitis", "Pharyngitis"])]
    if drug_id == "augmentin" and mode is DoseMode.MG_PER_DOSE:
        extra["augmentin_basis"] = ["total", "amoxicillin"][choose("Prescribed mg refers to", ["Total product", "Amoxicillin component"])]
    try:
        rx = Prescription(drug_id, s, dose, mode, freq, days,
                          rounding=0.01 if drug_id == "depakine" else 0.1, **extra)
        r = calculate(rx, Patient(weight, age, unit))
    except ValueError as e:
        print(f"\n{COLORS['high']}{e}{COLORS['end']}")
        return
    print_result(r)
    if input("\nSave to dispensing log? [y/N]: ").strip().lower() == "y":
        storage.append_log(r)
        print(f"  Saved to {storage.LOG_FILE}")
    if input("Export label to a text file? [y/N]: ").strip().lower() == "y":
        path = storage.export_label(make_label(r), Path.cwd() / f"label_{drug_id}.txt")
        print(f"  Written to {path}")


def add_strength() -> None:
    ids = list(CATALOG)
    drug_id = ids[choose("Drug", [CATALOG[k].name for k in ids])]
    if drug_id == "augmentin":
        amox, clav = ask_float("Amoxicillin mg"), ask_float("Clavulanate mg")
        mg = amox + clav
    else:
        amox = clav = None
        mg = ask_float("Active drug mg")
    vol = ask_float("Per volume mL", 5)
    bottle = ask_float("Bottle size mL")
    shelf = ask_float("In-use shelf life days (blank to skip)", allow_blank=True)
    s = Strength(mg, vol, bottle, int(shelf) if shelf else None, amox, clav)
    storage.save_custom_strength(drug_id, s)
    print(f"  Saved {s.describe()} for {CATALOG[drug_id].name}.")


def show_log() -> None:
    rows = storage.read_log()
    if not rows:
        print("  The dispensing log is empty.")
        return
    for row in rows[-15:]:
        print(f"  {row['timestamp']}  {row['drug']:<22} {row['ml_per_dose']:>6} mL × {row['frequency']:<3} "
              f"{row['bottles']} btl  {row['status']}")


MENU = {"1": ("Calculate a dose", run_calculation), "2": ("Add a strength you stock", add_strength),
        "3": ("View dispensing log", show_log)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doselab", description="Dose Lab by WaadAlwagdani — oral suspension dispensing calculator",
                                     epilog="© 2026 Waad Alwagdani, PharmD. All rights reserved.")
    parser.add_argument("--demo", action="store_true", help="run a sample Depakine case and exit")
    args = parser.parse_args(argv)
    if args.demo:
        s = CATALOG["depakine"].strengths[1]
        print_result(calculate(Prescription("depakine", s, 15, DoseMode.MG_KG_DAY, 2, 30, rounding=0.01),
                               Patient(22, 6, "years")))
        return 0
    print("Dose Lab by WaadAlwagdani — oral suspension dispensing calculator\n© 2026 Waad Alwagdani, PharmD. All rights reserved.")
    while True:
        print("\n" + "\n".join(f"  {k}. {v[0]}" for k, v in MENU.items()) + "\n  0. Exit")
        key = input("> ").strip()
        if key == "0":
            return 0
        if key in MENU:
            try:
                MENU[key][1]()
            except (KeyboardInterrupt, EOFError):
                print("\n  Cancelled.")
        else:
            print("  Choose a menu number.")


if __name__ == "__main__":
    sys.exit(main())
