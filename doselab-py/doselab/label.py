# Dose Lab by WaadAlwagdani
# © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com
# All rights reserved. Not to be copied, reused or redistributed without written permission.

"""Plain-text dispensing label."""

from datetime import date, timedelta

from .checks.base import fmt
from .models import DoseResult

FREQ_TEXT = {1: "once daily", 2: "every 12 hours", 3: "every 8 hours", 4: "every 6 hours", 6: "every 4 hours"}


def make_label(r: DoseResult, today: date | None = None) -> str:
    today = today or date.today()
    rx, s = r.prescription, r.strength
    freq = FREQ_TEXT.get(rx.frequency, f"{fmt(rx.frequency)} times daily")
    days = "1 day" if rx.duration_days == 1 else f"{fmt(rx.duration_days)} days"
    use_before = (today + timedelta(days=s.shelf_days)).strftime("%d %b %Y") if s.shelf_days else "—"
    tags = ["Shake well before use", "By mouth"]
    if rx.drug_id == "augmentin":
        tags.append("Refrigerate after reconstitution")
    if s.shelf_days and rx.duration_days > s.shelf_days:
        tags.append("Course exceeds in-use shelf life")
    width = 52
    rows = [
        "PHARMACY ▪ DISPENSING LABEL".ljust(width - 11) + today.strftime("%d %b %Y"),
        "=" * width,
        f"{r.drug.name} {s.describe()}",
        f"Give {fmt(r.ml_per_dose)} mL by mouth {freq} for {days}",
        "-" * width,
        f"Quantity: {r.bottles} × {fmt(s.bottle)} mL   Prepared: {today:%d %b %Y}   Use before: {use_before}",
        "-" * width,
        " | ".join(tags),
        "Dose Lab by WaadAlwagdani · © 2026 Waad Alwagdani, PharmD",
    ]
    return "\n".join(rows)
