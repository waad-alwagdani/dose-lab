# Dose Lab by WaadAlwagdani
# © 2026 Waad Alwagdani, PharmD (وعد الوقداني) · waadnalwagdani@gmail.com
# All rights reserved. Not to be copied, reused or redistributed without written permission.

"""HTML rendering for the Streamlit readout: syringe, gauge, metrics, check, formula, label.
Matches the visual identity of the Dose Lab web edition."""

from __future__ import annotations

import base64
import html
import random
from datetime import date, timedelta

from doselab.checks.base import fmt
from doselab.label import FREQ_TEXT

FONTS = ("https://fonts.googleapis.com/css2?family=Readex+Pro:wght@200;300;400;500"
         "&family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap")

TOKENS = """
:root{--bg:#fff;--paper:#fcfbfe;--well:#f7f5fc;--ink:#16131f;--ink2:#575366;--ink3:#9893a8;--hair:#ebe8f2;--hair2:#dcd8e8;
--violet:#6b4fe0;--violet-soft:#f1edff;--green:#1e9e6e;--green-soft:#e9f7f1;--ok:#1e9e6e;--okbg:#eef8f3;--low:#a87508;--lowbg:#fbf5e6;
--high:#c8443a;--highbg:#fcf0ee;--f-display:"Readex Pro","IBM Plex Sans Arabic",system-ui,sans-serif;
--f-body:"IBM Plex Sans Arabic",system-ui,-apple-system,"Segoe UI",sans-serif;--f-mono:"JetBrains Mono",ui-monospace,Menlo,monospace;
--ease:cubic-bezier(.22,.8,.24,1)}
"""

