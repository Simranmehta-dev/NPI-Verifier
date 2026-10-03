"""Builds the results card (stats + copyable table) as plain HTML. No Panel needed, so it is easy to test."""
from __future__ import annotations

from html import escape

import pandas as pd

STATUS_LABELS = {
    "verified": "Verified",
    "name_mismatch": "Name mismatch",
    "not_found": "Not found",
    "invalid_format": "Invalid format",
    "lookup_error": "Lookup error",
}

# Runs in the browser when the button is clicked. Copies only cells that are not marked "nocopy",
# as tab separated text, so it pastes straight into Excel or Google Sheets.
_COPY_JS = (
    "const root=this.closest('.npi-card');"
    "const text=[...root.querySelectorAll('tr')].map(tr=>"
    "[...tr.children].filter(c=>!c.classList.contains('nocopy'))"
    ".map(c=>c.innerText.trim()).join('\\t')).join('\\n');"
    "const btn=this;const label=btn.innerText;"
    "const done=()=>{btn.innerText='Copied';setTimeout(()=>{btn.innerText=label},1500)};"
    "if(navigator.clipboard){navigator.clipboard.writeText(text).then(done)}"
    "else{const t=document.createElement('textarea');t.value=text;document.body.appendChild(t);"
    "t.select();document.execCommand('copy');t.remove();done()}"
)

CSS = """
<style>
.npi-card{font-family:Inter,'Segoe UI',system-ui,sans-serif;background:#fff;border:1px solid #e7e9f0;
  border-radius:16px;box-shadow:0 6px 24px rgba(30,41,90,.06);padding:22px 24px;color:#1f2540}
.npi-head{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:18px}
.npi-stats{display:flex;gap:10px;flex-wrap:wrap}
.npi-chip{background:#f4f5fb;border-radius:12px;padding:8px 14px;min-width:92px}
.npi-chip b{display:block;font-size:22px;line-height:1.2}
.npi-chip span{font-size:12px;color:#6b7194;letter-spacing:.02em}
.npi-chip.good b{color:#0f9d6b}.npi-chip.warn b{color:#d9480f}
.npi-copy{background:#4f46e5;color:#fff;border:0;border-radius:10px;padding:9px 16px;font-size:13px;
  font-weight:600;cursor:pointer;transition:background .15s}
.npi-copy:hover{background:#4338ca}
.npi-wrap{max-height:62vh;overflow:auto;border-radius:12px;border:1px solid #eceef6}
.npi-table{border-collapse:collapse;width:100%;font-size:14px}
.npi-table th{position:sticky;top:0;background:#f7f8fd;text-align:left;font-size:12px;color:#6b7194;
  text-transform:uppercase;letter-spacing:.05em;padding:11px 14px;border-bottom:1px solid #eceef6}
.npi-table td{padding:11px 14px;border-bottom:1px solid #f1f2f8}
.npi-table tr:hover td{background:#fafaff}
.npi-table .mono{font-family:Consolas,'SFMono-Regular',monospace;letter-spacing:.03em}
.npi-table .muted{color:#a2a7c2}
.npi-badge{display:inline-block;border-radius:999px;padding:3px 10px;font-size:12px;font-weight:600}
.b-verified{background:#e3f7ee;color:#0b7a53}.b-name_mismatch{background:#fff0e0;color:#b4540a}
.b-not_found,.b-invalid_format{background:#fde8ea;color:#b42335}.b-lookup_error{background:#eceef6;color:#555b80}
.npi-empty{padding:42px 10px;text-align:center;color:#8a8fb0;font-size:14px}
</style>
"""


def _chip(label: str, value: str, kind: str = "") -> str:
    return f'<div class="npi-chip {kind}"><b>{escape(value)}</b><span>{escape(label)}</span></div>'


def render_empty() -> str:
    return (CSS + '<div class="npi-card"><div class="npi-empty">'
            "Upload a file (or use the sample) and click <b>Run verification</b>.</div></div>")


def render_results(df: pd.DataFrame, summary: dict, verified_only: bool = False) -> str:
    shown = df[df["status"] == "verified"] if verified_only else df
    rows = []
    for r in shown.itertuples(index=False):
        status = escape(r.status)
        specialty = escape(r.specialty) if r.specialty else '<span class="muted">-</span>'
        rows.append(
            f'<tr><td class="mono">{escape(str(r.npi).strip())}</td>'
            f"<td>{escape(r.first_name)}</td><td>{escape(r.last_name)}</td><td>{specialty}</td>"
            f'<td class="nocopy"><span class="npi-badge b-{status}" '
            f'title="{escape(r.detail)}">{escape(STATUS_LABELS.get(r.status, r.status))}</span></td></tr>'
        )
    body = "".join(rows) or '<tr><td colspan="5" class="npi-empty">No rows to show.</td></tr>'
    stats = "".join([
        _chip("Respondents", str(summary["total"])),
        _chip("Verified", str(summary["verified"]), "good"),
        _chip("Flagged", str(summary["flagged"]), "warn"),
        _chip("Verified rate", f"{summary['rate']:.0f}%"),
    ])
    return (
        CSS + '<div class="npi-card"><div class="npi-head">'
        f'<div class="npi-stats">{stats}</div>'
        f'<button class="npi-copy" onclick="{escape(_COPY_JS, quote=True)}">Copy table</button></div>'
        '<div class="npi-wrap"><table class="npi-table"><thead><tr><th>NPI</th><th>First name</th>'
        '<th>Last name</th><th>Specialty</th><th class="nocopy">Status</th></tr></thead>'
        f"<tbody>{body}</tbody></table></div></div>"
    )
