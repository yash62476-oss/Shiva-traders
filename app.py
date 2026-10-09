from __future__ import annotations

from datetime import datetime, date
from pathlib import Path
import html
import urllib.parse

import pandas as pd
import streamlit as st

# ============================================================
# SHIVA TRADERS — Mandi Billing & Account Manager
# Run: streamlit run shiva_traders.py
# ============================================================

st.set_page_config(
    page_title="Shiva Traders | Billing & Accounts",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(".")
SALES_FILE = APP_DIR / "mandi_commission_sales.csv"
PAYMENTS_FILE = APP_DIR / "mandi_payments.csv"
CUSTOMERS_FILE = APP_DIR / "customers_list.csv"

SALES_COLUMNS = [
    "Bill_ID", "Date", "Customer", "Phone", "Variety", "Bags", "Weight_Kg",
    "Rate_Per_Kg", "Gross_Amount", "Commission_Percent", "Commission_Amt",
    "Labour_Charges", "Total_Profit", "Net_Bill_Amount", "Remarks",
]
PAYMENT_COLUMNS = [
    "Payment_ID", "Date", "Customer", "Amount_Paid", "Payment_Mode", "Remarks",
]
CUSTOMER_COLUMNS = ["Customer_Name", "Phone"]

# ----------------------------- Theme -----------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
    :root { --accent:#38bdf8; --green:#34d399; --panel:#111827; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at 12% 0%, #14253c 0, #0b1120 38%, #080d17 100%); }
    [data-testid="stHeader"] { background: rgba(8,13,23,.85); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg,#101a2b,#0b1220); border-right:1px solid #26354a; }
    h1,h2,h3 { letter-spacing:-.4px; }
    h1 { color:#f8fafc !important; font-weight:800 !important; }
    h2,h3 { color:#7dd3fc !important; }
    p, label, [data-testid="stMarkdownContainer"] { color:#dbe5f1; }
    div[data-testid="stMetric"] {
      background:linear-gradient(145deg,rgba(23,37,58,.96),rgba(13,22,37,.96));
      border:1px solid #2b405a; border-radius:16px; padding:16px 18px;
      box-shadow:0 8px 24px rgba(0,0,0,.16); transition:transform .2s ease,border-color .2s ease;
    }
    div[data-testid="stMetric"]:hover { transform:translateY(-2px); border-color:#38bdf8; }
    [data-testid="stMetricLabel"] { color:#9fb3c9 !important; }
    [data-testid="stMetricValue"] { color:#f0f9ff !important; font-weight:800; }
    .hero {
      padding:24px 28px; border:1px solid #29415e; border-radius:20px;
      background:linear-gradient(120deg,rgba(14,116,144,.20),rgba(30,41,59,.65) 55%,rgba(5,150,105,.13));
      margin-bottom:18px;
    }
    .hero-kicker { color:#7dd3fc; text-transform:uppercase; letter-spacing:2px; font-size:11px; font-weight:800; }
    .hero-title { color:#f8fafc; font-size:34px; font-weight:800; line-height:1.15; margin:6px 0; }
    .hero-sub { color:#a8bdd2; font-size:14px; }
    .section-note { color:#9fb3c9; font-size:13px; margin-top:-8px; margin-bottom:16px; }
    .status-pill { display:inline-block; border-radius:999px; padding:4px 10px; background:#123b35; color:#6ee7b7; font-size:12px; font-weight:700; }
    div.stButton > button, div.stDownloadButton > button {
      border-radius:10px; font-weight:700; border:1px solid #2b526b;
      transition:all .2s ease;
    }
    div.stButton > button[kind="primary"] { background:linear-gradient(135deg,#0891b2,#047857); color:white; border:0; }
    div.stButton > button:hover, div.stDownloadButton > button:hover { border-color:#38bdf8; transform:translateY(-1px); }
    button[data-baseweb="tab"] { border-radius:10px 10px 0 0; font-weight:700; }
    [data-testid="stDataFrame"] { border:1px solid #2b405a; border-radius:12px; overflow:hidden; }
    hr { border-color:#26354a; }
    .small-muted { color:#94a3b8; font-size:12px; }
    @media print { .no-print { display:none !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------- Data helpers -----------------------------
def ensure_csv(path: Path, columns: list[str]) -> None:
    if not path.exists():
        pd.DataFrame(columns=columns).to_csv(path, index=False)


def read_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    ensure_csv(path, columns)
    try:
        df = pd.read_csv(path)
    except (pd.errors.EmptyDataError, UnicodeDecodeError):
        df = pd.DataFrame(columns=columns)
    for column in columns:
        if column not in df.columns:
            df[column] = pd.NA
    return df[columns]


def append_row(path: Path, row: dict, columns: list[str]) -> None:
    ensure_csv(path, columns)
    pd.DataFrame([row], columns=columns).to_csv(
        path, mode="a", header=False, index=False, encoding="utf-8"
    )


def money(value: float) -> str:
    return f"₹{float(value or 0):,.2f}"


def safe_text(value) -> str:
    return html.escape("" if pd.isna(value) else str(value))


def clean_phone(value: str) -> str:
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) == 10:
        digits = "91" + digits
    return digits


def next_id(prefix: str, df: pd.DataFrame, col: str) -> str:
    existing = df[col].dropna().astype(str).tolist() if col in df.columns else []
    number = len(existing) + 1
    candidate = f"{prefix}-{datetime.now():%y%m%d}-{number:04d}"
    while candidate in existing:
        number += 1
        candidate = f"{prefix}-{datetime.now():%y%m%d}-{number:04d}"
    return candidate


def get_balance_tables(sales: pd.DataFrame, payments: pd.DataFrame):
    sales_copy = sales.copy()
    payments_copy = payments.copy()
    if not sales_copy.empty:
        sales_copy["Net_Bill_Amount"] = pd.to_numeric(sales_copy["Net_Bill_Amount"], errors="coerce").fillna(0)
    if not payments_copy.empty:
        payments_copy["Amount_Paid"] = pd.to_numeric(payments_copy["Amount_Paid"], errors="coerce").fillna(0)
    billed = sales_copy.groupby("Customer")["Net_Bill_Amount"].sum() if not sales_copy.empty else pd.Series(dtype=float)
    paid = payments_copy.groupby("Customer")["Amount_Paid"].sum() if not payments_copy.empty else pd.Series(dtype=float)
    names = sorted(set(billed.index.tolist()) | set(paid.index.tolist()))
    summary = pd.DataFrame({"Customer": names})
    summary["Total_Billed"] = summary["Customer"].map(billed).fillna(0)
    summary["Total_Paid"] = summary["Customer"].map(paid).fillna(0)
    summary["Balance"] = summary["Total_Billed"] - summary["Total_Paid"]
    return summary


ensure_csv(SALES_FILE, SALES_COLUMNS)
ensure_csv(PAYMENTS_FILE, PAYMENT_COLUMNS)
ensure_csv(CUSTOMERS_FILE, CUSTOMER_COLUMNS)

sales_df = read_csv(SALES_FILE, SALES_COLUMNS)
payments_df = read_csv(PAYMENTS_FILE, PAYMENT_COLUMNS)
customers_df = read_csv(CUSTOMERS_FILE, CUSTOMER_COLUMNS)

for col in ["Bags", "Weight_Kg", "Rate_Per_Kg", "Gross_Amount", "Commission_Percent",
            "Commission_Amt", "Labour_Charges", "Total_Profit", "Net_Bill_Amount"]:
    sales_df[col] = pd.to_numeric(sales_df[col], errors="coerce").fillna(0)
payments_df["Amount_Paid"] = pd.to_numeric(payments_df["Amount_Paid"], errors="coerce").fillna(0)

balance_df = get_balance_tables(sales_df, payments_df)
total_sales = float(sales_df["Net_Bill_Amount"].sum()) if not sales_df.empty else 0.0
total_profit = float(sales_df["Total_Profit"].sum()) if not sales_df.empty else 0.0
total_received = float(payments_df["Amount_Paid"].sum()) if not payments_df.empty else 0.0
total_due = total_sales - total_received

# ----------------------------- Sidebar -----------------------------
with st.sidebar:
    st.markdown("## 🏢 SHIVA TRADERS")
    st.caption("Mandi billing • Commission • Accounts")
    st.markdown("---")
    st.markdown("**Quick overview**")
    st.metric("Total bills", len(sales_df))
    st.metric("Total parties", int(balance_df["Customer"].nunique()) if not balance_df.empty else 0)
    st.metric("Outstanding", money(total_due))
    st.markdown("---")
    st.caption(f"📅 {datetime.now():%d %B %Y}")
    st.caption("Tip: export your CSV files regularly as a backup.")

# ----------------------------- Header -----------------------------
st.markdown(
    f"""
    <div class="hero">
      <div class="hero-kicker">MANDI MANAGEMENT SUITE</div>
      <div class="hero-title">Shiva Traders <span style="color:#38bdf8">.</span></div>
      <div class="hero-sub">Billing, customer ledger, payments and printable statements — all in one place.</div>
      <div style="margin-top:14px"><span class="status-pill">● LOCAL DATA MODE</span>
      <span class="small-muted" style="margin-left:10px">Updated {datetime.now():%d %b %Y, %I:%M %p}</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Dashboard metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 Total billed", money(total_sales))
m2.metric("📥 Total received", money(total_received))
m3.metric("⏳ Outstanding", money(total_due), delta="Pending balance")
m4.metric("📈 Commission + labour", money(total_profit))

tab_dashboard, tab_bill, tab_customer, tab_payment, tab_ledger, tab_reports = st.tabs([
    "🏠 Dashboard", "🧾 New Bill", "👥 Customers", "💵 Payments", "📒 Party Ledger", "📊 Reports & Export"
])

# ----------------------------- Dashboard -----------------------------
with tab_dashboard:
    st.subheader("Business snapshot")
    st.markdown('<div class="section-note">A quick view of recent activity and outstanding customer balances.</div>', unsafe_allow_html=True)
    left, right = st.columns([1.4, 1])
    with left:
        st.markdown("#### Recent bills")
        if sales_df.empty:
            st.info("Abhi koi bill nahi hai. **New Bill** tab se pehli entry add karein.")
        else:
            recent = sales_df.sort_values("Date", ascending=False).head(8).copy()
            recent = recent[["Bill_ID", "Date", "Customer", "Variety", "Bags", "Net_Bill_Amount"]]
            recent["Net_Bill_Amount"] = recent["Net_Bill_Amount"].map(money)
            st.dataframe(recent, use_container_width=True, hide_index=True)
    with right:
        st.markdown("#### Highest outstanding")
        if balance_df.empty:
            st.info("Customer balance data abhi available nahi hai.")
        else:
            due = balance_df[balance_df["Balance"] > 0].sort_values("Balance", ascending=False).head(8).copy()
            if due.empty:
                st.success("🎉 Kisi customer ka positive balance pending nahi hai.")
            else:
                due["Balance"] = due["Balance"].map(money)
                st.dataframe(due[["Customer", "Balance"]], use_container_width=True, hide_index=True)
    st.markdown("---")
    if not sales_df.empty:
        st.markdown("#### Billing trend")
        trend = sales_df.copy()
        trend["DateOnly"] = pd.to_datetime(trend["Date"], errors="coerce").dt.date
        trend = trend.dropna(subset=["DateOnly"]).groupby("DateOnly", as_index=False)["Net_Bill_Amount"].sum()
        if not trend.empty:
            st.line_chart(trend.set_index("DateOnly")["Net_Bill_Amount"], use_container_width=True)
    st.caption("Note: data is stored in CSV files in the app's working folder. Keep backups.")

# ----------------------------- New bill -----------------------------
with tab_bill:
    st.subheader("Create a new bill")
    st.markdown('<div class="section-note">Enter the party, quantity and rate. Amounts are calculated automatically.</div>', unsafe_allow_html=True)

    saved_names = sorted(customers_df["Customer_Name"].dropna().astype(str).unique().tolist())
    choose_options = ["＋ Add a new customer"] + saved_names
    chosen = st.selectbox("Choose saved party (or add new)", choose_options, key="bill_customer_choice")
    if chosen == "＋ Add a new customer":
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Party / customer name", key="bill_customer_name").strip()
        with col2:
            customer_phone = st.text_input("Mobile number", key="bill_customer_phone").strip()
    else:
        match = customers_df[customers_df["Customer_Name"].astype(str) == chosen]
        default_phone = "" if match.empty or pd.isna(match.iloc[0]["Phone"]) else str(match.iloc[0]["Phone"])
        col1, col2 = st.columns(2)
        with col1:
            customer_name = chosen
            st.text_input("Party / customer name", value=chosen, disabled=True, key="saved_customer_name")
        with col2:
            customer_phone = st.text_input("Mobile number", value=default_phone, key="saved_customer_phone").strip()

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        variety = st.text_input("Item / variety", value="3797")
        bags = st.number_input("Bags / boriyan", min_value=1, value=50, step=1)
    with col_b:
        weight_kg = st.number_input("Total weight (kg)", min_value=0.1, value=2500.0, step=10.0)
        rate_kg = st.number_input("Rate per kg (₹)", min_value=0.0, value=12.0, step=0.5)
    with col_c:
        commission_percent = st.number_input("Commission (%)", min_value=0.0, value=1.0, step=0.25)
        labour_per_bag = st.number_input("Labour per bag (₹)", min_value=0.0, value=4.0, step=0.5)
    remarks = st.text_input("Vehicle number / remarks")

    gross = weight_kg * rate_kg
    commission = gross * commission_percent / 100
    labour = bags * labour_per_bag
    profit = commission + labour
    net_bill = gross + profit

    st.markdown("---")
    st.markdown("#### Bill calculation")
    calc1, calc2, calc3, calc4 = st.columns(4)
    calc1.metric("Gross amount", money(gross))
    calc2.metric("Commission", money(commission))
    calc3.metric("Labour", money(labour))
    calc4.metric("Net bill", money(net_bill))
    st.caption("Formula: Gross = Weight × Rate | Commission = Gross × % | Labour = Bags × Labour rate | Net bill = Gross + Commission + Labour")

    st.markdown("#### Payment received with this bill (optional)")
    p1, p2 = st.columns(2)
    with p1:
        instant_payment = st.number_input("Received now (₹)", min_value=0.0, value=0.0, step=100.0)
    with p2:
        instant_mode = st.selectbox("Payment method", ["Cash", "UPI / PhonePe", "Bank transfer", "Cheque"])

    if st.button("✅ Save bill", type="primary", use_container_width=True):
        if not customer_name:
            st.error("Party ka naam zaroor bharein.")
        elif instant_payment > net_bill:
            st.error("Received amount bill amount se zyada hai. Amount check karein.")
        else:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            sales_now = read_csv(SALES_FILE, SALES_COLUMNS)
            bill_id = next_id("ST", sales_now, "Bill_ID")
            append_row(SALES_FILE, {
                "Bill_ID": bill_id, "Date": now, "Customer": customer_name,
                "Phone": customer_phone, "Variety": variety, "Bags": bags,
                "Weight_Kg": weight_kg, "Rate_Per_Kg": rate_kg, "Gross_Amount": gross,
                "Commission_Percent": commission_percent, "Commission_Amt": commission,
                "Labour_Charges": labour, "Total_Profit": profit, "Net_Bill_Amount": net_bill,
                "Remarks": remarks,
            }, SALES_COLUMNS)
            if instant_payment > 0:
                payments_now = read_csv(PAYMENTS_FILE, PAYMENT_COLUMNS)
                append_row(PAYMENTS_FILE, {
                    "Payment_ID": next_id("PAY", payments_now, "Payment_ID"),
                    "Date": now, "Customer": customer_name, "Amount_Paid": instant_payment,
                    "Payment_Mode": instant_mode, "Remarks": f"Payment with bill {bill_id}",
                }, PAYMENT_COLUMNS)
            if customer_name not in saved_names:
                append_row(CUSTOMERS_FILE, {"Customer_Name": customer_name, "Phone": customer_phone}, CUSTOMER_COLUMNS)
            st.success(f"Bill {bill_id} saved successfully for {customer_name}.")
            st.info(f"Bill: {money(net_bill)}  •  Received now: {money(instant_payment)}  •  Remaining on this bill before older balances: {money(net_bill - instant_payment)}")
            if customer_phone:
                phone = clean_phone(customer_phone)
                if len(phone) >= 10:
                    message = (
                        f"SHIVA TRADERS\\nBill No: {bill_id}\\nParty: {customer_name}\\n"
                        f"Bill Amount: {money(net_bill)}\\nReceived: {money(instant_payment)}\\n"
                        f"Thank you!"
                    )
                    wa_url = f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"
                    st.link_button("📲 Send bill summary on WhatsApp", wa_url)
            st.caption("Reload the page if the dashboard totals do not update immediately.")

# ----------------------------- Customers -----------------------------
with tab_customer:
    st.subheader("Customer directory")
    with st.form("add_customer_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            new_name = st.text_input("Full customer / party name")
        with c2:
            new_phone = st.text_input("Mobile number")
        add_customer = st.form_submit_button("＋ Save customer", type="primary")
    if add_customer:
        new_name = new_name.strip()
        if not new_name:
            st.error("Customer name required.")
        elif not customers_df.empty and customers_df["Customer_Name"].fillna("").astype(str).str.casefold().eq(new_name.casefold()).any():
            st.warning("This customer is already saved.")
        else:
            append_row(CUSTOMERS_FILE, {"Customer_Name": new_name, "Phone": new_phone.strip()}, CUSTOMER_COLUMNS)
            st.success(f"{new_name} saved. Reload the page to refresh all lists.")
    st.markdown("---")
    st.markdown("#### Saved customers")
    if customers_df.empty:
        st.info("Abhi customer list khaali hai.")
    else:
        display_customers = customers_df.copy()
        display_customers = display_customers.fillna("")
        st.dataframe(display_customers, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Download customer list (CSV)",
            data=display_customers.to_csv(index=False).encode("utf-8-sig"),
            file_name="shiva_traders_customers.csv",
            mime="text/csv",
        )

# ----------------------------- Payments -----------------------------
with tab_payment:
    st.subheader("Record a payment")
    party_names = sorted(set(sales_df["Customer"].dropna().astype(str).tolist()) | set(payments_df["Customer"].dropna().astype(str).tolist()))
    if not party_names:
        st.info("Payment enter karne se pehle ek bill save karein ya customer add karein.")
    else:
        with st.form("payment_form", clear_on_submit=True):
            selected_party = st.selectbox("Customer / party", party_names)
            p1, p2 = st.columns(2)
            with p1:
                amount_paid = st.number_input("Amount received (₹)", min_value=1.0, value=1000.0, step=100.0)
                payment_date = st.date_input("Payment date", value=date.today())
            with p2:
                payment_mode = st.selectbox("Payment method", ["Cash", "UPI / PhonePe", "Bank transfer", "Cheque", "Other"])
                payment_note = st.text_input("Reference / note")
            save_payment = st.form_submit_button("💾 Save payment", type="primary")
        if save_payment:
            payments_now = read_csv(PAYMENTS_FILE, PAYMENT_COLUMNS)
            append_row(PAYMENTS_FILE, {
                "Payment_ID": next_id("PAY", payments_now, "Payment_ID"),
                "Date": f"{payment_date:%Y-%m-%d} {datetime.now():%H:%M}",
                "Customer": selected_party, "Amount_Paid": amount_paid,
                "Payment_Mode": payment_mode, "Remarks": payment_note,
            }, PAYMENT_COLUMNS)
            st.success(f"{money(amount_paid)} payment saved for {selected_party}. Reload to refresh balances.")
    st.markdown("---")
    st.markdown("#### Recent payments")
    if payments_df.empty:
        st.info("No payment entries yet.")
    else:
        recent_payments = payments_df.sort_values("Date", ascending=False).head(20)
        st.dataframe(recent_payments, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Download payment history (CSV)", payments_df.to_csv(index=False).encode("utf-8-sig"), "shiva_traders_payments.csv", "text/csv")

# ----------------------------- Party ledger -----------------------------
with tab_ledger:
    st.subheader("Party ledger & printable statement")
    if balance_df.empty:
        st.info("Ledger dikhane ke liye pehle bill ya payment entry karein.")
    else:
        party = st.selectbox("Select party", sorted(balance_df["Customer"].astype(str).tolist()), key="ledger_party")
        row = balance_df[balance_df["Customer"] == party].iloc[0]
        a, b, c = st.columns(3)
        a.metric("Total billed", money(row["Total_Billed"]))
        b.metric("Total received", money(row["Total_Paid"]))
        c.metric("Balance", money(row["Balance"]), delta="Receivable" if row["Balance"] > 0 else ("Advance / credit" if row["Balance"] < 0 else "Settled"))
        party_sales = sales_df[sales_df["Customer"].astype(str) == party].copy()
        party_payments = payments_df[payments_df["Customer"].astype(str) == party].copy()
        st.markdown("#### Bill history")
        if party_sales.empty:
            st.info("Is party ka bill history nahi hai.")
        else:
            cols = ["Bill_ID", "Date", "Variety", "Bags", "Weight_Kg", "Rate_Per_Kg", "Gross_Amount", "Commission_Amt", "Labour_Charges", "Net_Bill_Amount"]
            st.dataframe(party_sales[cols], use_container_width=True, hide_index=True)
        st.markdown("#### Payment history")
        if party_payments.empty:
            st.info("Is party ki payment entry nahi hai.")
        else:
            st.dataframe(party_payments[["Payment_ID", "Date", "Amount_Paid", "Payment_Mode", "Remarks"]], use_container_width=True, hide_index=True)

        # A print-friendly statement that safely escapes user-entered text.
        sales_rows = ""
        for _, r in party_sales.iterrows():
            sales_rows += (
                "<tr>"
                f"<td>{safe_text(r['Bill_ID'])}</td><td>{safe_text(r['Date'])}</td>"
                f"<td>{safe_text(r['Variety'])}</td><td>{float(r['Bags']):g}</td>"
                f"<td>{float(r['Weight_Kg']):,.2f}</td><td>{money(r['Net_Bill_Amount'])}</td>"
                "</tr>"
            )
        payment_rows = ""
        for _, r in party_payments.iterrows():
            payment_rows += (
                "<tr>"
                f"<td>{safe_text(r['Payment_ID'])}</td><td>{safe_text(r['Date'])}</td>"
                f"<td>{money(r['Amount_Paid'])}</td><td>{safe_text(r['Payment_Mode'])}</td>"
                "</tr>"
            )
        statement_html = f"""
        <!doctype html><html><head><meta charset="utf-8"><style>
        body{{font-family:Arial,sans-serif;color:#172033;padding:18px}}
        .sheet{{max-width:1100px;margin:auto;border:2px solid #164e63;padding:22px;border-radius:10px}}
        h1{{text-align:center;color:#164e63;margin-bottom:4px}} .sub{{text-align:center;color:#526277}}
        .summary{{display:flex;gap:12px;margin:18px 0}} .box{{flex:1;background:#eef6fa;padding:12px;border-radius:8px}}
        table{{width:100%;border-collapse:collapse;margin:12px 0 22px}}th,td{{border:1px solid #cbd5e1;padding:8px;text-align:left;font-size:12px}}
        th{{background:#164e63;color:white}} .due{{font-size:20px;font-weight:bold;color:#b91c1c}}
        button{{background:#047857;color:white;padding:10px 18px;border:0;border-radius:6px;font-weight:bold;cursor:pointer}}
        @media print{{button{{display:none}}.sheet{{border:0}}}}
        </style></head><body><div class="sheet">
        <button onclick="window.print()">🖨️ Print / Save as PDF</button>
        <h1>SHIVA TRADERS</h1><div class="sub">Party Account Statement • {datetime.now():%d-%m-%Y %I:%M %p}</div>
        <h2>Customer: {safe_text(party)}</h2>
        <div class="summary">
          <div class="box"><b>Total billed</b><br>{money(row['Total_Billed'])}</div>
          <div class="box"><b>Total received</b><br>{money(row['Total_Paid'])}</div>
          <div class="box"><b>Balance</b><br><span class="due">{money(row['Balance'])}</span></div>
        </div>
        <h3>Bill history</h3><table><thead><tr><th>Bill ID</th><th>Date</th><th>Item</th><th>Bags</th><th>Weight kg</th><th>Net bill</th></tr></thead><tbody>{sales_rows or '<tr><td colspan="6">No bills</td></tr>'}</tbody></table>
        <h3>Payment history</h3><table><thead><tr><th>Payment ID</th><th>Date</th><th>Amount</th><th>Method</th></tr></thead><tbody>{payment_rows or '<tr><td colspan="4">No payments</td></tr>'}</tbody></table>
        <p>Thank you for doing business with Shiva Traders.</p></div></body></html>
        """
        st.components.v1.html(statement_html, height=650, scrolling=True)
        statement_csv = pd.concat([
            party_sales.assign(Record_Type="Bill").rename(columns={"Net_Bill_Amount": "Amount"})[
                ["Record_Type", "Bill_ID", "Date", "Customer", "Amount", "Remarks"]
            ],
            party_payments.assign(Record_Type="Payment", Amount=party_payments["Amount_Paid"]).rename(columns={"Payment_ID": "Bill_ID"})[
                ["Record_Type", "Bill_ID", "Date", "Customer", "Amount", "Remarks"]
            ],
        ], ignore_index=True)
        st.download_button("⬇️ Download this party's ledger (CSV)", statement_csv.to_csv(index=False).encode("utf-8-sig"), f"{party}_ledger.csv", "text/csv")

# ----------------------------- Reports and export -----------------------------
with tab_reports:
    st.subheader("Reports & data export")
    st.markdown('<div class="section-note">Filter entries by date and download your records for backup or accounting.</div>', unsafe_allow_html=True)
    if not sales_df.empty:
        report = sales_df.copy()
        report["DateParsed"] = pd.to_datetime(report["Date"], errors="coerce")
        valid_dates = report["DateParsed"].dropna()
        if not valid_dates.empty:
            r1, r2 = st.columns(2)
            with r1:
                start_date = st.date_input("From date", value=valid_dates.min().date(), key="report_start")
            with r2:
                end_date = st.date_input("To date", value=valid_dates.max().date(), key="report_end")
            if start_date > end_date:
                st.error("From date should be earlier than or equal to To date.")
                filtered = report.iloc[0:0].copy()
            else:
                filtered = report[
                    (report["DateParsed"].dt.date >= start_date) &
                    (report["DateParsed"].dt.date <= end_date)
                ].copy()
        else:
            filtered = report
        f1, f2, f3 = st.columns(3)
        f1.metric("Bills in range", len(filtered))
        f2.metric("Billed in range", money(filtered["Net_Bill_Amount"].sum()))
        f3.metric("Profit in range", money(filtered["Total_Profit"].sum()))
        st.dataframe(filtered.drop(columns=["DateParsed"], errors="ignore"), use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Download filtered bills (CSV)",
            data=filtered.drop(columns=["DateParsed"], errors="ignore").to_csv(index=False).encode("utf-8-sig"),
            file_name="shiva_traders_filtered_bills.csv",
            mime="text/csv",
        )
    else:
        st.info("Report banane ke liye pehle bill entries add karein.")

    st.markdown("---")
    st.markdown("#### Full backup")
    st.caption("Download all three files and keep them somewhere safe. CSV files contain your business records.")
    d1, d2, d3 = st.columns(3)
    d1.download_button("📦 Sales CSV", sales_df.to_csv(index=False).encode("utf-8-sig"), "mandi_commission_sales.csv", "text/csv", use_container_width=True)
    d2.download_button("💵 Payments CSV", payments_df.to_csv(index=False).encode("utf-8-sig"), "mandi_payments.csv", "text/csv", use_container_width=True)
    d3.download_button("👥 Customers CSV", customers_df.to_csv(index=False).encode("utf-8-sig"), "customers_list.csv", "text/csv", use_container_width=True)

st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#718096;font-size:12px;padding:4px 0 16px">'
    'SHIVA TRADERS • Billing & Accounts • Built for simple day-to-day bookkeeping</div>',
    unsafe_allow_html=True,
)
