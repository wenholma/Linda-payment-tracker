import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# Page config
st.set_page_config(
    page_title="Payment Tracker: Marece & Charlene to Mother Linda",
    page_icon="💰",
)

# Title and caption
st.title("💰 Payment Tracker: Marece & Charlene to Mother Linda")
st.caption("Marece is a New Zealand Citizen based in New Zealand. Charlene and Mother Linda are South African Citizens based in South Africa.")

# Database setup
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
            from_country TEXT NOT NULL,
            from_bank TEXT NOT NULL,
            to_bank TEXT NOT NULL,
            beneficiary TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Helper functions
def add_payment(date_str, payer, amount, description, from_country, from_bank, to_bank, beneficiary):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO payments (date, payer, amount, description, from_country, from_bank, to_bank, beneficiary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (date_str, payer, amount, description, from_country, from_bank, to_bank, beneficiary))
    conn.commit()
    conn.close()

def update_payment(payment_id, date_str, payer, amount, description, from_country, from_bank, to_bank, beneficiary):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        UPDATE payments
        SET date=?, payer=?, amount=?, description=?, from_country=?, from_bank=?, to_bank=?, beneficiary=?
        WHERE id=?
    """, (date_str, payer, amount, description, from_country, from_bank, to_bank, beneficiary, payment_id))
    conn.commit()
    conn.close()

def delete_payment(payment_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM payments WHERE id=?", (payment_id,))
    conn.commit()
    conn.close()

def get_payments_df():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM payments ORDER BY date DESC, id DESC", conn)
    conn.close()
    return df

# Sidebar totals
df_all = get_payments_df()
if not df_all.empty:
    marece_total = df_all[df_all["payer"] == "Marece"]["amount"].sum()
    charlene_total = df_all[df_all["payer"] == "Charlene"]["amount"].sum()
    total = marece_total + charlene_total
else:
    marece_total = charlene_total = total = 0.0

st.sidebar.header("Summary")
st.sidebar.metric("Total paid by MARECE", f"R {marece_total:,.2f}")
st.sidebar.metric("Total paid by CHARLENE", f"R {charlene_total:,.2f}")
st.sidebar.metric("Total received by MOTHER LINDA", f"R {total:,.2f}")

# ----- Add payment section -----
st.header("➕ Record a new payment")

with st.form("add_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        add_date = st.date_input("Date", value=date.today())
        add_payer = st.selectbox("Payer", ["Marece", "Charlene"])
        add_amount = st.number_input("Amount (ZAR)", min_value=0.0, step=0.01, format="%.2f")
    with col2:
        add_description = st.text_input("Description (optional)")
        add_from_country = st.selectbox("Paid FROM Country", ["South Africa", "New Zealand"])
        if add_from_country == "New Zealand":
            add_from_bank = st.selectbox("Paid FROM Bank", ["Westpac New Zealand"])
        else:
            add_from_bank = st.selectbox("Paid FROM Bank", [
                "ABSA Bank", "Standard Bank", "First National Bank (FNB)", "Nedbank", "Capitec Bank"
            ])
        add_to_bank = st.selectbox("Paid TO Bank (Beneficiary Bank)", ["ABSA Bank"])
        add_beneficiary = st.selectbox("Beneficiary", ["Linda"])
    
    submitted = st.form_submit_button("💾 Add Payment")
    if submitted:
        if add_amount <= 0:
            st.error("Amount must be greater than 0.")
        else:
            add_payment(
                add_date.isoformat(),
                add_payer,
                add_amount,
                add_description,
                add_from_country,
                add_from_bank,
                add_to_bank,
                add_beneficiary
            )
            st.success("Payment added!")
            st.rerun()

# ----- Payment history section -----
st.header("📋 Payment history")
df = get_payments_df()
if df.empty:
    st.info("No payments recorded yet.")
else:
    # Display dataframe with formatted amount
    display_df = df.copy()
    display_df["amount_display"] = display_df["amount"].apply(lambda x: f"R {x:,.2f}")
    display_cols = ["id", "date", "payer", "amount_display", "description", "from_country", "from_bank", "to_bank", "beneficiary"]
    display_df = display_df[display_cols].rename(columns={"amount_display": "Amount"})
    st.dataframe(display_df, use_container_width=True)
    
    # Download CSV
    csv_df = df[["date", "payer", "amount", "description", "from_country", "from_bank", "to_bank", "beneficiary"]].copy()
    csv_df = csv_df.rename(columns={
        "date": "Date",
        "payer": "Payer",
        "amount": "Amount (ZAR)",
        "description": "Description",
        "from_country": "From Country",
        "from_bank": "From Bank",
        "to_bank": "To Bank",
        "beneficiary": "Beneficiary"
    })
    csv_df["Amount (ZAR)"] = csv_df["Amount (ZAR)"].apply(lambda x: f"R {x:,.2f}")
    csv = csv_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download clean CSV", data=csv, file_name="payments.csv", mime="text/csv")

# ----- Edit or delete section -----
st.header("✏️ Edit or delete a payment")
if df.empty:
    st.info("No payments to edit.")
else:
    payment_ids = df["id"].tolist()
    selected_id = st.selectbox("Select payment ID", payment_ids, key="edit_select")
    selected_row = df[df["id"] == selected_id].iloc[0]
    
    with st.expander(f"Edit payment #{selected_id}"):
        # Store original data in session state for this payment
        if "edit_orig_id" not in st.session_state or st.session_state.edit_orig_id != selected_id:
            st.session_state.edit_orig_id = selected_id
            st.session_state.edit_date = date.fromisoformat(selected_row["date"])
            st.session_state.edit_payer = selected_row["payer"]
            st.session_state.edit_amount = selected_row["amount"]
            st.session_state.edit_description = selected_row["description"] if selected_row["description"] else ""
            st.session_state.edit_from_country = selected_row["from_country"]
            st.session_state.edit_from_bank = selected_row["from_bank"]
            st.session_state.edit_to_bank = selected_row["to_bank"]
            st.session_state.edit_beneficiary = selected_row["beneficiary"]
        
        col1, col2 = st.columns(2)
        with col1:
            edit_date = st.date_input("Date", value=st.session_state.edit_date, key="edit_date")
            edit_payer = st.selectbox("Payer", ["Marece", "Charlene"], index=0 if st.session_state.edit_payer == "Marece" else 1, key="edit_payer")
            edit_amount = st.number_input("Amount (ZAR)", min_value=0.0, step=0.01, format="%.2f", value=st.session_state.edit_amount, key="edit_amount")
        with col2:
            edit_description = st.text_input("Description", value=st.session_state.edit_description, key="edit_description")
            edit_from_country = st.selectbox("Paid FROM Country", ["South Africa", "New Zealand"], index=0 if st.session_state.edit_from_country == "South Africa" else 1, key="edit_from_country")
            
            # Dynamic from_bank based on selected country
            if edit_from_country == "New Zealand":
                bank_options = ["Westpac New Zealand"]
            else:
                bank_options = ["ABSA Bank", "Standard Bank", "First National Bank (FNB)", "Nedbank", "Capitec Bank"]
            # Ensure current from_bank is valid for the selected country; if not, default to first option
            current_bank = st.session_state.edit_from_bank
            if current_bank not in bank_options:
                current_bank = bank_options[0]
            edit_from_bank = st.selectbox("Paid FROM Bank", bank_options, index=bank_options.index(current_bank), key="edit_from_bank")
            
            edit_to_bank = st.selectbox("Paid TO Bank (Beneficiary Bank)", ["ABSA Bank"], key="edit_to_bank")
            edit_beneficiary = st.selectbox("Beneficiary", ["Linda"], key="edit_beneficiary")
        
        col_save, col_del = st.columns(2)
        with col_save:
            if st.button("💾 Save changes", key="save_edit"):
                if edit_amount <= 0:
                    st.error("Amount must be greater than 0.")
                else:
                    update_payment(
                        selected_id,
                        edit_date.isoformat(),
                        edit_payer,
                        edit_amount,
                        edit_description,
                        edit_from_country,
                        edit_from_bank,
                        edit_to_bank,
                        edit_beneficiary
                    )
                    st.success("Payment updated!")
                    st.rerun()
        with col_del:
            if st.button("🗑️ Delete this payment", key="delete_payment"):
                delete_payment(selected_id)
                st.success("Payment deleted!")
                st.rerun()

# ----- Filter section -----
st.header("🔍 Filter payments by payer")
filter_choice = st.radio("Show", ["All", "Marece", "Charlene"], horizontal=True)
df_filtered = get_payments_df()
if not df_filtered.empty:
    if filter_choice != "All":
        df_filtered = df_filtered[df_filtered["payer"] == filter_choice]
    if df_filtered.empty:
        st.info("No payments for this payer.")
    else:
        display_filtered = df_filtered.copy()
        display_filtered["amount_display"] = display_filtered["amount"].apply(lambda x: f"R {x:,.2f}")
        display_filtered = display_filtered[["id", "date", "payer", "amount_display", "description", "from_country", "from_bank", "to_bank", "beneficiary"]]
        display_filtered = display_filtered.rename(columns={"amount_display": "Amount"})
        st.dataframe(display_filtered, use_container_width=True)
