import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# ---------- BANK LISTS ----------
SA_BANKS = [
    "ABSA Bank",
    "Standard Bank",
    "First National Bank (FNB)",
    "Nedbank",
    "Capitec Bank"
]

NZ_BANKS = ["Westpac New Zealand"]

BENEFICIARIES = {
    "Linda": {
        "bank": "ABSA Bank"
    }
}

# ---------- DATABASE SETUP ----------
DB_NAME = "payments.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            payer TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            from_country TEXT,
            from_bank TEXT,
            to_bank TEXT,
            beneficiary TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_payment(date_str, payer, amount, description, from_country, from_bank, to_bank, beneficiary):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO payments (date, payer, amount, description, from_country, from_bank, to_bank, beneficiary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (date_str, payer, amount, description, from_country, from_bank, to_bank, beneficiary))
    conn.commit()
    conn.close()

def get_all_payments():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM payments ORDER BY date DESC, id DESC", conn)
    conn.close()
    return df

def delete_payment(payment_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
    conn.commit()
    conn.close()

def update_payment(payment_id, date_str, payer, amount, description, from_country, from_bank, to_bank, beneficiary):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        UPDATE payments
        SET date = ?, payer = ?, amount = ?, description = ?, from_country = ?, from_bank = ?, to_bank = ?, beneficiary = ?
        WHERE id = ?
    """, (date_str, payer, amount, description, from_country, from_bank, to_bank, beneficiary, payment_id))
    conn.commit()
    conn.close()

# ---------- STREAMLIT UI ----------
st.set_page_config(page_title="Payment Tracker: Marece & Charlene to Mother Linda", page_icon="💰")

# Title in smaller font
st.markdown("""
    <h3 style='margin-bottom: 0;'>💰 Payment Tracker: Marece &amp; Charlene to Mother Linda</h3>
""", unsafe_allow_html=True)

# Bold black date caption
st.markdown("<p style='font-size:18px; font-weight:bold; color:black;'>This tracker is from 01 March 2026</p>", unsafe_allow_html=True)

# Arrow instruction in black
st.markdown("<p style='color:black;'>👉 Tap the 2 >> arrows at the top‑left corner for total money paid to mother to date.</p>", unsafe_allow_html=True)

# Initialize DB
init_db()

# Sidebar: quick stats
st.sidebar.header("📊 Summary from 1 March 2026")
df_all = get_all_payments()
if not df_all.empty:
    total_marece = df_all[df_all["payer"] == "Marece"]["amount"].sum()
    total_charlene = df_all[df_all["payer"] == "Charlene"]["amount"].sum()
    total_linda = total_marece + total_charlene

    # Get last payment date for Marece
    marece_df = df_all[df_all["payer"] == "Marece"]
    if not marece_df.empty:
        marece_last_date = pd.to_datetime(marece_df["date"]).max().strftime("%d %B %Y")
    else:
        marece_last_date = "N/A"

    # Marece
    st.sidebar.markdown(f"💰 Marece<br><small>(total paid as of {marece_last_date})</small>", unsafe_allow_html=True)
    st.sidebar.metric(label="", value=f"R{total_marece:,.2f}")

    # Charlene
    st.sidebar.markdown("💰 Charlene<br><small>(yet to capture all the funds paid from 1 March 2026)</small>", unsafe_allow_html=True)
    st.sidebar.metric(label="", value=f"R{total_charlene:,.2f}")

    # Total payments to Mother Linda
    st.sidebar.markdown("💰 Total payments to Mother Linda", unsafe_allow_html=True)
    st.sidebar.metric(label="", value=f"R{total_linda:,.2f}")
else:
    st.sidebar.info("No payments recorded yet.")

# ---------- ADD NEW PAYMENT ----------
# Subheader in smaller font
st.markdown("""
    <h4 style='margin-top: 1rem;'>➕ Record a new payment</h4>
""", unsafe_allow_html=True)

with st.form("add_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        payment_date = st.date_input("Date", value=date.today())
    with col2:
        payer = st.selectbox("Payer", ["Marece", "Charlene"])
    with col3:
        amount = st.number_input("Amount (ZAR)", min_value=0.00, value=0.00, step=0.01, format="%.2f")

    description = st.text_input("Description (optional)", placeholder="e.g., groceries, rent, dinner...")

    st.markdown("### Bank Details")

    from_country = st.selectbox("Paid FROM Country", ["South Africa", "New Zealand"])

    # --- FIXED LOGIC ---
    if from_country == "New Zealand":
        from_bank = st.selectbox("Paid FROM Bank", ["Westpac New Zealand"])
    else:
        from_bank = st.selectbox("Paid FROM Bank", SA_BANKS)

    # Beneficiary bank ALWAYS ABSA
    to_bank = st.selectbox("Paid TO Bank (Beneficiary Bank)", ["ABSA Bank"])

    beneficiary = st.selectbox("Beneficiary", list(BENEFICIARIES.keys()))

    submitted = st.form_submit_button("💾 Add Payment")
    if submitted:
        if amount <= 0:
            st.error("Amount must be greater than 0.")
        else:
            add_payment(
                payment_date.isoformat(),
                payer,
                amount,
                description,
                from_country,
                from_bank,
                to_bank,
                beneficiary
            )
            st.success("Payment added!")
            st.rerun()

# ---------- DISPLAY & MANAGE PAYMENTS ----------
st.subheader("📋 Payment history")

df = get_all_payments()

if df.empty:
    st.info("No payments yet. Use the form above to add one.")
else:
    display_cols = [
        "id", "date", "payer", "amount", "description",
        "from_country", "from_bank", "to_bank", "beneficiary"
    ]

    st.dataframe(
        df[display_cols].style.format({"amount": "R{:.2f}"}),
        width="stretch",
        hide_index=True,
    )

    # ---------- CLEAN CSV EXPORT ----------
    export_df = df.copy()
    export_df = export_df.rename(columns={
        "date": "Date",
        "payer": "Payer",
        "amount": "Amount (ZAR)",
        "description": "Description",
        "from_country": "From Country",
        "from_bank": "From Bank",
        "to_bank": "To Bank",
        "beneficiary": "Beneficiary"
    })

    export_df["Amount (ZAR)"] = export_df["Amount (ZAR)"].apply(lambda x: f"R {x:,.2f}")

    export_df = export_df[[
        "Date", "Payer", "Amount (ZAR)", "Description",
        "From Country", "From Bank", "To Bank", "Beneficiary"
    ]]

    csv_data = export_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download clean CSV",
        data=csv_data,
        file_name="payments_clean.csv",
        mime="text/csv",
    )

    # ---------- EDIT / DELETE ----------
    st.subheader("✏️ Edit or delete a payment")
    payment_ids = df["id"].tolist()
    selected_id = st.selectbox("Select payment ID to edit/delete", payment_ids, key="select_id")

    selected_row = df[df["id"] == selected_id].iloc[0]

    col_edit, col_del = st.columns([3, 1])

    with col_edit:
        with st.expander(f"Edit payment #{selected_id}", expanded=False):
            with st.form("edit_form"):
                new_date = st.date_input("Date", value=pd.to_datetime(selected_row["date"]).date())
                new_payer = st.selectbox("Payer", ["Marece", "Charlene"], index=0 if selected_row["payer"] == "Marece" else 1)
                new_amount = st.number_input("Amount (ZAR)", min_value=0.00, value=float(selected_row["amount"]), step=0.01, format="%.2f")
                new_desc = st.text_input("Description", value=selected_row["description"] if selected_row["description"] else "")
                new_from_country = st.selectbox("Paid FROM Country", ["South Africa", "New Zealand"], index=0 if selected_row["from_country"] == "South Africa" else 1)

                # --- FIXED EDIT LOGIC ---
                if new_from_country == "New Zealand":
                    new_from_bank = st.selectbox("Paid FROM Bank", ["Westpac New Zealand"], index=0)
                else:
                    if selected_row["from_bank"] in SA_BANKS:
                        default_index = SA_BANKS.index(selected_row["from_bank"])
                    else:
                        default_index = 0
                    new_from_bank = st.selectbox("Paid FROM Bank", SA_BANKS, index=default_index)

                new_to_bank = st.selectbox("Paid TO Bank", ["ABSA Bank"], index=0)
                new_beneficiary = st.selectbox("Beneficiary", list(BENEFICIARIES.keys()), index=0)

                if st.form_submit_button("💾 Save changes"):
                    update_payment(
                        selected_id,
                        new_date.isoformat(),
                        new_payer,
                        new_amount,
                        new_desc,
                        new_from_country,
                        new_from_bank,
                        new_to_bank,
                        new_beneficiary
                    )
                    st.success("Payment updated!")
                    st.rerun()

    with col_del:
        if st.button("🗑️ Delete this payment", key="delete_btn"):
            delete_payment(selected_id)
            st.success(f"Payment #{selected_id} deleted.")
            st.rerun()

# ---------- FILTER ----------
st.subheader("🔍 Filter payments by payer")
filter_payer = st.radio("Show only:", ["All", "Marece", "Charlene"], horizontal=True)
if filter_payer != "All":
    filtered_df = df[df["payer"] == filter_payer]
else:
    filtered_df = df

if not filtered_df.empty:
    st.dataframe(
        filtered_df[display_cols].style.format({"amount": "R{:.2f}"}),
        width="stretch",
        hide_index=True,
    )
else:
    st.info("No payments for this filter.")

# Footer
st.caption("💡 Tip: All payments are stored locally in 'payments.db' (SQLite).")
st.caption("Developed by Marece Wenhold, 2026, Paekākāriki, New Zealand.")