# ---------- page-level CSS injected into Streamlit ----------
APP_CSS = f"""<style>
@import url("{FONTS}");
/* Dose Lab by WaadAlwagdani */
{TOKENS}
html,body,[class*="css"],.stApp{{font-family:var(--f-body)!important;color:var(--ink)}}
.stApp{{background:#fff}}
header[data-testid="stHeader"]{{background:transparent}}
.block-container{{max-width:1180px;padding-top:1.6rem}}
.dl-bar{{display:flex;justify-content:space-between;align-items:center;padding-bottom:16px;border-bottom:1px solid var(--hair);margin-bottom:34px}}
.dl-mark{{display:flex;align-items:center;gap:10px;font-family:var(--f-display);font-weight:500;font-size:15px}}
.dl-mark span{{color:var(--ink3);font-weight:300}} .dl-mark small{{font-family:var(--f-mono);font-size:10.5px;color:var(--violet)}}
.dl-bar nav{{display:flex;gap:18px;font-size:12px;color:var(--ink3)}} .dl-bar nav b{{color:var(--ink);font-family:var(--f-mono)}}
.dl-hero{{display:grid;grid-template-columns:1.2fr .8fr;gap:40px;align-items:end;margin-bottom:34px}}
@media(max-width:820px){{.dl-hero{{grid-template-columns:1fr;gap:16px}}}}
.dl-hero h1{{margin:0;padding:0;font-family:var(--f-display)!important;font-weight:300!important;font-size:clamp(34px,5vw,56px)!important;line-height:1.12!important;letter-spacing:-.015em}}
.dl-hero h1 em{{font-style:normal;color:var(--violet)}}
.dl-hero p{{margin:0;color:var(--ink2);font-size:14.5px;line-height:1.7}}
.dl-flow{{display:flex;flex-wrap:wrap;margin-top:18px;font-size:12px;color:var(--ink2)}}
.dl-flow span{{display:flex;align-items:center;gap:8px;padding-inline-end:14px}}
.dl-flow span+span::before{{content:"";width:18px;height:1px;background:var(--hair2);margin-inline-end:6px}}
.dl-flow b{{font-family:var(--f-mono);font-size:10px;color:var(--violet);background:var(--violet-soft);width:20px;height:20px;display:grid;place-items:center;border-radius:50%}}
h3{{font-family:var(--f-display)!important;font-weight:400!important;font-size:17px!important}}
/* form card */
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div .dl-formcard){{border:1px solid var(--hair)!important;border-radius:14px!important;padding:8px 10px}}
label,[data-testid="stWidgetLabel"] p{{font-size:12px!important;font-weight:500!important;color:var(--ink2)!important}}
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div,input{{border-radius:9px!important;border-color:var(--hair2)!important;background:#fff!important}}
div[data-baseweb="select"]>div:focus-within,div[data-baseweb="input"]>div:focus-within{{border-color:var(--violet)!important;box-shadow:0 0 0 4px var(--violet-soft)!important}}
input[type=number]{{font-family:var(--f-mono)!important}}
.stButton>button,.stDownloadButton>button,.stFormSubmitButton>button{{border-radius:10px;height:46px;font-weight:500;border:0;background:var(--well);color:var(--ink2)}}
.stButton>button[kind="primary"]{{background:var(--violet);color:#fff;box-shadow:0 6px 18px -8px rgba(107,79,224,.55)}}
div[data-testid="stExpander"]{{border:1px dashed var(--hair2);border-radius:10px}}
div[role="radiogroup"] label p{{font-size:13px!important;color:var(--ink)!important}}
/* force the light Dose Lab look even when Streamlit runs in dark mode or without config.toml */
.stApp,.stApp p,.stApp span,.stApp div{{color-scheme:light}}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],section.main{{background:#fff!important;color:var(--ink)!important}}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] h3,[data-testid="stWidgetLabel"] p,.stRadio label p{{color:var(--ink)!important}}
[data-testid="stWidgetLabel"] p{{color:var(--ink2)!important}}
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div,div[data-baseweb="base-input"],
div[data-baseweb="input"] input,div[data-baseweb="select"] input,[data-testid="stNumberInputContainer"]{{background:#fff!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important;border-color:var(--hair2)!important}}
div[data-baseweb="select"] div[class*="ValueContainer"] *,div[data-baseweb="select"] span,div[data-baseweb="select"] div{{color:var(--ink)!important}}
div[data-baseweb="select"] svg,[data-testid="stNumberInputContainer"] svg{{fill:var(--ink2)!important;color:var(--ink2)!important}}
[data-testid="stNumberInputStepDown"],[data-testid="stNumberInputStepUp"],div[data-baseweb="select"]>div>div:last-child{{background:#fff!important;color:var(--ink2)!important}}
ul[role="listbox"],div[data-baseweb="popover"] ul,div[data-baseweb="menu"]{{background:#fff!important}}
ul[role="listbox"] li,div[data-baseweb="popover"] li{{color:var(--ink)!important;background:#fff!important}}
ul[role="listbox"] li:hover,ul[role="listbox"] li[aria-selected="true"]{{background:var(--violet-soft)!important}}
.stRadio div[role="radiogroup"] label>div:first-child{{background:#fff!important;border:1.5px solid var(--hair2)!important}}
.stRadio div[role="radiogroup"] label:has(input:checked)>div:first-child{{border:5px solid var(--violet)!important}}
.stRadio div[role="radiogroup"] label>div:first-child>div{{background:transparent!important}}
[data-testid="stSlider"] div[role="slider"]{{background:var(--violet)!important;border-color:var(--violet)!important;box-shadow:none!important}}
[data-testid="stSlider"] [data-testid="stSliderThumbValue"]{{color:var(--violet)!important}}
[data-testid="stSlider"] div[data-baseweb="slider"]>div>div{{background:linear-gradient(to right,var(--violet) 0%,var(--violet) var(--p,0%),var(--hair) var(--p,0%))}}
[data-testid="stSliderTickBar"]{{color:var(--ink3)!important}}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary *{{color:var(--ink)!important;background:#fff!important}}
[data-testid="stExpander"] details{{background:#fff!important}}
.stButton>button,.stDownloadButton>button{{color:var(--ink2)!important}}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"],.stFormSubmitButton>button{{background:var(--violet)!important;color:#fff!important}}
div[data-testid="stVerticalBlockBorderWrapper"]{{background:#fff!important;border-color:var(--hair)!important}}
[data-testid="stTextInput"] div[data-baseweb="input"],[data-testid="stTextInput"] div[data-baseweb="base-input"],[data-testid="stTextInputRootElement"]{{background:#fff!important;border:1px solid var(--hair2)!important;border-radius:9px!important;box-shadow:none!important}}
[data-testid="stTextInput"] input{{background:#fff!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important}}
[data-testid="stTextInputRootElement"]:focus-within{{border-color:var(--violet)!important;box-shadow:0 0 0 4px var(--violet-soft)!important}}
[data-testid="stNumberInputContainer"],[data-testid="stNumberInput"] div[data-baseweb="input"]{{border:1px solid var(--hair2)!important;border-radius:9px!important}}
.react-aria-ComboBox>div{{background:#fff!important;border:1px solid var(--hair2)!important;border-radius:9px!important}}
.react-aria-ComboBox input{{background:#fff!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important}}
.react-aria-ComboBox button,.react-aria-ComboBox button svg{{color:var(--ink2)!important;fill:var(--ink2)!important;background:transparent!important}}
.dl-box{{padding:14px 16px;border-radius:10px;font-size:12.5px;line-height:1.85;color:var(--ink2);margin:4px 0 6px}}
.dl-box.v{{background:var(--violet-soft);border:1px solid #e2dbfb}} .dl-box.g{{background:var(--green-soft);border:1px solid #d3eee2}}
.dl-box strong{{display:block;color:var(--ink);font-weight:500;font-size:13px}}
.dl-foot{{margin-top:36px;padding-top:18px;border-top:1px solid var(--hair);display:flex;justify-content:space-between;gap:12px 32px;flex-wrap:wrap}}
.dl-foot b{{font-family:var(--f-display);font-weight:500}} .dl-foot span{{display:block;font-family:var(--f-mono);font-size:11px;color:var(--violet)}}
.dl-foot p{{margin:0;font-size:11.5px;color:var(--ink3);max-width:60ch;line-height:1.8}}
</style>
"""

