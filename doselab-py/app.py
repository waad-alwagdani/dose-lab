# Dose Lab by WaadAlwagdani
# © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com
# All rights reserved. Not to be copied, reused or redistributed without written permission.

"""Streamlit web interface for Dose Lab.  Run:  streamlit run app.py"""

import streamlit as st

from doselab import CATALOG, Patient, Prescription, calculate, storage
from doselab.catalog import DEFAULT_KG_DAY
from doselab.label import make_label
from doselab.label_pdf import make_label_pdf
from doselab.models import DoseMode, Strength
from ui_render import APP_CSS, FOOTER, HEADER, readout_height, readout_html

st.set_page_config(page_title="Dose Lab by WaadAlwagdani", page_icon="💊", layout="wide",
                   menu_items={"About": "Dose Lab by WaadAlwagdani · © 2026 Waad Alwagdani, PharmD. All rights reserved."})
st.html(APP_CSS)
st.html(HEADER)

BOXES = {
    "paracetamol": ("g", "Paracetamol dose check", "10–15 mg/kg per dose every 4–6 h, max 4 doses/24 h. Daily limit 60 mg/kg/day for neonates and infants; children usual 60, max 75 mg/kg/day, cap 4 g, single dose up to 750 mg; ≥12 y and ≥50 kg 500–1,000 mg per dose."),
    "ibuprofen": ("g", "Ibuprofen dose check", "6 months–11 years and <50 kg: 5–10 mg/kg every 6–8 h, max 400 mg per dose and 40 mg/kg/day (cap 2,400 mg). ≥12 y or ≥50 kg: 200–800 mg; 1,200 mg/day OTC, 3,200 mg/day Rx. Not under 6 months."),
    "augmentin": ("v", "Augmentin dose check", "Checked on the amoxicillin component against q8h (4:1), q12h (7:1), high-dose ES (14:1) or infant references; the selected strength's ratio is matched to the regimen."),
    "azithromycin": ("v", "Azithromycin dose check", "Once daily by actual weight; ≥45 kg uses the fixed adult dose. Under 6 months the dose is individualized."),
    "depakine": ("v", "Depakine dose check", "Start 10–15 mg/kg/day, titrate by 5–10 weekly, max 60 mg/kg/day and 3,000 mg/day, single dose up to 1,000 mg. Syrup in 2–3 doses daily."),
    "levetiracetam": ("v", "Levetiracetam dose check", "Children <50 kg: start 20 mg/kg/day q12h, titrate to 40–60. Limit 60 mg/kg/day (6 months–3 years: 50), cap 3,000 mg/day. ≥16 y or ≥50 kg: 500–3,000 mg/day."),
    "cefuroxime": ("v", "Cefuroxime dose check", "Oral suspension, 3 months–12 years and <40 kg, by weight q12h, max 500 mg per dose. ≥13 y or ≥40 kg: 250–500 mg q12h, max 1,000 mg/day. Give with food."),
}

