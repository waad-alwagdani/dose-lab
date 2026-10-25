# Dose Lab by WaadAlwagdani
# © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com
# All rights reserved. Not to be copied, reused or redistributed without written permission.

"""Streamlit web interface for Dose Lab.  Run:  streamlit run app.py"""

import streamlit as st

from doselab import CATALOG, Patient, Prescription, calculate, storage
from doselab.catalog import DEFAULT_KG_DAY
from doselab.label import make_label
from doselab.models import DoseMode, Strength

st.set_page_config(page_title="Dose Lab by WaadAlwagdani", page_icon="💊", layout="wide",
                   menu_items={"About": "Dose Lab by WaadAlwagdani · © 2026 Waad Alwagdani, PharmD. All rights reserved."})
st.markdown("""<style>
.block-container{padding-top:2rem}
.big{font-size:3.2rem;font-weight:200;line-height:1;color:#16131f}
.chip{display:inline-block;padding:2px 10px;border-radius:20px;font-size:.8rem;font-weight:600}
.ok{background:#eef8f3;color:#1e9e6e}.low{background:#fbf5e6;color:#a87508}.high{background:#fcf0ee;color:#c8443a}
</style>""", unsafe_allow_html=True)

st.title("Oral Suspension Dispensing Calculator")
st.caption("Dose Lab by WaadAlwagdani · © 2026 Waad Alwagdani, PharmD")

left, right = st.columns([1.05, 1], gap="large")
with left:
    st.subheader("Prescription")
    drug_id = st.selectbox("Drug", list(CATALOG), format_func=lambda k: CATALOG[k].name)
    strengths = CATALOG[drug_id].strengths + storage.load_custom_strengths().get(drug_id, [])
    s = st.selectbox("Strength", strengths, format_func=lambda x: x.describe() + (" (added)" if x.custom else ""))
    bottle = st.number_input("Bottle size (mL)", min_value=1.0, value=float(s.bottle))
    s = Strength(s.mg, s.vol, bottle, s.shelf_days, s.amox_mg, s.clav_mg, s.label, s.custom)

    modes = {"mg per dose": DoseMode.MG_PER_DOSE, "mL per dose": DoseMode.ML_PER_DOSE,
             "mg/kg per dose": DoseMode.MG_KG_DOSE, "mg/kg/day": DoseMode.MG_KG_DAY}
    mode = modes[st.radio("Dose entered as", list(modes), index=3 if drug_id in DEFAULT_KG_DAY else 0, horizontal=True)]
    c1, c2, c3 = st.columns(3)
    dose = c1.number_input("Dose", min_value=0.0, value=15.0 if mode is DoseMode.MG_KG_DAY else 0.0)
    freq = c2.number_input("Doses per day", min_value=1.0, value=2.0 if drug_id in DEFAULT_KG_DAY else 1.0 if drug_id == "azithromycin" else 3.0)
    days = c3.number_input("Duration (days)", min_value=0.5, value=5.0)
    c4, c5, c6 = st.columns(3)
    weight = c4.number_input("Weight (kg)", min_value=0.0, value=0.0) or None
    age = c5.number_input("Age", min_value=0.0, value=0.0) or None
    unit = c6.selectbox("Age unit", ["years", "months", "days"])

    extra = {}
    if drug_id == "azithromycin":
        extra["azithro_regimen"] = st.selectbox("Regimen", ["d3", "d5", "strep", "single"], format_func={
            "d3": "10 mg/kg × 3 days", "d5": "10 mg/kg day 1, then 5 mg/kg days 2–5",
            "strep": "12 mg/kg × 5 days (pharyngitis)", "single": "30 mg/kg single dose"}.get)
        if extra["azithro_regimen"] == "d5":
            extra["azithro_day"] = st.radio("Entered dose is for", ["1", "2"], format_func={"1": "Day 1", "2": "Days 2–5"}.get, horizontal=True)
    if drug_id == "cefuroxime":
        extra["cef_regimen"] = st.selectbox("Indication", ["aom", "phar"], format_func={"aom": "Otitis / sinusitis", "phar": "Pharyngitis"}.get)
    if drug_id == "augmentin":
        extra["augmentin_reference"] = st.selectbox("Reference", ["auto", "q8", "q12", "high", "infant"])
        if mode is DoseMode.MG_PER_DOSE:
            extra["augmentin_basis"] = st.radio("Prescribed mg refers to", ["total", "amoxicillin"], horizontal=True)
    rounding = st.select_slider("Round mL to", [0.01, 0.1, 0.25, 0.5, 1.0], value=0.01 if drug_id == "depakine" else 0.1)

    with st.expander("Add a strength you stock"):
        with st.form("add"):
            a1, a2 = st.columns(2)
            if drug_id == "augmentin":
                amox, clav = a1.number_input("Amoxicillin mg", 0.0), a2.number_input("Clavulanate mg", 0.0)
                mg_new = amox + clav
            else:
                amox = clav = None
                mg_new = a1.number_input("Active drug mg", 0.0)
            vol_new = a2.number_input("Per volume mL", 0.0, value=5.0)
            b_new = a1.number_input("Bottle size mL", 0.0)
            shelf_new = a2.number_input("Shelf life days (0 = none)", 0, step=1)
            if st.form_submit_button("Save strength"):
                if mg_new > 0 and vol_new > 0 and b_new > 0:
                    storage.save_custom_strength(drug_id, Strength(mg_new, vol_new, b_new, shelf_new or None, amox, clav))
                    st.success("Saved. Reselect the drug to see it in the list.")
                else:
                    st.error("Enter the strength, volume and bottle size.")

with right:
    st.subheader("Readout")
    if dose <= 0:
        st.info("Enter a dose to calculate.")
        st.stop()
    try:
        r = calculate(Prescription(drug_id, s, dose, mode, freq, days, rounding=rounding, **extra), Patient(weight, age, unit))
    except ValueError as e:
        st.error(str(e))
        st.stop()
    st.markdown(f"<div class='big'>{r.ml_per_dose:g} mL</div><p>per dose · {r.mg_per_dose:g} mg</p>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Daily", f"{r.daily_ml:g} mL")
    m2.metric("Course", f"{r.total_ml:g} mL")
    m3.metric("Bottles", r.bottles)
    st.progress(min(r.ml_per_dose / next(c for c in (1, 3, 5, 10, 20, 30, 60, 1e9) if c >= r.ml_per_dose), 1.0),
                text="Oral syringe fill")
    if r.check:
        st.markdown(f"<span class='chip {r.check.status.value}'>{r.check.title}</span>", unsafe_allow_html=True)
        for line in r.check.lines:
            st.write(line)
    st.code("\n".join(r.formula), language=None)
    for w in r.warnings:
        st.warning(w)
    label = make_label(r)
    st.text(label)
    d1, d2 = st.columns(2)
    d1.download_button("Download label", label, file_name=f"label_{drug_id}.txt")
    if d2.button("Save to dispensing log"):
        storage.append_log(r)
        st.toast("Saved to the dispensing log")

with st.expander("Dispensing log"):
    st.dataframe(storage.read_log()[::-1])

st.divider()
st.caption("Dose Lab by WaadAlwagdani · © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com · "
           "All rights reserved. Not to be copied, reused or redistributed without written permission.")