LOGO = ('<svg width="26" height="26" viewBox="0 0 26 26"><rect x="1" y="1" width="24" height="24" rx="7" fill="#6b4fe0"/>'
        '<rect x="6" y="11" width="11" height="4" rx="1" fill="#fff"/><rect x="17" y="12" width="3.5" height="2" fill="#fff" opacity=".7"/>'
        '<rect x="6" y="11" width="5" height="4" rx="1" fill="#1e9e6e"/></svg>')

LOGO_IMG = f'<img width="26" height="26" alt="" src="data:image/svg+xml;base64,{base64.b64encode(LOGO.replace("<svg ", "<svg xmlns=\'http://www.w3.org/2000/svg\' ").encode()).decode()}">'

HEADER = f"""
<div class="dl-bar"><div class="dl-mark">{LOGO_IMG}Dose<span>Lab</span><small>by WaadAlwagdani</small></div>
<nav><span>Built-in strengths <b>15</b></span><span>Dose checks <b>7</b></span></nav></div>
<div class="dl-hero"><h1>Oral Suspension<br><em>Dispensing Calculator</em></h1>
<div><p>Converts the prescribed dose to mL, counts bottles against the in-use shelf life, and checks pediatric doses by weight for seven drugs.</p>
<div class="dl-flow"><span><b>1</b>Prescription</span><span><b>2</b>Conversion</span><span><b>3</b>Check</span><span><b>4</b>Label</span></div></div></div>
"""

FOOTER = """<div class="dl-foot"><div><b>Dose Lab by WaadAlwagdani</b><span>Waad Alwagdani, PharmD · وعد الوقداني</span>
<span style="color:#575366">waadnalwagdani@gmail.com</span></div>
<p>A dispensing support tool; it does not replace the prescriber's decision or an approved clinical reference.
The concept, clinical logic, design and code are the author's own work. © 2026 All rights reserved.</p></div>"""

