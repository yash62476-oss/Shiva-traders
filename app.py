# Mobile pull-to-refresh rokne ke liye JavaScript trick
st.markdown(
    """
    <script>
    document.body.style.overscrollBehaviorY = 'none';
    window.addEventListener('touchmove', function(e) {
        // Agar page top par hai aur user aur upar khich raha hai toh default roko
        if (window.pageYOffset <= 0 && e.scale !== 1) {
            // allow normal scrolling inside containers
        }
    }, { passive: false });
    </script>
    """,
    unsafe_allow_html=True,
)
from datetime import datetime
import os
import urllib.parse
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(page_title="Shiva Traders", page_icon="🏢", layout="wide")

# High-Contrast Styling
st.markdown(
    """
    <style>
    .stApp { background-color: #0f172a !important; color: #ffffff !important; }
    label, label p, div[data-testid="stMarkdownContainer"] p { color: #ffffff !important; font-size: 16px !important; font-weight: 700 !important; }
    h1, h2, h3, h4, .stSubheader { color: #38bdf8 !important; font-weight: 800 !important; }
    input { color: #ffffff !important; background-color: #1e293b !important; border: 1px solid #64748b !important; border-radius: 6px !important; }
    button[data-baseweb="tab"] { background-color: #334155 !important; border-radius: 8px !important; padding: 10px 18px !important; margin-right: 6px !important; }
    button[data-baseweb="tab"] p { color: #f8fafc !important; font-weight: bold !important; font-size: 15px !important; }
    button[data-baseweb="tab"][aria-selected="true"] { background: #2563eb !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #ffffff !important; }
    [data-testid="stMetricLabel"] p { color: #cbd5e1 !important; }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; font-weight: 800 !important; }
    </style>
""",
    unsafe_allow_html=True,
)

TRANSACTIONS_FILE = "mandi_commission_sales.csv"
PAYMENTS_FILE = "mandi_payments.csv"

