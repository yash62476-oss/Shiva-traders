"""
SHIVA TRADERS - Mandi Commission Billing & Accounting
Run:  streamlit run shiva_traders_app.py
"""

from __future__ import annotations

import html
import io
import os
import shutil
import urllib.parse
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

# ======================================================================
# PAGE CONFIG & THEME
# ======================================================================
st.set_page_config(
    page_title="Shiva Traders | Billing & Accounting", page_icon="🏢", layout="wide"
)

st.markdown(
    """
    <style>
    /* ---------- Background ---------- */
    .stApp { background: radial-gradient(1200px 600px at 10% -10%, #1e1b4b 0%, transparent 60%),
                        radial-gradient(900px 500px at 100% 0%, #064e3b 0%, transparent 55%),
                        #090d16 !important;
             color:#f1f5f9 !important; overscroll-behavior-y:none !important; animation:fadeIn .5s ease-in-out; }
    @keyframes fadeIn { from{opacity:0; transform:translateY(6px);} to{opacity:1; transform:translateY(0);} }
    html, body { overscroll-behavior-y:none !important; font-family:'Segoe UI',Tahoma,Verdana,sans-serif; }
    footer { visibility:hidden; }

    /* ---------- Headings ---------- */
    h1 { background:linear-gradient(90deg,#22d3ee,#a78bfa,#f472b6,#fbbf24); -webkit-background-clip:text;
         background-clip:text; -webkit-text-fill-color:transparent; font-weight:900 !important; letter-spacing:1px; }
    h2,h3,h4 { color:#67e8f9 !important; font-weight:800 !important; letter-spacing:-.3px; }
    h3 { border-bottom:3px solid transparent; border-image:linear-gradient(90deg,#22d3ee,#a78bfa,transparent) 1; padding-bottom:6px; }
    label, label p, div[data-testid="stMarkdownContainer"] p { color:#e2e8f0 !important; font-weight:600 !important; }

    /* ---------- Inputs ---------- */
    input, select, textarea { color:#fff !important; background-color:#111827 !important;
        border:1px solid #4b5563 !important; border-radius:8px !important; transition:all .25s ease !important; }
    input:hover { border-color:#a78bfa !important; }
    input:focus, select:focus { border-color:#22d3ee !important; box-shadow:0 0 12px rgba(34,211,238,.5) !important; }

    /* ---------- Tabs: each tab has its own colour ---------- */
    button[data-baseweb="tab"] { background:#111827 !important; border-radius:10px !important;
        padding:10px 18px !important; margin-right:6px !important; border:1px solid #374151 !important;
        transition:all .25s cubic-bezier(.4,0,.2,1); }
    button[data-baseweb="tab"]:hover { background:#1f2937 !important; transform:translateY(-2px); }
    button[data-baseweb="tab"] p { color:#9ca3af !important; font-weight:700 !important; font-size:14px !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color:#fff !important; }
    button[data-baseweb="tab"][aria-selected="true"] { box-shadow:0 6px 18px rgba(0,0,0,.45); border-color:transparent !important; }
    button[data-baseweb="tab"]:nth-of-type(1):hover { border-color:#38bdf8 !important; }
    button[data-baseweb="tab"]:nth-of-type(2):hover { border-color:#34d399 !important; }
    button[data-baseweb="tab"]:nth-of-type(3):hover { border-color:#fbbf24 !important; }
    button[data-baseweb="tab"]:nth-of-type(4):hover { border-color:#a78bfa !important; }
    button[data-baseweb="tab"]:nth-of-type(5):hover { border-color:#f472b6 !important; }
    button[data-baseweb="tab"]:nth-of-type(6):hover { border-color:#22d3ee !important; }
    button[data-baseweb="tab"]:nth-of-type(7):hover { border-color:#fb923c !important; }
    button[data-baseweb="tab"][aria-selected="true"]:nth-of-type(1) { background:linear-gradient(135deg,#0ea5e9,#2563eb) !important; }
    button[data-baseweb="tab"][aria-selected="true"]:nth-of-type(2) { background:linear-gradient(135deg,#10b981,#047857) !important; }
    button[data-baseweb="tab"][aria-selected="true"]:nth-of-type(3) { background:linear-gradient(135deg,#f59e0b,#b45309) !important; }
    button[data-baseweb="tab"][aria-selected="true"]:nth-of-type(4) { background:linear-gradient(135deg,#8b5cf6,#6d28d9) !important; }
    button[data-baseweb="tab"][aria-selected="true"]:nth-of-type(5) { background:linear-gradient(135deg,#ec4899,#be185d) !important; }
    button[data-baseweb="tab"][aria-selected="true"]:nth-of-type(6) { background:linear-gradient(135deg,#06b6d4,#0e7490) !important; }
    button[data-baseweb="tab"][aria-selected="true"]:nth-of-type(7) { background:linear-gradient(135deg,#f97316,#c2410c) !important; }

    /* ---------- Metric cards: coloured by column ---------- */
    [data-testid="stMetric"] { background:linear-gradient(145deg,#111827,#1f2937) !important;
        border:1px solid #374151 !important; border-left:5px solid #22d3ee !important;
        padding:16px !important; border-radius:12px !important;
        box-shadow:0 8px 20px rgba(0,0,0,.35); transition:transform .25s ease, box-shadow .25s ease; }
    [data-testid="stMetric"]:hover { transform:translateY(-4px); box-shadow:0 12px 28px rgba(34,211,238,.25); }
    [data-testid="stMetricLabel"] p { color:#9ca3af !important; font-size:13px !important; text-transform:uppercase; letter-spacing:.8px; }
    [data-testid="stMetricValue"] { color:#22d3ee !important; font-weight:800 !important; font-size:24px !important; }

    [data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"], [data-testid="column"]:nth-child(2) [data-testid="stMetric"] { border-left-color:#34d399 !important; }
    [data-testid="stColumn"]:nth-child(2) [data-testid="stMetricValue"], [data-testid="column"]:nth-child(2) [data-testid="stMetricValue"] { color:#34d399 !important; }
    [data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"], [data-testid="column"]:nth-child(3) [data-testid="stMetric"] { border-left-color:#fbbf24 !important; }
    [data-testid="stColumn"]:nth-child(3) [data-testid="stMetricValue"], [data-testid="column"]:nth-child(3) [data-testid="stMetricValue"] { color:#fbbf24 !important; }
    [data-testid="stColumn"]:nth-child(4) [data-testid="stMetric"], [data-testid="column"]:nth-child(4) [data-testid="stMetric"] { border-left-color:#f472b6 !important; }
    [data-testid="stColumn"]:nth-child(4) [data-testid="stMetricValue"], [data-testid="column"]:nth-child(4) [data-testid="stMetricValue"] { color:#f472b6 !important; }
    [data-testid="stColumn"]:nth-child(5) [data-testid="stMetric"], [data-testid="column"]:nth-child(5) [data-testid="stMetric"] { border-left-color:#a78bfa !important; }
    [data-testid="stColumn"]:nth-child(5) [data-testid="stMetricValue"], [data-testid="column"]:nth-child(5) [data-testid="stMetricValue"] { color:#a78bfa !important; }

    /* ---------- Buttons ---------- */
    .stButton>button, .stFormSubmitButton>button, .stLinkButton>a {
        background:linear-gradient(135deg,#10b981,#047857) !important; color:#fff !important;
        font-weight:700 !important; border-radius:10px !important; padding:10px 24px !important;
        border:none !important; box-shadow:0 4px 15px rgba(16,185,129,.4);
        transition:all .25s cubic-bezier(.4,0,.2,1) !important; }
    .stButton>button:hover, .stFormSubmitButton>button:hover, .stLinkButton>a:hover {
        background:linear-gradient(135deg,#34d399,#059669) !important;
        box-shadow:0 8px 25px rgba(16,185,129,.7); transform:translateY(-2px) scale(1.02); }
    .stDownloadButton>button { background:linear-gradient(135deg,#8b5cf6,#4f46e5) !important; color:#fff !important;
        font-weight:700 !important; border-radius:10px !important; padding:10px 24px !important; border:none !important;
        box-shadow:0 4px 15px rgba(139,92,246,.45); transition:all .25s cubic-bezier(.4,0,.2,1) !important; }
    .stDownloadButton>button:hover { background:linear-gradient(135deg,#a78bfa,#6366f1) !important;
        box-shadow:0 8px 25px rgba(139,92,246,.7); transform:translateY(-2px) scale(1.02); }
    .stButton>button:disabled { background:#374151 !important; box-shadow:none; transform:none; }

    /* ---------- Alerts, expander, tables ---------- */
    [data-testid="stAlert"] { border-radius:10px !important; }
    [data-testid="stExpander"] { border:1px solid #4c1d95 !important; border-radius:10px !important; background:rgba(76,29,149,.12); }
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] { border:1px solid #1d4ed8; border-radius:10px; overflow:hidden; }
    hr { border-color:#312e81 !important; }

    /* ================= ANIMATIONS ================= */
    @keyframes gradientShift { 0%{background-position:0% 50%;} 50%{background-position:100% 50%;} 100%{background-position:0% 50%;} }
    @keyframes popIn    { from{opacity:0; transform:translateY(18px) scale(.94);} to{opacity:1; transform:translateY(0) scale(1);} }
    @keyframes fadeUp   { from{opacity:0; transform:translateY(14px);} to{opacity:1; transform:translateY(0);} }
    @keyframes slideIn  { from{opacity:0; transform:translateX(-24px);} to{opacity:1; transform:translateX(0);} }
    @keyframes shine    { from{left:-120%;} to{left:160%;} }
    @keyframes pulseGlow{ 0%,100%{box-shadow:0 4px 15px rgba(16,185,129,.35);} 50%{box-shadow:0 4px 30px rgba(16,185,129,.95);} }
    @keyframes tabGlow  { 0%,100%{filter:brightness(1);} 50%{filter:brightness(1.18);} }
    @keyframes floaty   { 0%,100%{transform:translateY(0);} 50%{transform:translateY(-5px);} }
    @keyframes lineGrow { from{background-size:0% 3px;} to{background-size:100% 3px;} }

    /* moving rainbow title */
    h1 { background-size:300% 100% !important; animation:gradientShift 6s ease infinite, floaty 4s ease-in-out infinite; }

    /* animated underline under sub-headings */
    h3 { border-bottom:none !important; border-image:none !important;
         background:linear-gradient(90deg,#22d3ee,#a78bfa,#f472b6) no-repeat left bottom / 100% 3px;
         animation:lineGrow 1s ease-out; }

    /* tab content slides up when you switch tabs */
    [data-baseweb="tab-panel"] { animation:fadeUp .45s ease-out; }

    /* selected tab breathes */
    button[data-baseweb="tab"][aria-selected="true"] { animation:tabGlow 2.6s ease-in-out infinite; }

    /* metric cards pop in one after another */
    [data-testid="stMetric"] { animation:popIn .6s cubic-bezier(.2,.8,.2,1) backwards; }
    [data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"], [data-testid="column"]:nth-child(2) [data-testid="stMetric"] { animation-delay:.08s; }
    [data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"], [data-testid="column"]:nth-child(3) [data-testid="stMetric"] { animation-delay:.16s; }
    [data-testid="stColumn"]:nth-child(4) [data-testid="stMetric"], [data-testid="column"]:nth-child(4) [data-testid="stMetric"] { animation-delay:.24s; }
    [data-testid="stColumn"]:nth-child(5) [data-testid="stMetric"], [data-testid="column"]:nth-child(5) [data-testid="stMetric"] { animation-delay:.32s; }

    /* buttons: shine sweep on hover, primary ones pulse */
    .stButton>button, .stFormSubmitButton>button, .stDownloadButton>button, .stLinkButton>a { position:relative; overflow:hidden; }
    .stButton>button::after, .stFormSubmitButton>button::after, .stDownloadButton>button::after, .stLinkButton>a::after {
        content:""; position:absolute; top:0; left:-120%; width:55%; height:100%;
        background:linear-gradient(120deg,transparent,rgba(255,255,255,.4),transparent); transform:skewX(-20deg); }
    .stButton>button:hover::after, .stFormSubmitButton>button:hover::after,
    .stDownloadButton>button:hover::after, .stLinkButton>a:hover::after { animation:shine .8s ease; }
    .stButton>button:active, .stFormSubmitButton>button:active, .stDownloadButton>button:active { transform:scale(.96) !important; }
    .stButton>button[kind="primary"], .stFormSubmitButton>button[kind="primary"] { animation:pulseGlow 2.4s ease-in-out infinite; }
    .stButton>button[kind="primary"]:hover, .stFormSubmitButton>button[kind="primary"]:hover { animation:none; }

    /* alerts (success / warning / error) slide in */
    [data-testid="stAlert"] { animation:slideIn .5s cubic-bezier(.2,.8,.2,1); }

    /* tables, charts, expanders fade up */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"], [data-testid="stExpander"],
    [data-testid="stArrowVegaLiteChart"], [data-testid="stVegaLiteChart"] { animation:fadeUp .6s ease-out; }

    /* inputs lift slightly when focused */
    input:focus, select:focus, textarea:focus { transform:translateY(-1px); }

    /* respect users who turn animations off in their OS */
    @media (prefers-reduced-motion: reduce) { * { animation:none !important; transition:none !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================================================================
# CONSTANTS
# ======================================================================
TX_FILE = Path("mandi_commission_sales.csv")
PAY_FILE = Path("mandi_payments.csv")
CUST_FILE = Path("customers_list.csv")
BACKUP_DIR = Path("backups")

TX_COLS = [
    "Bill_ID",
    "Date",
    "Customer",
    "Phone",
    "Variety",
    "Bags",
    "Weight_Kg",
    "Rate_Per_Kg",
    "Gross_Amount",
    "Commission_Percent",
    "Commission_Amt",
    "Labour_Charges",
    "Total_Profit",
    "Net_Bill_Amount",
    "Remarks",
]
TX_NUM = [
    "Bags",
    "Weight_Kg",
    "Rate_Per_Kg",
    "Gross_Amount",
    "Commission_Percent",
    "Commission_Amt",
    "Labour_Charges",
    "Total_Profit",
    "Net_Bill_Amount",
]
PAY_COLS = ["Pay_ID", "Date", "Customer", "Amount_Paid", "Payment_Mode", "Remarks"]
CUST_COLS = ["Customer_Name", "Phone", "Opening_Balance"]

PAY_MODES = ["Cash (नकद)", "UPI / PhonePe", "Bank Transfer", "Cheque"]
NEW_CUSTOMER = "-- नया नाम टाइप करें --"
DT_FMT = "%Y-%m-%d %H:%M"

try:
  _ver = tuple(int(x) for x in st.__version__.split(".")[:2])
except ValueError:
  _ver = (1, 0)
STRETCH = {"width": "stretch"} if _ver >= (1, 50) else {"use_container_width": True}


# ======================================================================
# HELPERS
# ======================================================================
def inr(x) -> str:
  try:
    x = float(x)
  except (TypeError, ValueError):
    x = 0.0
  neg = x < 0
  whole, dec = f"{abs(x):.2f}".split(".")
  if len(whole) > 3:
    head, tail = whole[:-3], whole[-3:]
    parts = []
    while len(head) > 2:
      parts.insert(0, head[-2:])
      head = head[:-2]
    if head:
      parts.insert(0, head)
    whole = ",".join(parts + [tail])
  return f"{'-' if neg else ''}₹{whole}.{dec}"


def num(x) -> str:
  try:
    return f"{float(x):g}"
  except (TypeError, ValueError):
    return str(x)


def clean_phone(p) -> str:
  s = str(p or "").strip()
  if s.endswith(".0"):
    s = s[:-2]
  d = "".join(ch for ch in s if ch.isdigit())
  if len(d) == 10:
    return "91" + d
  if len(d) == 11 and d.startswith("0"):
    return "91" + d[1:]
  if len(d) == 12 and d.startswith("91"):
    return d
  return ""


def wa_url(phone, text: str) -> str:
  p = clean_phone(phone)
  return f"https://wa.me/{p}?text={urllib.parse.quote(text)}" if p else ""


def backup_once(path: Path) -> None:
  if not path.exists():
    return
  BACKUP_DIR.mkdir(exist_ok=True)
  dst = BACKUP_DIR / f"{date.today():%Y-%m-%d}_{path.name}"
  if not dst.exists():
    shutil.copy2(path, dst)


def _fill_ids(df: pd.DataFrame, col: str) -> None:
  nums = pd.to_numeric(df[col], errors="coerce")
  nxt = int(nums.max()) + 1 if nums.notna().any() else 1
  for i in df.index[nums.isna()]:
    df.at[i, col] = str(nxt)
    nxt += 1


def _load(path: Path, cols, num_cols=(), id_col=None) -> pd.DataFrame:
  try:
    df = (
        pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        if path.exists()
        else pd.DataFrame(columns=cols)
    )
  except pd.errors.EmptyDataError:
    df = pd.DataFrame(columns=cols)
  for c in cols:
    if c not in df.columns:
      df[c] = ""
  df = df[cols].copy().reset_index(drop=True)
  for c in num_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
  if id_col:
    _fill_ids(df, id_col)
  return df


def load_tx() -> pd.DataFrame:
  df = _load(TX_FILE, TX_COLS, TX_NUM, "Bill_ID")
  df["Customer"] = df["Customer"].str.strip()
  return df


def load_pay() -> pd.DataFrame:
  df = _load(PAY_FILE, PAY_COLS, ["Amount_Paid"], "Pay_ID")
  df["Customer"] = df["Customer"].str.strip()
  return df


def load_cust() -> pd.DataFrame:
  df = _load(CUST_FILE, CUST_COLS, ["Opening_Balance"])
  df["Customer_Name"] = df["Customer_Name"].str.strip()
  return df.drop_duplicates("Customer_Name").reset_index(drop=True)


def save_df(df: pd.DataFrame, path: Path) -> None:
  backup_once(path)
  tmp = path.with_suffix(".tmp")
  df.to_csv(tmp, index=False, encoding="utf-8-sig")
  os.replace(tmp, path)


def append_row(df: pd.DataFrame, row: dict) -> pd.DataFrame:
  new = pd.DataFrame([row], columns=df.columns)
  return new if df.empty else pd.concat([df, new], ignore_index=True)


def next_id(df: pd.DataFrame, col: str) -> str:
  n = pd.to_numeric(df[col], errors="coerce")
  return str(int(n.max()) + 1) if n.notna().any() else "1"


def upsert_customer(name: str, phone: str) -> None:
  c = load_cust()
  m = c["Customer_Name"] == name
  if m.any():
    if phone and c.loc[m, "Phone"].iloc[0] != phone:
      c.loc[m, "Phone"] = phone
      save_df(c, CUST_FILE)
  else:
    c = append_row(
        c, {"Customer_Name": name, "Phone": phone, "Opening_Balance": 0.0}
    )
    save_df(c, CUST_FILE)


def balances(tx: pd.DataFrame, pay: pd.DataFrame, cust: pd.DataFrame) -> pd.DataFrame:
  names = sorted(
      {
          str(n).strip()
          for n in pd.concat(
              [cust["Customer_Name"], tx["Customer"], pay["Customer"]]
          )
          if str(n).strip()
      }
  )
  out = pd.DataFrame({"Customer": names})
  opening = cust.set_index("Customer_Name")["Opening_Balance"]
  out["Opening"] = out["Customer"].map(opening).fillna(0.0)
  out["Billed"] = (
      out["Customer"]
      .map(tx.groupby("Customer")["Net_Bill_Amount"].sum())
      .fillna(0.0)
  )
  out["Paid"] = (
      out["Customer"]
      .map(pay.groupby("Customer")["Amount_Paid"].sum())
      .fillna(0.0)
  )
  out["Balance"] = out["Opening"] + out["Billed"] - out["Paid"]
  return out


def balance_of(bal: pd.DataFrame, name: str) -> float:
  r = bal.loc[bal["Customer"] == name, "Balance"]
  return float(r.iloc[0]) if not r.empty else 0.0


def phone_of(cust: pd.DataFrame, name: str) -> str:
  r = cust.loc[cust["Customer_Name"] == name, "Phone"]
  p = str(r.iloc[0]) if not r.empty else ""
  return p[:-2] if p.endswith(".0") else p


def flash_and_rerun(
    msg: str, wa: str = "", wa_label: str = "📲 WhatsApp पर भेजें"
) -> None:
  st.session_state["flash"] = {"msg": msg, "wa": wa, "wa_label": wa_label}
  st.rerun()


# ======================================================================
# PRINT / HTML BUILDERS (With Satyanarayan Signature)
# ======================================================================
PRINT_CSS = """
body{font-family:Arial,sans-serif;padding:10px;color:#0f172a;background:#fff}
.card{border:3px solid #4f46e5;padding:20px;border-radius:14px;box-sizing:border-box;background:linear-gradient(180deg,#eef2ff 0,#fff 140px)}
.title{text-align:center;color:#fff;font-size:28px;font-weight:800;letter-spacing:2px;padding:12px;border-radius:10px;background:linear-gradient(90deg,#2563eb,#7c3aed,#db2777)}
.meta{display:flex;justify-content:space-between;margin-top:12px;font-size:15px}
h3{color:#4338ca;margin:18px 0 0}
table{width:100%;border-collapse:collapse;margin-top:10px}
th,td{border:1px solid #94a3b8;padding:7px;text-align:center;font-size:13px;color:#0f172a}
th{background:linear-gradient(90deg,#2563eb,#7c3aed);color:#fff}
tbody tr:nth-child(even){background:#f1f5f9}
tr.grand td{background:#0f172a;color:#fde047;font-weight:bold}
.totals{margin-top:15px;padding:12px;background:#fefce8;border-radius:8px;border-left:6px solid #f59e0b;font-size:16px;font-weight:bold;text-align:right}
.totals p{margin:4px 0}
.signature-section{margin-top:35px;display:flex;justify-content:space-between;align-items:flex-end;padding-top:15px}
.sign-box{text-align:right;width:220px}
.sign-name{font-size:20px;font-weight:bold;color:#1e3a8a;font-family:'Brush Script MT', cursive, serif;margin-bottom:2px}
.sign-label{font-size:13px;color:#475569;border-top:1px solid #94a3b8;padding-top:4px}
@keyframes up{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}.card{animation:up .6s ease-out}
.btn{background:linear-gradient(135deg,#16a34a,#15803d);color:#fff;padding:10px 20px;border:none;border-radius:8px;cursor:pointer;font-size:16px;font-weight:bold;margin-bottom:15px}
@media print{.btn{display:none}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""


def html_page(body: str) -> str:
  return (
      "<!DOCTYPE html><html><head><meta charset='utf-8'>"
      f"<style>{PRINT_CSS}</style></head><body>"
      "<button class='btn' onclick='window.print()'>🖨️ प्रिंट / PDF"
      f" निकालें</button>{body}</body></html>"
  )


def statement_body(
    party: str, sales: pd.DataFrame, pays: pd.DataFrame, lines, show_pays=True
) -> str:
  e = html.escape
  s_rows = (
      "".join(
          f"<tr><td>{e(str(r.Date))}</td><td>{e(str(r.Variety))}</td><td>{num(r.Bags)}</td>"
          f"<td>{num(r.Weight_Kg)} Kg</td><td>{inr(r.Rate_Per_Kg)}</td><td>{inr(r.Gross_Amount)}</td>"
          f"<td>{inr(r.Commission_Amt)} ({num(r.Commission_Percent)}%)</td><td>{inr(r.Labour_Charges)}</td>"
          f"<td style='color:#1d4ed8;font-weight:bold'>{inr(r.Net_Bill_Amount)}</td></tr>"
          for r in sales.itertuples()
      )
      or "<tr><td colspan='9'>कोई बिल नहीं है।</td></tr>"
  )

  pay_html = ""
  if show_pays:
    p_rows = (
        "".join(
            f"<tr><td>{e(str(r.Date))}</td>"
            f"<td style='color:#15803d;font-weight:bold'>{inr(r.Amount_Paid)}</td>"
            f"<td>{e(str(r.Payment_Mode))}</td><td>{e(str(r.Remarks))}</td></tr>"
            for r in pays.itertuples()
        )
        or "<tr><td colspan='4'>कोई जमा राशि नहीं है।</td></tr>"
    )
    pay_html = (
        "<h3>💵 जमा राशि विवरण:</h3><table><thead><tr><th>तारीख</th><th>जमा"
        f" रकम</th><th>माध्यम</th><th>नोट</th></tr></thead><tbody>{p_rows}</tbody></table>"
    )

  totals = ""
  for i, (label, val, color) in enumerate(lines):
    size = "font-size:19px;" if i == len(lines) - 1 else ""
    totals += f"<p style='color:{color};{size}'>{e(label)}: {val}</p>"

  return (
      "<div class='card'><div class='title'>SHIVA TRADERS</div>"
      f"<div class='meta'><span><b>ग्राहक नाम:</b> <span"
      f" style='color:#1d4ed8'>{e(party)}</span></span><span><b>दिनांक:</b>"
      f" {datetime.now():%d-%m-%Y %H:%M}</span></div>"
      "<h3>📦 बिक्री विवरण:</h3><table><thead><tr><th>तारीख</th><th>विवरण</th><th>बोरी</th>"
      "<th>वजन</th><th>रेट</th><th>मूल"
      " रकम</th><th>कमीशन</th><th>मजदूरी</th><th>कुल बिल</th></tr></thead>"
      f"<tbody>{s_rows}</tbody></table>{pay_html}<div"
      f" class='totals'>{totals}</div>"
      "<div class='signature-section'><div></div>"
      "<div class='sign-box'><div"
      " class='sign-name'>सत्यनारायण</div><div class='sign-label'>For SHIVA"
      " TRADERS<br>Authorized Signatory</div></div></div></div>"
  )


REG_COLS = [
    ("Customer", "पार्टी का नाम", "t"),
    ("Bags", "बोरी", "n"),
    ("Weight", "वजन (Kg)", "n"),
    ("Gross", "मूल रकम", "m"),
    ("Comm", "कमीशन", "m"),
    ("Labour", "मजदूरी", "m"),
    ("Profit", "कुल प्रॉफिट", "m"),
    ("Bill", "कुल बिल", "m"),
    ("Paid", "जमा", "m"),
    ("Balance", "कुल बकाया (अब तक)", "m"),
]


def register_body(reg: pd.DataFrame, period: str) -> str:
  e = html.escape
  head = "".join(f"<th>{e(lbl)}</th>" for _, lbl, _ in REG_COLS)
  rows = ""
  for r in reg.to_dict("records"):
    grand = r["Customer"] == "GRAND TOTAL"
    cells = ""
    for key, _, kind in REG_COLS:
      v = r[key]
      txt = e(str(v)) if kind == "t" else (num(v) if kind == "n" else inr(v))
      align = " style='text-align:left'" if kind == "t" else ""
      cells += f"<td{align}>{txt}</td>"
    rows += f"<tr class='{'grand' if grand else ''}'>{cells}</tr>"
  return (
      "<div class='card'><div class='title'>SHIVA TRADERS</div>"
      f"<p style='text-align:right;font-size:13px;color:#475569'><b>अवधि:</b>"
      f" {e(period)} &nbsp; <b>Report:</b> {datetime.now():%d-%m-%Y %H:%M}</p>"
      f"<table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>"
      "<div class='signature-section'><div></div>"
      "<div class='sign-box'><div"
      " class='sign-name'>सत्यनारायण</div><div class='sign-label'>For SHIVA"
      " TRADERS<br>Authorized Signatory</div></div></div></div>"
  )


def backup_zip() -> bytes:
  buf = io.BytesIO()
  with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for p in (TX_FILE, PAY_FILE, CUST_FILE):
      if p.exists():
        z.write(p, p.name)
  return buf.getvalue()


# ======================================================================
# TABS
# ======================================================================
def tab_dashboard(tx, pay, bal):
  st.subheader("आज का हिसाब (Dashboard)")
  today = date.today()
  dt = pd.to_datetime(tx["Date"], errors="coerce")
  pdt = pd.to_datetime(pay["Date"], errors="coerce")
  t_tx, t_pay = tx[dt.dt.date == today], pay[pdt.dt.date == today]
  month_profit = tx.loc[
      (dt.dt.year == today.year) & (dt.dt.month == today.month), "Total_Profit"
  ].sum()

  c1, c2, c3, c4, c5 = st.columns(5)
  c1.metric("आज के बिल", f"{len(t_tx)}")
  c2.metric("आज की बिक्री", inr(t_tx["Net_Bill_Amount"].sum()))
  c3.metric("आज का प्रॉफिट", inr(t_tx["Total_Profit"].sum()))
  c4.metric("आज की वसूली", inr(t_pay["Amount_Paid"].sum()))
  c5.metric("इस महीने का प्रॉफिट", inr(month_profit))

  total_due = bal.loc[bal["Balance"] > 0, "Balance"].sum() if not bal.empty else 0.0
  st.markdown(f"### 🚨 कुल बाज़ार बकाया (Udhaar): {inr(total_due)}")

  left, right = st.columns(2)
  with left:
    st.markdown("#### 🔝 सबसे ज़्यादा बकाया वाली पार्टियाँ")
    top = bal[bal["Balance"] > 0].nlargest(8, "Balance")
    if top.empty:
      st.info("कोई बकाया नहीं है 🎉")
    else:
      st.bar_chart(top.set_index("Customer")["Balance"])
  with right:
    st.markdown("#### 📈 पिछले 7 दिन का प्रॉफिट")
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    sub = tx[dt >= pd.Timestamp(days[0])]
    daily = (
        sub.groupby(dt[sub.index].dt.date)["Total_Profit"]
        .sum()
        .reindex(days, fill_value=0.0)
    )
    daily.index = [d.strftime("%d-%m") for d in days]
    st.bar_chart(daily)


def tab_new_bill(tx, pay, cust, bal):
  st.subheader("1. नया बिल और आढ़त एंट्री")

  if st.session_state.pop("_reset_bill", False):
    for k in ("bill_name", "bill_phone", "bill_rem"):
      st.session_state[k] = ""
    st.session_state["bill_instant"] = 0.0

  names = list(bal["Customer"]) if not bal.empty else []
  col1, col2, col3 = st.columns(3)

  with col1:
    if names:
      choice = st.selectbox("ग्राहक चुनें:", [NEW_CUSTOMER] + names, key="bill_cust")
    else:
      choice = NEW_CUSTOMER
      st.info("⚠️ कोई ग्राहक सेव नहीं है — नया नाम लिखें।")

    if choice == NEW_CUSTOMER:
      name = st.text_input("ग्राहक / पार्टी का नाम:", key="bill_name").strip()
      phone = st.text_input("फोन नंबर (WhatsApp):", key="bill_phone").strip()
    else:
      name = choice
      phone = st.text_input(
          "फोन नंबर (WhatsApp):",
          value=phone_of(cust, choice),
          key=f"bill_phone_{choice}",
      ).strip()
      prev = balance_of(bal, choice)
      st.caption(f"📒 अभी तक का बकाया: **{inr(prev)}**")

    variety = st.text_input("आइटम / विवरण:", value="3797", key="bill_variety")
    bill_date = st.date_input("बिल की तारीख:", value=date.today(), key="bill_date")

  with col2:
    bags = st.number_input(
        "बोरी / कट्टे (Bags):", min_value=1, value=50, step=1, key="bill_bags"
    )
    weight_kg = st.number_input(
        "कुल वजन (Kg):", min_value=1.0, value=2500.0, step=10.0, key="bill_wt"
    )
    rate_kg = st.number_input(
        "रेट (₹ per Kg):", min_value=0.5, value=12.0, step=0.5, key="bill_rate"
    )

  with col3:
    comm_percent = st.number_input(
        "कमीशन (%):", min_value=0.0, value=1.0, step=0.25, key="bill_comm"
    )
    labour_per_bag = st.number_input(
        "मजदूरी / खर्चा (₹ प्रति बोरी):",
        min_value=0.0,
        value=4.0,
        step=0.5,
        key="bill_lab",
    )
    remarks = st.text_input("गाड़ी नंबर / रिमार्क्स:", key="bill_rem")

  gross = round(weight_kg * rate_kg, 2)
  comm_amt = round(gross * comm_percent / 100.0, 2)
  labour_total = round(bags * labour_per_bag, 2)
  profit = round(comm_amt + labour_total, 2)
  net_bill = round(gross + profit, 2)

  st.markdown("---")
  st.subheader("📊 हिसाब-किताब & फ्रंट पेमेंट")
  p1, p2 = st.columns(2)
  instant_pay = p1.number_input(
      "हाथ-हाथ मिले पैसे (₹) [अगर अभी कुछ मिला है]:",
      min_value=0.0,
      value=0.0,
      step=100.0,
      key="bill_instant",
  )
  pay_mode = p2.selectbox("पेमेंट माध्यम:", PAY_MODES, key="bill_mode")

  m1, m2, m3, m4 = st.columns(4)
  m1.metric("मूल रकम (Gross)", inr(gross))
  m2.metric(f"कमीशन ({num(comm_percent)}%)", inr(comm_amt))
  m3.metric(f"मजदूरी ({bags} बोरी)", inr(labour_total))
  m4.metric("🔥 कुल प्रॉफिट", inr(profit))
  st.markdown(f"## 💸 Party Net Bill Amount: {inr(net_bill)}")

  if instant_pay > net_bill:
    st.warning("⚠️ हाथ-हाथ पैसे बिल रकम से ज़्यादा हैं (एडवांस के तौर पर जमा होगा)।")

  if st.button("पर्ची सेव करें (Save Bill & Payment)", type="primary", key="bill_save"):
    if not name:
      st.error("कृपया ग्राहक का नाम भरें!")
    elif phone and not clean_phone(phone):
      st.error("फोन नंबर सही नहीं है (10 अंक का मोबाइल नंबर डालें)।")
    else:
      now_str = datetime.combine(
          bill_date, datetime.now().time()
      ).strftime(DT_FMT)
      prev_bal = balance_of(bal, name)

      tx_df = load_tx()
      tx_df = append_row(
          tx_df,
          {
              "Bill_ID": next_id(tx_df, "Bill_ID"),
              "Date": now_str,
              "Customer": name,
              "Phone": phone,
              "Variety": variety,
              "Bags": bags,
              "Weight_Kg": weight_kg,
              "Rate_Per_Kg": rate_kg,
              "Gross_Amount": gross,
              "Commission_Percent": comm_percent,
              "Commission_Amt": comm_amt,
              "Labour_Charges": labour_total,
              "Total_Profit": profit,
              "Net_Bill_Amount": net_bill,
              "Remarks": remarks,
          },
      )
      save_df(tx_df, TX_FILE)

      if instant_pay > 0:
        pay_df = load_pay()
        pay_df = append_row(
            pay_df,
            {
                "Pay_ID": next_id(pay_df, "Pay_ID"),
                "Date": now_str,
                "Customer": name,
                "Amount_Paid": instant_pay,
                "Payment_Mode": pay_mode,
                "Remarks": "बिल के साथ फ्रंट पेमेंट",
            },
        )
        save_df(pay_df, PAY_FILE)

      upsert_customer(name, phone)
      new_bal = prev_bal + net_bill - instant_pay

      lines = [
          "🏢 *SHIVA TRADERS*",
          "",
          f"नमस्ते {name} जी,",
          "आपका बिल तैयार है:",
          f"• बिल रकम: {inr(net_bill)}",
          f"• जमा किए: {inr(instant_pay)}",
      ]
      if abs(prev_bal) > 0.005:
        lines.append(f"• पिछला बकाया: {inr(prev_bal)}")
      lines += [f"• *कुल बकाया: {inr(new_bal)}*", "", "धन्यवाद! 🙏"]

      st.session_state["_reset_bill"] = True
      flash_and_rerun(
          f"✅ {name} का बिल सेव हो गया! कुल बकाया: {inr(new_bal)}",
          wa_url(phone, "\n".join(lines)),
      )


def tab_payment(bal):
  st.subheader("2. ग्राहक से जमा पैसा (Payment Entry)")
  if bal.empty:
    st.info("अभी कोई ग्राहक नहीं है।")
    return

  names = list(bal["Customer"])
  cust_name = st.selectbox("ग्राहक चुनें:", names, key="pay_cust")
  cur = balance_of(bal, cust_name)
  st.caption(f"📒 अभी का बकाया: **{inr(cur)}**")

  c1, c2 = st.columns(2)
  amount = c1.number_input(
      "कितने पैसे मिले (₹):", min_value=1.0, value=1000.0, step=100.0, key="pay_amt"
  )
  mode = c2.selectbox("माध्यम:", PAY_MODES, key="pay_mode")
  pay_date = c1.date_input("तारीख:", value=date.today(), key="pay_date")
  remark = c2.text_input("नोट / टिप्पणी:", key="pay_rem")

  if amount > cur and cur >= 0:
    st.warning("⚠️ यह रकम बकाये से ज़्यादा है — बाकी एडवांस माना जाएगा।")

  if st.button("पेमेंट सेव करें", type="primary", key="pay_btn"):
    pay_df = load_pay()
    pay_df = append_row(
        pay_df,
        {
            "Pay_ID": next_id(pay_df, "Pay_ID"),
            "Date": datetime.combine(pay_date, datetime.now().time()).strftime(
                DT_FMT
            ),
            "Customer": cust_name,
            "Amount_Paid": amount,
            "Payment_Mode": mode,
            "Remarks": remark,
        },
    )
    save_df(pay_df, PAY_FILE)
    new_bal = cur - amount
    msg = (
        f"🏢 *SHIVA TRADERS*\n\nनमस्ते {cust_name} जी,\nआपके {inr(amount)} जमा हो"
        f" गए हैं。\n*शेष बकाया: {inr(new_bal)}*\n\nधन्यवाद! 🙏"
    )
    flash_and_rerun(
        f"✅ {inr(amount)} की जमा एंट्री हो गई! ({cust_name}) — शेष बकाया:"
        f" {inr(new_bal)}",
        wa_url(phone_of(load_cust(), cust_name), msg),
        "📲 रसीद WhatsApp करें",
    )


def tab_customers(cust, bal):
  st.subheader("3. ग्राहक सूची")

  with st.form("add_customer", clear_on_submit=True):
    a, b, c = st.columns(3)
    n = a.text_input("ग्राहक का पूरा नाम:")
    p = b.text_input("मोबाइल नंबर (WhatsApp):")
    ob = c.number_input("पुराना बकाया (₹) [Opening]:", value=0.0, step=100.0)
    submitted = st.form_submit_button("ग्राहक सेव करें", type="primary")

  if submitted:
    n, p = n.strip(), p.strip()
    existing = {x.lower() for x in bal["Customer"]} if not bal.empty else set()
    if not n:
      st.error("कृपया ग्राहक का नाम दर्ज करें!")
    elif n.lower() in existing:
      st.warning("यह ग्राहक पहले से सूची में मौजूद है!")
    elif p and not clean_phone(p):
      st.error("फोन नंबर सही नहीं है (10 अंक)।")
    else:
      c_df = append_row(
          load_cust(),
          {"Customer_Name": n, "Phone": p, "Opening_Balance": ob},
      )
      save_df(c_df, CUST_FILE)
      flash_and_rerun(f"✅ '{n}' सफलतापूर्वक सेव हो गया!")

  st.markdown("### 📋 सभी ग्राहक (फोन / पुराना बकाया यहीं बदलें)")
  if bal.empty:
    st.info("अभी कोई ग्राहक सेव नहीं है।")
    return

  base = (
      cust.set_index("Customer_Name")
      .reindex(bal["Customer"])
      .reset_index()
      .rename(columns={"Customer": "Customer_Name", "index": "Customer_Name"})
  )
  base["Phone"] = base["Phone"].fillna("")
  base["Opening_Balance"] = base["Opening_Balance"].fillna(0.0)
  base = base[CUST_COLS]

  edited = st.data_editor(
      base,
      hide_index=True,
      disabled=["Customer_Name"],
      key="cust_editor",
      column_config={
          "Customer_Name": st.column_config.TextColumn("ग्राहक"),
          "Phone": st.column_config.TextColumn("फोन"),
          "Opening_Balance": st.column_config.NumberColumn(
              "पुराना बकाया (₹)", format="%.2f"
          ),
      },
      **STRETCH,
  )
  if st.button("बदलाव सेव करें", key="cust_save"):
    bad = [
        r.Customer_Name
        for r in edited.itertuples()
        if str(r.Phone).strip() and not clean_phone(r.Phone)
    ]
    if bad:
      st.error(f"इनका फोन नंबर सही नहीं है: {', '.join(bad)}")
    else:
      out = edited.copy()
      out["Phone"] = out["Phone"].fillna("").astype(str).str.strip()
      out["Opening_Balance"] = (
          pd.to_numeric(out["Opening_Balance"], errors="coerce").fillna(0.0)
      )
      save_df(out, CUST_FILE)
      flash_and_rerun("✅ ग्राहक सूची अपडेट हो गई!")


def tab_print(tx, pay, cust, bal):
  st.subheader("4. ग्राहक पर्ची व खाता प्रिंट")
  if bal.empty:
    st.info("प्रिंट करने के लिए कोई डाटा नहीं है।")
    return

  party = st.selectbox("ग्राहक चुनें:", list(bal["Customer"]), key="print_cust")
  mode = st.radio(
      "क्या प्रिंट करना है?",
      ["पूरा खाता (Statement)", "सिर्फ़ एक बिल (Single Bill)"],
      horizontal=True,
      key="print_mode",
  )

  sales = tx[tx["Customer"] == party]
  pays = pay[pay["Customer"] == party]
  row = bal[bal["Customer"] == party].iloc[0]
  opening, total_bill, total_paid, balance = (
      row["Opening"],
      row["Billed"],
      row["Paid"],
      row["Balance"],
  )
  profit_party = sales["Total_Profit"].sum()

  m1, m2, m3, m4 = st.columns(4)
  m1.metric("कुल बिल रकम", inr(total_bill))
  m2.metric("कुल जमा किया", inr(total_paid))
  m3.metric("🚨 कुल बकाया (Udhaar)", inr(balance))
  m4.metric("📈 इस पार्टी से प्रॉफिट", inr(profit_party))
  st.markdown("---")

  if mode.startswith("पूरा"):
    lines = []
    if abs(opening) > 0.005:
      lines.append(("पिछला बकाया (Opening)", inr(opening), "#000000"))
    lines += [
        ("कुल बिल रकम", inr(total_bill), "#000000"),
        ("कुल जमा रकम", inr(total_paid), "#16a34a"),
        ("🚨 कुल शेष बकाया", inr(balance), "#dc2626"),
    ]
    body = statement_body(party, sales, pays, lines, show_pays=True)
    height = min(1500, 520 + 36 * (len(sales) + len(pays)))
    file_name = f"{party}_khata_{date.today():%Y%m%d}.html"
  else:
    if sales.empty:
      st.info("इस पार्टी का कोई बिल नहीं है।")
      return
    opts = {
        r.Bill_ID: (
            f"#{r.Bill_ID} | {r.Date} | {r.Variety} |"
            f" {inr(r.Net_Bill_Amount)}"
        )
        for r in sales.iloc[::-1].itertuples()
    }
    bid = st.selectbox(
        "बिल चुनें:", list(opts), format_func=opts.get, key="print_bill"
    )
    one = sales[sales["Bill_ID"] == bid]
    lines = [
        (f"बिल #{bid} की रकम", inr(one["Net_Bill_Amount"].iloc[0]), "#1d4ed8"),
        ("पार्टी का कुल बकाया (अब तक)", inr(balance), "#dc2626"),
    ]
    body = statement_body(party, one, pays, lines, show_pays=False)
    height = 520
    file_name = f"{party}_bill_{bid}.html"

  page = html_page(body)
  st.components.v1.html(page, height=height, scrolling=True)

  d1, d2 = st.columns(2)
  d1.download_button(
      "⬇️ HTML डाउनलोड (browser में खोलकर प्रिंट करें)",
      page.encode("utf-8"),
      file_name=file_name,
      mime="text/html",
      key="print_dl",
  )
  phone = phone_of(cust, party)
  if balance > 0.005 and clean_phone(phone):
    remind = (
        f"🏢 *SHIVA TRADERS*\n\nनमस्ते {party} जी,\nआपका कुल बकाया"
        f" *{inr(balance)}* है。\nकृपया जल्द जमा करें। धन्यवाद! 🙏"
    )
    d2.link_button("📲 बकाया याद दिलाएँ (WhatsApp)", wa_url(phone, remind))


def tab_register(tx, pay, bal):
  st.subheader("5. Shiva Traders खाता रजिस्टर (Summary)")
  if tx.empty:
    st.info("रजिस्टर में दिखाने के लिए अभी कोई डेटा नहीं है।")
    return

  dt = pd.to_datetime(tx["Date"], errors="coerce")
  first = dt.min().date() if dt.notna().any() else date.today()
  rng = st.date_input(
      "तारीख से — तक:", value=(first, date.today()), key="reg_range"
  )
  if not (isinstance(rng, (tuple, list)) and len(rng) == 2):
    st.info("कृपया शुरू और आख़िरी दोनों तारीख चुनें।")
    return
  d1, d2 = pd.Timestamp(rng[0]), pd.Timestamp(rng[1])

  def in_range(frame):
    d = pd.to_datetime(frame["Date"], errors="coerce").dt.normalize()
    return frame[(d >= d1) & (d <= d2)]

  txp, payp = in_range(tx), in_range(pay)
  g_tx = txp.groupby("Customer").agg(
      Bags=("Bags", "sum"),
      Weight=("Weight_Kg", "sum"),
      Gross=("Gross_Amount", "sum"),
      Comm=("Commission_Amt", "sum"),
      Labour=("Labour_Charges", "sum"),
      Profit=("Total_Profit", "sum"),
      Bill=("Net_Bill_Amount", "sum"),
  )
  g_pay = payp.groupby("Customer")["Amount_Paid"].sum().rename("Paid")
  reg = g_tx.join(g_pay, how="outer").fillna(0.0)
  reg.index.name = "Customer"
  reg = (
      reg.reset_index()
      .merge(bal[["Customer", "Balance"]], on="Customer", how="left")
      .fillna(0.0)
  )

  if reg.empty:
    st.info("इस अवधि में कोई एंट्री नहीं है।")
    return

  reg = reg.sort_values("Bill", ascending=False).reset_index(drop=True)
  totals = {k: reg[k].sum() for k, _, kind in REG_COLS if kind != "t"}
  reg = pd.concat(
      [reg, pd.DataFrame([{"Customer": "GRAND TOTAL", **totals}])],
      ignore_index=True,
  )

  k1, k2, k3, k4 = st.columns(4)
  k1.metric("कुल बिक्री", inr(totals["Bill"]))
  k2.metric("कुल प्रॉफिट", inr(totals["Profit"]))
  k3.metric("कुल वसूली", inr(totals["Paid"]))
  k4.metric(
      "🚨 कुल बकाया (अब तक)",
      inr(bal.loc[bal["Balance"] > 0, "Balance"].sum()),
  )

  label_map = {k: lbl for k, lbl, _ in REG_COLS}
  cfg = {
      lbl: st.column_config.NumberColumn(lbl, format="₹ %.2f")
      for k, lbl, kind in REG_COLS
      if kind == "m"
  }
  st.dataframe(
      reg.rename(columns=label_map),
      hide_index=True,
      column_config=cfg,
      **STRETCH,
  )

  period = f"{rng[0]:%d-%m-%Y} से {rng[1]:%d-%m-%Y}"
  page = html_page(register_body(reg, period))
  a, b = st.columns(2)
  a.download_button(
      "⬇️ Excel/CSV डाउनलोड",
      reg.rename(columns=label_map).to_csv(index=False).encode("utf-8-sig"),
      file_name=f"register_{date.today():%Y%m%d}.csv",
      mime="text/csv",
      key="reg_csv",
  )
  b.download_button(
      "🖨️ प्रिंट वाला रजिस्टर (HTML)",
      page.encode("utf-8"),
      file_name=f"register_{date.today():%Y%m%d}.html",
      mime="text/html",
      key="reg_print",
  )


def tab_backup():
  st.subheader("6. बैकअप और डेटा सुरक्षा")
  st.markdown(
      "यहाँ से आप अपना पूरा डेटा (बिल, पेमेंट्स, कस्टमर लिस्ट) सुरक्षित रूप से"
      " डाउनलोड कर सकते हैं।"
  )

  zip_bytes = backup_zip()
  st.download_button(
      "📦 सभी CSV फाइल्स का ZIP डाउनलोड करें",
      zip_bytes,
      file_name=f"shiva_traders_backup_{date.today():%Y%m%d}.zip",
      mime="application/zip",
      type="primary",
  )


# ======================================================================
# MAIN
# ======================================================================
def main():
  tx = load_tx()
  pay = load_pay()
  cust = load_cust()
  bal = balances(tx, pay, cust)

  st.title("🏢 SHIVA TRADERS")
  st.markdown(
      "<p style='color:#9ca3af;font-size:16px;margin-top:-10px;margin-bottom:20px'>Professional"
      " Mandi Commission & Billing Dashboard</p>",
      unsafe_allow_html=True,
  )

  flash = st.session_state.pop("flash", None)
  if flash:
    st.success(flash["msg"])
    if flash["wa"]:
      st.link_button(flash["wa_label"], flash["wa"])

  t1, t2, t3, t4, t5, t6, t7 = st.tabs([
      "📊 डैशबोर्ड",
      "📑 नया बिल",
      "💵 जमा पैसा",
      "👥 ग्राहक सूची",
      "🖨️ पर्ची प्रिंट",
      "📋 रजिस्टर",
      "💾 बैकअप",
  ])

  with t1:
    tab_dashboard(tx, pay, bal)
  with t2:
    tab_new_bill(tx, pay, cust, bal)
  with t3:
    tab_payment(bal)
  with t4:
    tab_customers(cust, bal)
  with t5:
    tab_print(tx, pay, cust, bal)
  with t6:
    tab_register(tx, pay, bal)
  with t7:
    tab_backup()


if __name__ == "__main__":
  main()