# ---------- readout component ----------
READ_CSS = TOKENS + """
*{box-sizing:border-box}body{margin:0;font-family:var(--f-body);color:var(--ink);background:transparent;font-size:14px;line-height:1.7}
.inst{border:1px solid var(--hair);border-radius:14px;background:var(--paper);overflow:hidden}
.head{display:flex;justify-content:space-between;align-items:baseline;padding:18px 22px 0}
.head h2{margin:0;font-family:var(--f-display);font-weight:400;font-size:17px}.head small{font-size:12px;color:var(--ink3)}
.hero{padding:12px 22px 4px}.row{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap}
.lbl{font-size:12px;color:var(--ink3)}
.ml{font-family:var(--f-display);font-weight:200;font-size:68px;line-height:1;letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.side{display:flex;gap:22px}.side small{display:block;font-size:11px;color:var(--ink3)}
.side strong{font-family:var(--f-mono);font-weight:500;font-size:14px}.side .bt{font-size:22px;color:var(--green)}
svg.syr{width:100%;height:auto;display:block;margin-top:8px}
#liq{transform-box:fill-box;transform-origin:left center;animation:fill 1.6s var(--ease) both}
#pl{animation:pull 1.6s var(--ease) both}
@keyframes fill{from{transform:scaleX(0)}to{transform:scaleX(var(--sx))}}
@keyframes pull{from{transform:translateX(0)}to{transform:translateX(var(--tx))}}
.tip{animation:show .4s .9s both}@keyframes show{from{opacity:0}}
.cap{font-family:var(--f-mono);font-size:10.5px;color:var(--ink3);text-align:center;margin:-2px 0 12px}
.gauge{padding:16px 22px 14px;border-top:1px solid var(--hair);background:#fff}
.gt{display:flex;justify-content:space-between;gap:10px;margin-bottom:12px;font-size:12px;color:var(--ink2)}
.gt b{font-family:var(--f-mono);font-weight:500}
.track{position:relative;height:26px}.rail{position:absolute;left:0;right:0;top:11px;height:4px;border-radius:4px;background:var(--hair)}
.zone{position:absolute;top:11px;height:4px;border-radius:4px;background:var(--green);opacity:.35}
.needle{position:absolute;top:4px;width:18px;height:18px;margin-left:-9px;border-radius:50%;background:#fff;border:2px solid var(--ink);animation:needle 1s cubic-bezier(.3,1.3,.4,1) both}
@keyframes needle{from{left:0}}
.ok .needle{border-color:var(--ok)}.low .needle{border-color:var(--low)}.high .needle{border-color:var(--high)}
.ok .gt b{color:var(--ok)}.low .gt b{color:var(--low)}.high .gt b{color:var(--high)}
.scale{display:flex;justify-content:space-between;font-family:var(--f-mono);font-size:10px;color:var(--ink3);margin-top:4px}
.metrics{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--hair)}
.m{padding:12px 22px;border-bottom:1px solid var(--hair)}.m:nth-child(odd){border-right:1px solid var(--hair)}
.m span{display:block;font-size:11.5px;color:var(--ink3)}.m strong{font-family:var(--f-mono);font-weight:500;font-size:14px}
.check{margin:16px 22px 0;padding:13px 15px;border-radius:10px;font-size:12.5px;line-height:1.9}
.check b{font-weight:600}.check.ok{background:var(--okbg);color:#14593f}.check.low{background:var(--lowbg);color:#6e4d05}.check.high{background:var(--highbg);color:#8a2b24}
.formula{margin:16px 22px 0;padding:12px 14px;font-family:var(--f-mono);font-size:11px;line-height:2;color:var(--ink2);background:#fff;border:1px solid var(--hair);border-radius:10px;overflow-x:auto;white-space:nowrap}
.warn{margin:16px 22px 22px;padding:12px 15px;font-size:12px;line-height:1.85;color:#7c3a33;background:var(--highbg);border-radius:10px}
.warn div+div{margin-top:4px}
.rx{position:relative;background:#fff;border-radius:6px;padding:18px 20px 14px;margin:18px 2px 6px;box-shadow:0 1px 2px rgba(22,19,31,.06),0 12px 30px -14px rgba(22,19,31,.18);animation:print .7s .3s var(--ease) both}
.rx::before,.rx::after{content:"";position:absolute;left:10px;right:10px;height:6px;background:radial-gradient(circle,#fff 2.4px,transparent 2.6px) 0 0/10px 6px repeat-x}
.rx::before{top:-3px;background:radial-gradient(circle,#f3f1f8 2.4px,transparent 2.6px) 0 0/10px 6px repeat-x}.rx::after{bottom:-3px;background:radial-gradient(circle,#f3f1f8 2.4px,transparent 2.6px) 0 0/10px 6px repeat-x}
@keyframes print{from{opacity:0;clip-path:inset(0 0 100% 0);transform:translateY(-8px)}to{opacity:1;clip-path:inset(0 0 0 0)}}
.lt{display:flex;justify-content:space-between;padding-bottom:10px;border-bottom:1.5px solid var(--ink)}.lt b{font-size:11px;font-weight:600}
.lt span{font-family:var(--f-mono);font-size:10px;color:var(--ink3)}
.ld{font-family:var(--f-display);font-size:18px;font-weight:500;margin:10px 0 2px}
.ls{font-size:15px;margin:6px 0 12px}.ls b{font-family:var(--f-mono);font-weight:500;background:var(--violet-soft);color:var(--violet);padding:0 6px;border-radius:4px}
.lg{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;font-size:11px;color:var(--ink3);padding:10px 0;border-top:1px dashed var(--hair2);border-bottom:1px dashed var(--hair2)}
.lg strong{display:block;color:var(--ink);font-family:var(--f-mono);font-weight:500;font-size:12.5px}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:11px}.tags span{font-size:10.5px;font-weight:500;padding:3px 9px;border-radius:3px;background:var(--ink);color:#fff}
.tags .g{background:var(--green)}.tags .r{background:var(--high)}
.lf{display:flex;justify-content:space-between;align-items:flex-end;margin-top:12px}.bc{height:26px;display:flex;gap:1px}.bc i{background:var(--ink)}
.lf small,.cr{font-family:var(--f-mono);font-size:9.5px;color:var(--ink3)}.cr{margin-top:8px;font-size:8.5px;letter-spacing:.04em}
@media(prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def _syringe(ml: float) -> str:
    caps = [1, 3, 5, 10, 20, 30, 60]
    cap = next((c for c in caps if c >= ml), 60)
    minor = {1: .05, 3: .1, 5: .2, 10: .5, 20: 1, 30: 1, 60: 2}[cap]
    major = {1: .2, 3: .5, 5: 1, 10: 1, 20: 5, 30: 5, 60: 10}[cap]
    W, X0 = 262, 40
    ticks = []
    for i in range(round(cap / minor) + 1):
        v = i * minor
        x = X0 + (W - 15) * v / cap
        is_major = abs(v / major - round(v / major)) < 1e-6
        mid = not is_major and abs(v / (major / 2) - round(v / (major / 2))) < 1e-6
        ticks.append(f'<line x1="{x:.2f}" x2="{x:.2f}" y1="75" y2="{63 if is_major else 67 if mid else 70}" '
                     f'stroke="#4a4560" stroke-width="{.9 if is_major else .55}" opacity="{.8 if is_major else .55}"/>')
        if is_major:
            ticks.append(f'<text x="{x:.2f}" y="92" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="8.5" fill="#575366">{v:g}</text>')
    travel = (W - 15) * min(ml / cap, 1)
    note = f"{cap} mL oral syringe" + (f" · draw {-(-ml // cap):.0f}×" if ml > cap else "")
    return f"""
