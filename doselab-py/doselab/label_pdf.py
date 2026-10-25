# Dose Lab by WaadAlwagdani
# © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com
# All rights reserved. Not to be copied, reused or redistributed without written permission.

"""Printable pharmacy label as a PDF sized for label printers (100 × 70 mm)."""

from __future__ import annotations

import hashlib
import io
from datetime import date, timedelta

from reportlab.graphics.barcode import code128
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .checks.base import fmt
from .label import FREQ_TEXT
from .models import DoseResult

INK, INK3, VIOLET, VIOLET_SOFT, GREEN, RED, HAIR = (HexColor(c) for c in
    ("#16131f", "#9893a8", "#6b4fe0", "#f1edff", "#1e9e6e", "#c8443a", "#dcd8e8"))
SIZE = (100 * mm, 70 * mm)
SIGNATURE = "Dose Lab by WaadAlwagdani · © 2026 Waad Alwagdani, PharmD"


def rx_number(r: DoseResult) -> str:
    key = f"{r.drug.id}|{r.strength.describe()}|{r.ml_per_dose}|{r.prescription.frequency}|{r.prescription.duration_days}"
    return "RX" + str(int(hashlib.sha1(key.encode()).hexdigest(), 16))[:8]


def _fit(c, text, font, size, max_w):
    """Shrink the font until the text fits the width."""
    while size > 5 and c.stringWidth(text, font, size) > max_w:
        size -= 0.25
    return size


def make_label_pdf(r: DoseResult, today: date | None = None, patient_name: str = "") -> bytes:
    today = today or date.today()
    rx, s = r.prescription, r.strength
    W, H = SIZE
    m = 4 * mm
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=SIZE)
    c.setTitle(f"{r.drug.name} label — Dose Lab by WaadAlwagdani")
    c.setAuthor("WaadAlwagdani (Waad Alwagdani, PharmD)")
    c.setCreator("Dose Lab by WaadAlwagdani")
    c.setSubject("Pharmacy dispensing label")

    # header bar
    c.setFillColor(INK)
    c.rect(0, H - 8 * mm, W, 8 * mm, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(m, H - 5.2 * mm, "PHARMACY  |  DISPENSING LABEL")
    c.setFont("Helvetica", 7)
    c.drawRightString(W - m, H - 5.2 * mm, today.strftime("%d %b %Y"))

    y = H - 8 * mm - 5.5 * mm
    if patient_name:
        c.setFillColor(INK3); c.setFont("Helvetica", 6.5)
        c.drawString(m, y + 1.2 * mm, "PATIENT")
        c.setFillColor(INK); c.setFont("Helvetica-Bold", 8)
        c.drawString(m + 13 * mm, y + 1.2 * mm, patient_name[:40])
        y -= 4.2 * mm

    # drug name
    name = f"{r.drug.name} {s.describe()}"
    c.setFillColor(INK)
    size = _fit(c, name, "Helvetica-Bold", 11.5, W - 2 * m)
    c.setFont("Helvetica-Bold", size)
    c.drawString(m, y - 1 * mm, name)

    # directions with highlighted volume
    y -= 7 * mm
    freq = FREQ_TEXT.get(rx.frequency, f"{fmt(rx.frequency)} times daily")
    days = "1 day" if rx.duration_days == 1 else f"{fmt(rx.duration_days)} days"
    vol = f"{fmt(r.ml_per_dose)} mL"
    c.setFont("Helvetica", 9.5)
    x = m
    c.drawString(x, y, "Give")
    x += c.stringWidth("Give ", "Helvetica", 9.5)
    pill_w = c.stringWidth(vol, "Helvetica-Bold", 10) + 3 * mm
    c.setFillColor(VIOLET_SOFT)
    c.roundRect(x, y - 1.4 * mm, pill_w, 5 * mm, 1.2 * mm, stroke=0, fill=1)
    c.setFillColor(VIOLET); c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 1.5 * mm, y, vol)
    x += pill_w + 1.2 * mm
    rest = f"by mouth {freq}"
    c.setFillColor(INK); c.setFont("Helvetica", 9.5)
    c.drawString(x, y, rest)
    y -= 4.8 * mm
    c.drawString(m, y, f"for {days}.")

    # grid
    y -= 3.5 * mm
    c.setStrokeColor(HAIR); c.setDash(1.5, 1.2); c.setLineWidth(0.5)
    c.line(m, y, W - m, y)
    exp = (today + timedelta(days=s.shelf_days)).strftime("%d %b %Y") if s.shelf_days else "—"
    cols = [("QUANTITY", f"{r.bottles} × {fmt(s.bottle)} mL"), ("PREPARED", today.strftime("%d %b %Y")), ("USE BEFORE", exp)]
    cw = (W - 2 * m) / 3
    for i, (k, v) in enumerate(cols):
        cx = m + i * cw
        c.setFillColor(INK3); c.setFont("Helvetica", 5.8); c.drawString(cx, y - 3.2 * mm, k)
        c.setFillColor(INK); c.setFont("Helvetica-Bold", 8); c.drawString(cx, y - 6.8 * mm, v)
    y -= 8.8 * mm
    c.line(m, y, W - m, y)
    c.setDash()

    # warning tags
    tags = [("SHAKE WELL BEFORE USE", INK), ("BY MOUTH", GREEN)]
    if rx.drug_id == "augmentin" or s.shelf_days:
        tags.append(("REFRIGERATE AFTER MIXING" if rx.drug_id in ("augmentin", "cefuroxime") else "CHECK STORAGE", INK))
    if s.shelf_days and rx.duration_days > s.shelf_days:
        tags.append(("COURSE EXCEEDS SHELF LIFE", RED))
    tx, ty = m, y - 5 * mm
    for text, col in tags:
        w = c.stringWidth(text, "Helvetica-Bold", 5.6) + 3 * mm
        if tx + w > W - m:
            tx, ty = m, ty - 4.6 * mm
        c.setFillColor(col); c.roundRect(tx, ty - 1 * mm, w, 3.8 * mm, 0.6 * mm, stroke=0, fill=1)
        c.setFillColor(white); c.setFont("Helvetica-Bold", 5.6); c.drawString(tx + 1.5 * mm, ty + 0.2 * mm, text)
        tx += w + 1.5 * mm

    # barcode + rx number + signature
    num = rx_number(r)
    c.setFillColor(INK)
    bc = code128.Code128(num, barHeight=7 * mm, barWidth=0.62)
    bc.drawOn(c, m - 2.2 * mm, 5.2 * mm)
    c.setFillColor(INK3); c.setFont("Courier", 6)
    c.drawRightString(W - m, 9 * mm, num)
    c.setFont("Helvetica", 4.8)
    c.drawRightString(W - m, 2.4 * mm, SIGNATURE)
    c.showPage()
    c.save()
    return buf.getvalue()
