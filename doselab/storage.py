"""File handling: custom strengths (JSON), dispensing log (CSV), label export (TXT)."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .models import DoseResult, Strength

DATA_DIR = Path.home() / ".doselab"
STRENGTHS_FILE = DATA_DIR / "custom_strengths.json"
LOG_FILE = DATA_DIR / "dispensing_log.csv"
LOG_FIELDS = ["timestamp", "drug", "strength", "dose", "mode", "frequency", "days",
              "weight_kg", "age", "ml_per_dose", "bottles", "status"]


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_custom_strengths(path: Path = STRENGTHS_FILE) -> dict[str, list[Strength]]:
    """Read saved strengths; a missing or broken file returns an empty dict."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Warning: {path} is not valid JSON; ignoring it.")
        return {}
    return {drug: [Strength(**{**s, "custom": True}) for s in items] for drug, items in raw.items()}


def save_custom_strength(drug_id: str, strength: Strength, path: Path = STRENGTHS_FILE) -> None:
    data = {k: [asdict(s) for s in v] for k, v in load_custom_strengths(path).items()}
    data.setdefault(drug_id, []).append(asdict(strength))
    _ensure_dir(path)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def delete_custom_strength(drug_id: str, index: int, path: Path = STRENGTHS_FILE) -> bool:
    data = {k: [asdict(s) for s in v] for k, v in load_custom_strengths(path).items()}
    if drug_id not in data or not 0 <= index < len(data[drug_id]):
        return False
    data[drug_id].pop(index)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def append_log(r: DoseResult, path: Path = LOG_FILE) -> None:
    """Append one dispensing record to a CSV log (header written once)."""
    _ensure_dir(path)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LOG_FIELDS)
        if new:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "drug": r.drug.name, "strength": r.strength.describe(),
            "dose": r.prescription.dose, "mode": r.prescription.mode.value,
            "frequency": r.prescription.frequency, "days": r.prescription.duration_days,
            "weight_kg": r.patient.weight_kg or "", "age": f"{r.patient.age or ''} {r.patient.age_unit if r.patient.age else ''}".strip(),
            "ml_per_dose": r.ml_per_dose, "bottles": r.bottles,
            "status": r.check.status.value if r.check else "",
        })


def read_log(path: Path = LOG_FILE) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def export_label(text: str, path: Path) -> Path:
    _ensure_dir(path)
    path.write_text(text, encoding="utf-8")
    return path