<svg class="syr" viewBox="0 0 600 104" style="--sx:{travel / W:.4f};--tx:{travel:.2f}px">
<defs><linearGradient id="gl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/><stop offset=".45" stop-color="#f6f4fb"/><stop offset=".8" stop-color="#eeebf6"/><stop offset="1" stop-color="#fbfaff"/></linearGradient>
<linearGradient id="lq" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8e75f0"/><stop offset=".55" stop-color="#6b4fe0"/><stop offset="1" stop-color="#5a3fcf"/></linearGradient>
<linearGradient id="rb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3b3450"/><stop offset=".5" stop-color="#211c2e"/><stop offset="1" stop-color="#3b3450"/></linearGradient>
<linearGradient id="rd" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f3f1f8"/><stop offset=".5" stop-color="#dcd7e8"/><stop offset="1" stop-color="#ece9f3"/></linearGradient>
<clipPath id="bc"><rect x="40" y="35" width="262" height="40" rx="5"/></clipPath><clipPath id="tc"><path d="M8 50 Q8 47 11 47 L40 45 L40 65 L11 63 Q8 63 8 60 Z"/></clipPath></defs>
<g id="pl"><rect x="54" y="50" width="282" height="10" rx="1.5" fill="url(#rd)"/><rect x="54" y="54.4" width="282" height="1.2" fill="#c9c3da"/>
<rect x="334" y="30" width="7" height="50" rx="3" fill="url(#rd)" stroke="#cfc9de" stroke-width=".8"/>
<g clip-path="url(#bc)"><rect x="40" y="35" width="15" height="40" fill="url(#rb)"/><rect x="43.5" y="35" width="1.3" height="40" fill="#5a5270"/><rect x="48.5" y="35" width="1.3" height="40" fill="#5a5270"/></g></g>
<path d="M8 50 Q8 47 11 47 L40 45 L40 65 L11 63 Q8 63 8 60 Z" fill="url(#gl)" stroke="#cdc6e0"/>
<rect class="tip" x="8" y="49.5" width="32" height="11" fill="url(#lq)" clip-path="url(#tc)"/>
<rect x="40" y="35" width="262" height="40" rx="5" fill="url(#gl)" opacity=".55"/>
<g clip-path="url(#bc)"><rect id="liq" x="40" y="35" width="262" height="40" fill="url(#lq)" opacity=".9"/>
<g class="tip" fill="#fff"><circle cx="70" cy="44" r="1.6" opacity=".7"/><circle cx="92" cy="47" r="1" opacity=".6"/></g></g>
<rect x="40" y="38" width="262" height="3" rx="1.5" fill="#fff" opacity=".7"/>
<rect x="40" y="35" width="262" height="40" rx="5" fill="none" stroke="#c4bcdb" stroke-width="1.1"/>
{''.join(ticks)}<text x="320" y="92" font-family="JetBrains Mono,monospace" font-size="8.5" fill="#9893a8">mL</text>
<rect x="300" y="24" width="9" height="62" rx="3.5" fill="url(#gl)" stroke="#c4bcdb" stroke-width="1.1"/></svg>
<div class="cap">{note}</div>"""


def _gauge(check) -> str:
    if not check or not check.gauge:
        return ""
    v, lo, hi, unit = check.gauge
    mx = max(hi * 1.6, lo * 2.5, v * 1.1)
    p = lambda x: max(0, min(100, x / mx * 100))
    return (f'<div class="gauge {check.status.value}"><div class="gt"><span>Prescribed dose vs reference range</span>'
            f'<b>{fmt(v)} {html.escape(unit)}</b></div><div class="track"><div class="rail"></div>'
            f'<div class="zone" style="left:{p(lo):.1f}%;width:{p(hi) - p(lo):.1f}%"></div>'
            f'<div class="needle" style="left:{p(v):.1f}%"></div></div>'
            f'<div class="scale"><span>0</span><span>{fmt(lo)}</span><span>{fmt(hi)}</span><span>{fmt(mx, 0)}</span></div></div>')


def _label(r) -> str:
    today = date.today()
    s, rx = r.strength, r.prescription
    freq = FREQ_TEXT.get(rx.frequency, f"{fmt(rx.frequency)} times daily")
    days = "1 day" if rx.duration_days == 1 else f"{fmt(rx.duration_days)} days"
    exp = (today + timedelta(days=s.shelf_days)).strftime("%d %b %Y") if s.shelf_days else "—"
    tags = ['<span>Shake well before use</span>', '<span class="g">By mouth</span>']
    if rx.drug_id == "augmentin":
        tags.append("<span>Refrigerate after reconstitution</span>")
    if s.shelf_days and rx.duration_days > s.shelf_days:
        tags.append('<span class="r">Course exceeds in-use shelf life</span>')
    rnd = random.Random(f"{r.drug.id}{r.ml_per_dose}{rx.frequency}")
    bars = "".join(f'<i style="width:{rnd.randint(1, 3)}px"></i>' for _ in range(46))
    d = today.strftime("%d %b %Y")
    return (f'<div class="rx"><div class="lt"><b>Pharmacy ▪ Dispensing label</b><span>{d}</span></div>'
            f'<div class="ld">{html.escape(r.drug.name)} {html.escape(s.describe())}</div>'
            f'<div class="ls">Give <b>{fmt(r.ml_per_dose)} mL</b> by mouth {freq} for {days}</div>'
            f'<div class="lg"><div>Quantity<strong>{r.bottles} × {fmt(s.bottle)} mL</strong></div>'
            f'<div>Prepared<strong>{d}</strong></div><div>Use before<strong>{exp}</strong></div></div>'
            f'<div class="tags">{"".join(tags)}</div><div class="lf"><div class="bc">{bars}</div>'
            f'<small>RX-{rnd.randint(100000, 999999)}</small></div>'
            f'<div class="cr">Dose Lab by WaadAlwagdani · © 2026 Waad Alwagdani, PharmD</div></div>')


def readout_html(r) -> str:
    c = r.check
    check = ""
    if c:
        check = (f'<div class="check {c.status.value}"><b>{html.escape(c.title)}</b><br>'
                 + "<br>".join(html.escape(x) for x in c.lines) + "</div>")
    metrics = [("Daily total", f"{fmt(r.daily_ml)} mL/day"), ("Course total", f"{fmt(r.total_ml)} mL"),
               ("Dispensed volume", f"{fmt(r.dispensed_ml)} mL"), ("Dose per administration", f"{fmt(r.mg_per_dose)} mg")]
    if "amox_per_dose_mg" in r.extra:
        metrics += [("Amoxicillin / dose", f"{fmt(r.extra['amox_per_dose_mg'])} mg"),
                    ("Clavulanate / dose", f"{fmt(r.extra['clav_per_dose_mg'])} mg")]
    warn = ("".join(f"<div>• {html.escape(w)}</div>" for w in r.warnings)) if r.warnings else ""
    return f"""<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{FONTS}">