if not os.path.exists(TRANSACTIONS_FILE):
  df_tx = pd.DataFrame(
      columns=[
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
  )
  df_tx.to_csv(TRANSACTIONS_FILE, index=False)

if not os.path.exists(PAYMENTS_FILE):
  df_pay = pd.DataFrame(
      columns=["Date", "Customer", "Amount_Paid", "Payment_Mode", "Remarks"]
  )
  df_pay.to_csv(PAYMENTS_FILE, index=False)

st.title("🏢 SHIVA TRADERS")

tab1, tab2, tab3, tab4 = st.tabs([
    "📑 नया बिल (New Bill)",
    "💵 जमा पैसा (Payment Entry)",
    "🖨️ पर्ची प्रिंट (Print Bill)",
    "📊 पूरा रजिस्टर (All Summary)",
])

# ==========================================
# TAB 1: NEW BILL
# ==========================================
with tab1:
  st.subheader("1. नया बिल और आढ़त entries")

  # Load existing transactions to fetch previous customers
  df_tx_all = (
      pd.read_csv(TRANSACTIONS_FILE)
      if os.path.exists(TRANSACTIONS_FILE)
      else pd.DataFrame()
  )
  existing_customers = (
      sorted(df_tx_all["Customer"].dropna().unique().tolist())
      if not df_tx_all.empty and "Customer" in df_tx_all.columns
      else []
  )

  col1, col2, col3 = st.columns(3)

  with col1:
    cust_mode = st.radio(
        "ग्राहक का प्रकार:",
        ["पुराना ग्राहक (Existing)", "नया ग्राहक (New)"],
        horizontal=True,
    )

    if cust_mode == "पुराना ग्राहक (Existing)" and existing_customers:
      cust_name = st.selectbox("सूची से ग्राहक चुनें:", existing_customers)
      # Fetch last used phone number for this customer automatically
      last_phone = ""
      if not df_tx_all.empty:
        cust_rows = df_tx_all[df_tx_all["Customer"] == cust_name]
        if not cust_rows.empty and "Phone" in cust_rows.columns:
          valid_phones = cust_rows["Phone"].dropna()
          if not valid_phones.empty:
            last_phone = str(valid_phones.iloc[-1])
      cust_phone = st.text_input(
          "फोन नंबर (WhatsApp / SMS):", value=last_phone
      ).strip()
    else:
      cust_name = st.text_input("नया ग्राहक / पार्टी का नाम:").strip()
      cust_phone = st.text_input("फोन नंबर (WhatsApp / SMS):").strip()

    variety = st.text_input("आइटम / विवरण:", value="3797")

  with col2:
    bags = st.number_input(
        "बोरी / कट्टे (Bags):", min_value=1, value=50, step=1
    )
    weight_kg = st.number_input(
        "कुल वजन (Kg):", min_value=1.0, value=2500.0, step=10.0
    )
    rate_kg = st.number_input(
        "रेट (₹ per Kg):", min_value=0.5, value=12.0, step=0.5
    )

  with col3:
    comm_percent = st.number_input(
        "कमीशन (%):", min_value=0.0, value=1.0, step=0.25
    )
    labour_per_bag = st.number_input(
        "मजदूरी / खर्चा (₹ प्रति बोरी):", min_value=0.0, value=4.0, step=0.5
    )
    remarks = st.text_input("गाड़ी नंबर / रिमार्क्स:")

  gross_amount = weight_kg * rate_kg
  comm_amount = (gross_amount * comm_percent) / 100.0
  labour_total = bags * labour_per_bag
  total_profit = comm_amount + labour_total
  net_bill_amount = gross_amount + total_profit

  st.markdown("---")
  st.subheader("📊 हिसाब-किताब breakdown:")

  c1, c2, c3, c4 = st.columns(4)
  c1.metric("मूल रकम (Gross)", f"₹{gross_amount:,.2f}")
  c2.metric(f"कमीशन ({comm_percent}%)", f"₹{comm_amount:,.2f}")
  c3.metric(f"मजदूरी ({bags} बोरी)", f"₹{labour_total:,.2f}")
  c4.metric("🔥 कुल प्रॉफिट", f"₹{total_profit:,.2f}")

  st.markdown(f"## 💸 Party Net Bill Amount: ₹{net_bill_amount:,.2f}")

  if st.button("पर्ची सेव करें (Save Bill)", type="primary"):
    if not cust_name:
      st.error("कृपया ग्राहक का नाम भरें!")
    else:
      new_data = pd.DataFrame([{
          "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
          "Customer": cust_name,
          "Phone": cust_phone,
          "Variety": variety,
          "Bags": bags,
          "Weight_Kg": weight_kg,
          "Rate_Per_Kg": rate_kg,
          "Gross_Amount": gross_amount,
          "Commission_Percent": comm_percent,
          "Commission_Amt": comm_amount,
          "Labour_Charges": labour_total,
          "Total_Profit": total_profit,
          "Net_Bill_Amount": net_bill_amount,
          "Remarks": remarks,
      }])
      new_data.to_csv(TRANSACTIONS_FILE, mode="a", header=False, index=False)
      st.success(f"✅ {cust_name} का बिल सेव हो गया!")

      # WhatsApp Link Generation
      if cust_phone:
        clean_phone = "".join(filter(str.isdigit, str(cust_phone)))
        if len(clean_phone) == 10:
          clean_phone = "91" + clean_phone

        sms_text = f"🏢 *SHIVA TRADERS*\n\nNamaste {cust_name} ji,\nAapka naya bill generate ho gaya hai:\n\n• Item: {variety}\n• Bori: {bags}\n• Wt: {weight_kg} kg\n• Rate: ₹{rate_kg}/kg\n• Total Bill: ₹{net_bill_amount:,.2f}\n\nDhanyawad!"
        encoded_msg = urllib.parse.quote(sms_text)
        wa_url = f"https://wa.me/{clean_phone}?text={encoded_msg}"

        st.markdown(f"### 📲 ग्राहक को मैसेज भेजें:")
        st.markdown(f"[👉 Click Here to Send WhatsApp Message]({wa_url})")

# ==========================================
# TAB 2: PAYMENT ENTRY
# ==========================================
with tab2:
  st.subheader("2. ग्राहक से जमा पैसा (Payment Entry)")

  df_tx = pd.read_csv(TRANSACTIONS_FILE) if os.path.exists(TRANSACTIONS_FILE) else pd.DataFrame()
  existing_customers = (
      sorted(df_tx["Customer"].dropna().unique().tolist())
      if not df_tx.empty and "Customer" in df_tx.columns
      else []
  )

  if existing_customers:
    pay_cust = st.selectbox("ग्राहक चुनें:", existing_customers)
    pay_amount = st.number_input(
        "कितने पैसे मिले (₹):", min_value=1.0, value=1000.0, step=100.0
    )
    pay_mode = st.selectbox(
        "माध्यम:", ["Cash (नकद)", "UPI / PhonePe", "Bank Transfer", "Cheque"]
    )
    pay_remark = st.text_input("नोट / टिप्पणी:")

    if st.button("पेमेंट सेव करें", type="primary"):
      new_pay = pd.DataFrame([{
          "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
          "Customer": pay_cust,
          "Amount_Paid": pay_amount,
          "Payment_Mode": pay_mode,
          "Remarks": pay_remark,
      }])
      new_pay.to_csv(PAYMENTS_FILE, mode="a", header=False, index=False)
      st.success(
          f"✅ ₹{pay_amount} की जमा एंट्री हो गई! (पार्टी: {pay_cust})"
      )
  else:
    st.info("अभी तक कोई पार्टी दर्ज नहीं है।")

# ==========================================
# TAB 3: PRINT PARCHI
# ==========================================
with tab3:
  st.subheader("3. ग्राहक पर्ची व बिल प्रिंट")

  df_tx = pd.read_csv(TRANSACTIONS_FILE) if os.path.exists(TRANSACTIONS_FILE) else pd.DataFrame()
  df_pay = pd.read_csv(PAYMENTS_FILE) if os.path.exists(PAYMENTS_FILE) else pd.DataFrame()

  existing_customers = (
      sorted(df_tx["Customer"].dropna().unique().tolist())
      if not df_tx.empty and "Customer" in df_tx.columns
      else []
  )

  if existing_customers:
    selected_cust = st.selectbox(
        "जिस ग्राहक की पर्ची प्रिंट करनी है चुनें:", existing_customers
    )

    cust_sales = (
        df_tx[df_tx["Customer"] == selected_cust]
        if not df_tx.empty and "Customer" in df_tx.columns
        else pd.DataFrame()
    )
    cust_payments = (
        df_pay[df_pay["Customer"] == selected_cust]
        if not df_pay.empty and "Customer" in df_pay.columns
        else pd.DataFrame()
    )

    total_bill = (
        cust_sales["Net_Bill_Amount"].sum() if not cust_sales.empty else 0.0
    )
    total_profit_earned = (
        cust_sales["Total_Profit"].sum() if not cust_sales.empty else 0.0
    )
    total_paid = (
        cust_payments["Amount_Paid"].sum() if not cust_payments.empty else 0.0
    )
    balance = total_bill - total_paid

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("कुल बिल रकम", f"₹{total_bill:,.2f}")
    m2.metric("कुल जमा किया", f"₹{total_paid:,.2f}")
    m3.metric("🚨 कुल बकाया (Udhaar)", f"₹{balance:,.2f}")
    m4.metric("📈 इस पार्टी से कुल प्रॉफिट", f"₹{total_profit_earned:,.2f}")

    st.markdown("---")

    sales_rows = ""
    if not cust_sales.empty:
      for idx, row in cust_sales.iterrows():
        sales_rows += f"""
            <tr>
                <td>{row['Date']}</td>
                <td>{row['Variety']}</td>
                <td>{row['Bags']}</td>
                <td>{row['Weight_Kg']} Kg</td>
                <td>₹{row['Rate_Per_Kg']}</td>
                <td>₹{row['Gross_Amount']:,.2f}</td>
                <td>₹{row['Commission_Amt']:,.2f} ({row['Commission_Percent']}%)</td>
                <td>₹{row['Labour_Charges']:,.2f}</td>
                <td style="color:#1d4ed8; font-weight:bold;">₹{row['Net_Bill_Amount']:,.2f}</td>
            </tr>
            """

    payment_rows = ""
    if not cust_payments.empty:
      for idx, row in cust_payments.iterrows():
        payment_rows += f"""
                <tr>
                    <td>{row['Date']}</td>
                    <td style="color:#15803d; font-weight:bold;">₹{row['Amount_Paid']:,.2f}</td>
                    <td>{row['Payment_Mode']}</td>
                    <td>{row['Remarks']}</td>
                </tr>
                """
    else:
      payment_rows = "<tr><td colspan='4'>कोई जमा राशि नहीं है।</td></tr>"

    html_parchi = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 10px; color: #000000; background-color: #ffffff; }}
                .bill-card {{ border: 2px solid #1e3a8a; padding: 20px; border-radius: 10px; width: 100%; box-sizing: border-box; background: #ffffff; }}
                .header-title {{ text-align: center; color: #1e3a8a; font-size: 26px; font-weight: 800; margin-bottom: 5px; border-bottom: 2px solid #2563eb; padding-bottom: 5px; }}
                .data-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                .data-table th, .data-table td {{ border: 1px solid #475569; padding: 8px; text-align: center; font-size: 14px; color: #000000; }}
                .data-table th {{ background: #2563eb; color: #ffffff; font-weight: bold; }}
                .total-box {{ margin-top: 15px; padding: 12px; background-color: #f1f5f9; border-radius: 6px; border-left: 5px solid #2563eb; font-size: 16px; font-weight: bold; text-align: right; }}
                .btn-print {{ background: #16a34a; color: #ffffff; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; margin-bottom: 15px; }}
                @media print {{ .btn-print {{ display: none; }} }}
            </style>
        </head>
        <body>
            <button class="btn-print" onclick="window.print()">🖨️ पर्ची प्रिंट / PDF निकालें</button>
            <div class="bill-card">
                <div class="header-title">SHIVA TRADERS</div>
                <div style="display:flex; justify-content:space-between; margin-top:10px; font-size:15px;">
                    <p><b>ग्राहक नाम:</b> <span style="color:#1d4ed8;">{selected_cust}</span></p>
                    <p><b>दिनांक:</b> {datetime.now().strftime("%d-%m-%Y %H:%M")}</p>
                </div>
                
                <h3 style="color:#1e3a8a; margin-top:15px;">📦 बिक्री विवरण:</h3>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>तारीख</th>
                            <th>विवरण</th>
                            <th>बोरी</th>
                            <th>वजन</th>
                            <th>रेट</th>
                            <th>मूल रकम</th>
                            <th>कमीशन</th>
                            <th>मजदूरी</th>
                            <th>कुल बिल</th>
                        </tr>
                    </thead>
                    <tbody>{sales_rows}</tbody>
                </table>

                <h3 style="color:#1e3a8a; margin-top:15px;">💵 जमा राशि विवरण:</h3>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>तारीख</th>
                            <th>जमा रकम</th>
                            <th>माध्यम</th>
                            <th>नोट</th>
                        </tr>
                    </thead>
                    <tbody>{payment_rows}</tbody>
                </table>

                <div class="total-box">
                    <p style="margin:4px 0;">कुल बिल रकम: ₹{total_bill:,.2f}</p>
                    <p style="margin:4px 0; color:#16a34a;">कुल जमा रकम: ₹{total_paid:,.2f}</p>
                    <p style="font-size:18px; color:#dc2626; margin:4px 0 0 0;">🚨 कुल शेष बकाया: ₹{balance:,.2f}</p>
                </div>
            </div>
        </body>
        </html>
        """
    st.components.v1.html(html_parchi, height=750, scrolling=True)
  else:
    st.info("प्रिंट करने के लिए कोई डाटा नहीं है।")

# ==========================================
# TAB 4: REGISTER SUMMARY
# ==========================================
with tab4:
  st.subheader("4. Shiva Traders खाता रजिस्टर (Summary)")

  df_tx = pd.read_csv(TRANSACTIONS_FILE) if os.path.exists(TRANSACTIONS_FILE) else pd.DataFrame()

  if not df_tx.empty and "Customer" in df_tx.columns:
    summary_rows_html = ""

    grand_bags = 0
    grand_weight = 0.0
    grand_gross = 0.0
    grand_comm = 0.0
    grand_labour = 0.0
    grand_net = 0.0

    for cust, group in df_tx.groupby("Customer"):
      cust_bags = group["Bags"].sum()
      cust_weight = group["Weight_Kg"].sum()
      cust_gross = group["Gross_Amount"].sum()
      cust_comm = group["Commission_Amt"].sum()
      cust_labour = group["Labour_Charges"].sum()
      cust_net = group["Net_Bill_Amount"].sum()

      grand_bags += cust_bags
      grand_weight += cust_weight
      grand_gross += cust_gross
      grand_comm += cust_comm
      grand_labour += cust_labour
      grand_net += cust_net

      for idx, row in group.iterrows():
        summary_rows_html += f"""
                <tr>
                    <td style="text-align:left;"><b>{row['Customer']}</b></td>
                    <td>{row['Bags']}</td>
                    <td>{row['Weight_Kg']}</td>
                    <td>₹{row['Rate_Per_Kg']}</td>
                    <td>₹{row['Gross_Amount']:,.2f}</td>
                    <td>₹{row['Commission_Amt']:,.2f}</td>
                    <td>₹{row['Labour_Charges']:,.2f}</td>
                    <td style="color:#16a34a; font-weight:bold;">₹{row['Total_Profit']:,.2f}</td>
                    <td style="color:#1d4ed8; font-weight:bold;">₹{row['Net_Bill_Amount']:,.2f}</td>
                </tr>
                """

      summary_rows_html += f"""
            <tr style="background-color: #f1f5f9; font-weight: bold; border-bottom: 2px solid #000000;">
                <td style="text-align:left; color:#1e3a8a;">Total ({cust})</td>
                <td>{cust_bags}</td>
                <td>{cust_weight}</td>
                <td>-</td>
                <td>₹{cust_gross:,.2f}</td>
                <td>₹{cust_comm:,.2f}</td>
                <td>₹{cust_labour:,.2f}</td>
                <td style="color:#16a34a;">₹{(cust_comm + cust_labour):,.2f}</td>
                <td style="color:#1d4ed8;">₹{cust_net:,.2f}</td>
            </tr>
            """

    html_all_register = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 10px; color: #000000; background-color: #ffffff; }}
                .register-box {{ border: 2px solid #1e3a8a; padding: 15px; border-radius: 8px; width: 100%; box-sizing: border-box; }}
                .header-title {{ text-align: center; color: #1e3a8a; font-size: 24px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }}
                .reg-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                .reg-table th, .reg-table td {{ border: 1px solid #475569; padding: 6px; text-align: center; font-size: 13px; color: #000000; }}
                .reg-table th {{ background-color: #2563eb; color: #ffffff; font-weight: bold; }}
                .grand-total {{ background-color: #0f172a; color: #ffffff; font-size: 14px; font-weight: bold; }}
                .btn-print {{ background-color: #2563eb; color: #ffffff; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; margin-bottom: 15px; }}
                @media print {{ .btn-print {{ display: none; }} }}
            </style>
        </head>
        <body>
            <button class="btn-print" onclick="window.print()">🖨️ पूरा रजिस्टर Print / PDF निकालें</button>
            <div class="register-box">
                <div class="header-title">SHIVA TRADERS</div>
                <p style="text-align:right; font-size:13px; color:#475569;"><b>Report Date:</b> {datetime.now().strftime("%d-%m-%Y %H:%M")}</p>
                
                <table class="reg-table">
                    <thead>
                        <tr>
                            <th>पार्टी का नाम</th>
                            <th>बोरी</th>
                            <th>वजन (Kg)</th>
                            <th>रेट (₹)</th>
                            <th>मूल रकम</th>
                            <th>कमीशन (₹)</th>
                            <th>मजदूरी (₹)</th>
                            <th>कुल प्रॉफिट (₹)</th>
                            <th>अंतिम बिल बनाते वक्त</th>
                        </tr>
                    </thead>
                    <tbody>
                        {summary_rows_html}
                        <tr class="grand-total">
                            <td style="text-align:left; color:#facc15;">GRAND TOTAL</td>
                            <td>{grand_bags}</td>
                            <td>{grand_weight}</td>
                            <td>-</td>
                            <td>₹{grand_gross:,.2f}</td>
                            <td>₹{grand_comm:,.2f}</td>
                            <td>₹{grand_labour:,.2f}</td>
                            <td style="color:#4ade80;">₹{(grand_comm + grand_labour):,.2f}</td>
                            <td style="color:#60a5fa;">₹{grand_net:,.2f}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
    st.components.v1.html(html_all_register, height=800, scrolling=True)
  else:
    st.info("रजिस्टर में दिखाने के लिए अभी कोई डेटा नहीं है।")