left, right = st.columns([1, 1], gap="large")
with left:
    with st.container(border=True):
        st.markdown('<span class="dl-formcard"></span>', unsafe_allow_html=True)
        st.markdown("### Prescription details")
        drug_id = st.selectbox("Drug", list(CATALOG), index=list(CATALOG).index("paracetamol"),
                               format_func=lambda k: CATALOG[k].name)
        strengths = CATALOG[drug_id].strengths + storage.load_custom_strengths().get(drug_id, [])
        a, b = st.columns([2, 1])
        s = a.selectbox("Strength", strengths, format_func=lambda x: x.describe() + (" — added" if x.custom else ""))
        bottle = b.number_input("Bottle size (mL)", min_value=1.0, value=float(s.bottle), key=f"bottle_{drug_id}_{s.describe()}")
        s = Strength(s.mg, s.vol, bottle, s.shelf_days, s.amox_mg, s.clav_mg, s.label, s.custom)

        if drug_id in BOXES:
            tone, title, text = BOXES[drug_id]
            st.markdown(f'<div class="dl-box {tone}"><strong>{title}</strong>{text}</div>', unsafe_allow_html=True)

        extra = {}
        if drug_id == "azithromycin":
            extra["azithro_regimen"] = st.selectbox("Regimen", ["d3", "d5", "strep", "single"], format_func={
                "d3": "10 mg/kg daily × 3 days (otitis / sinusitis)", "d5": "10 mg/kg day 1, then 5 mg/kg days 2–5",
                "strep": "12 mg/kg daily × 5 days (pharyngitis, ≥2 y)", "single": "30 mg/kg single dose (otitis)"}.get)
            if extra["azithro_regimen"] == "d5":
                extra["azithro_day"] = st.radio("Entered dose is for", ["1", "2"], horizontal=True,
                                                format_func={"1": "Day 1", "2": "Days 2–5"}.get)
        if drug_id == "cefuroxime":
            extra["cef_regimen"] = st.selectbox("Indication", ["aom", "phar"], format_func={
                "aom": "Otitis media / sinusitis: 30 mg/kg/day × 10 days", "phar": "Pharyngitis / tonsillitis: 20 mg/kg/day × 10 days"}.get)

        modes = {"mg per dose": DoseMode.MG_PER_DOSE, "mL per dose": DoseMode.ML_PER_DOSE,
                 "mg/kg per dose": DoseMode.MG_KG_DOSE, "mg/kg/day": DoseMode.MG_KG_DAY}
        mode = modes[st.radio("Dose entered as", list(modes), horizontal=True,
                              index=3 if drug_id in DEFAULT_KG_DAY else 0, key=f"mode_{drug_id}")]
        if drug_id == "augmentin":
            c1, c2 = st.columns(2)
            extra["augmentin_reference"] = c1.selectbox("Reference", ["auto", "q8", "q12", "high", "infant"], format_func={
                "auto": "Automatic by age and frequency", "q8": "Standard q8h: 20–40 mg/kg/day", "q12": "Standard q12h: 25–45 mg/kg/day",
                "high": "High dose q12h: 90 mg/kg/day", "infant": "Under 12 weeks: 30 mg/kg/day"}.get)
            if mode is DoseMode.MG_PER_DOSE:
                extra["augmentin_basis"] = c2.selectbox("Prescribed mg refers to", ["total", "amoxicillin"],
                                                        format_func={"total": "Total product", "amoxicillin": "Amoxicillin component"}.get)

        defaults = {"paracetamol": (150.0, 4, 3, 10.0, 1.0), "depakine": (15.0, 2, 30, 22.0, 6.0),
                    "levetiracetam": (20.0, 2, 30, 16.0, 4.0), "cefuroxime": (30.0, 2, 10, 18.0, 5.0),
                    "azithromycin": (150.0, 1, 3, 15.0, 3.0), "ibuprofen": (100.0, 4, 3, 11.0, 1.5),
                    "augmentin": (156.0, 3, 7, 15.0, 3.0)}
        dd, df, dn, dw, da = defaults.get(drug_id, (5.0 if mode is DoseMode.ML_PER_DOSE else 250.0, 3, 5, 0.0, 0.0))
        c1, c2, c3 = st.columns(3)
        dose = c1.number_input("Dose", min_value=0.0, value=dd, key=f"dose_{drug_id}_{mode.value}")
        freq = c2.number_input("Doses per day", min_value=1, value=df, step=1, key=f"freq_{drug_id}")
        days = c3.number_input("Duration (days)", min_value=1, value=dn, step=1, key=f"days_{drug_id}")
        needs_patient = drug_id in BOXES or mode in (DoseMode.MG_KG_DOSE, DoseMode.MG_KG_DAY)
        weight = age = None
        unit = "years"
        if needs_patient:
            c4, c5, c6 = st.columns(3)
            weight = c4.number_input("Weight (kg)", min_value=0.0, value=dw or 10.0, key=f"w_{drug_id}") or None
            if drug_id in BOXES:
                age = c5.number_input("Age", min_value=0.0, value=da or 1.0, key=f"a_{drug_id}") or None
                unit = c6.selectbox("Age unit", ["years", "months", "days"], key=f"u_{drug_id}")
        rounding = st.select_slider("Round mL per dose to", [0.01, 0.1, 0.25, 0.5, 1.0],
                                    value=0.01 if drug_id == "depakine" else 0.1, key=f"r_{drug_id}")

    with st.expander("＋ Add a strength you stock"):
        with st.form("add", border=False):
            a1, a2 = st.columns(2)
            if drug_id == "augmentin":
                amox, clav = a1.number_input("Amoxicillin mg", 0.0), a2.number_input("Clavulanate mg", 0.0)
                mg_new = amox + clav
            else:
                amox = clav = None
                mg_new = a1.number_input("Active drug mg", 0.0)
            vol_new = a2.number_input("Per volume mL", 0.0, value=5.0)
            b_new = a1.number_input("Bottle size mL", 0.0)
            shelf_new = a2.number_input("In-use shelf life days (0 = none)", 0, step=1)
            if st.form_submit_button("Save strength", type="primary"):
                if mg_new > 0 and vol_new > 0 and b_new > 0:
                    storage.save_custom_strength(drug_id, Strength(mg_new, vol_new, b_new, shelf_new or None, amox, clav))
                    st.rerun()
                else:
                    st.error("Enter the strength, volume and bottle size.")

with right:
    if dose <= 0:
        st.info("Enter a dose to see the readout.")
    else:
        try:
            r = calculate(Prescription(drug_id, s, dose, mode, freq, days, rounding=rounding, **extra),
                          Patient(weight, age, unit))
        except ValueError as e:
            st.error(str(e))
        else:
            page = readout_html(r)
            if hasattr(st, "iframe"):          # Streamlit ≥ 1.50
                st.iframe(page, height=readout_height(r))
            else:                              # older Streamlit
                import streamlit.components.v1 as components
                components.html(page, height=readout_height(r), scrolling=False)
            patient_name = st.text_input("Patient name on label (optional)", key="pname")
            d1, d2 = st.columns(2)
            d1.download_button("Print label (PDF)", make_label_pdf(r, patient_name=patient_name),
                               file_name=f"label_{drug_id}.pdf", mime="application/pdf", type="primary")
            if d2.button("Save to dispensing log"):
                storage.append_log(r)
                st.toast("Saved to the dispensing log")

log = storage.read_log()
if log:
    with st.expander(f"Dispensing log ({len(log)})"):
        st.dataframe(log[::-1], hide_index=True)

st.html(FOOTER)