<style>/* Dose Lab by WaadAlwagdani */{READ_CSS}</style></head><body>
<div class="inst"><div class="head"><h2>Readout</h2><small>{html.escape(r.drug.name)} · {html.escape(r.strength.describe())}</small></div>
<div class="hero"><div class="row"><div><div class="lbl">Volume per dose</div><div class="ml">{fmt(r.ml_per_dose)} mL</div></div>
<div class="side"><div><small>Dose</small><strong>{fmt(r.mg_per_dose)} mg</strong></div><div><small>Bottles</small><strong class="bt">{r.bottles}</strong></div></div></div>
{_syringe(r.ml_per_dose)}</div>{_gauge(c)}
<div class="metrics">{''.join(f'<div class="m"><span>{a}</span><strong>{b}</strong></div>' for a, b in metrics)}</div>
{check}<div class="formula">{'<br>'.join(html.escape(x) for x in r.formula)}</div>
{f'<div class="warn">{warn}</div>' if warn else '<div style="height:22px"></div>'}</div>
{_label(r)}</body></html>"""


def readout_height(r) -> int:
    h = 920 + 24 * len(r.formula) + sum(26 * (1 + len(w) // 70) for w in r.warnings)
    if r.check:
        h += 50 + sum(26 * (1 + len(x) // 70) for x in r.check.lines)
    if "amox_per_dose_mg" in r.extra:
        h += 60
    return h
