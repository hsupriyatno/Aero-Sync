import streamlit as st
import sys
import os
import pandas as pd
import io
from datetime import date
import importlib.util

# --- KONEKSI KE DATABASE ---
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
file_path = os.path.join(parent_dir, "database_logic.py") # Pastikan sudah pakai underscore

spec = importlib.util.spec_from_file_location("database_logic", file_path)
db_logic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db_logic)

if not st.session_state.get('logged_in'):
    st.warning("Silakan login di halaman utama.")
    st.stop()

st.title("📊 Aircraft Utilization Record")

# --- 1. LIVE STATISTICS (Ringkasan Otomatis) ---
df = db_logic.get_utilization_data()

if not df.empty:
    st.write("### ✈️ Fleet Overview")
    c_stat1, c_stat2, c_stat3 = st.columns(3)
    
    total_fh = df['flight_hours'].sum()
    total_fc = df['flight_cycles'].sum()
    unique_ac = df['tail_number'].nunique()
    
    c_stat1.metric("Total Flight Hours", f"{total_fh:.1f}")
    c_stat2.metric("Total Flight Cycles", f"{total_fc}")
    c_stat3.metric("Aircraft Active", unique_ac)
    st.write("---")

# --- 2. FORM INPUT ---
with st.expander("➕ Add New Flight Log", expanded=False): # Dibuat tertutup biar rapi
    c1, c2 = st.columns(2)
    with c1:
        dt = st.date_input("Date", date.today())
        tp = st.selectbox("Aircraft Type", db_logic.get_aircraft_types())
        tn = st.selectbox("Tail Number", db_logic.get_tail_numbers(tp))
    with c2:
        fh = st.number_input("Flight Hours", min_value=0.0, step=0.1)
        fc = st.number_input("Flight Cycles", min_value=0, step=1)
        rm = st.text_input("Remarks")

    if st.button("Save to Database", use_container_width=True):
        db_logic.save_utilization(str(dt), tp, tn, fh, fc, rm)
        st.success(f"Data {tn} berhasil disimpan!")
        st.rerun()

# --- 3. DATA HISTORY & EXPORT ---
st.subheader("History Records")
if not df.empty:
    st.dataframe(df.drop(columns=['id']), use_container_width=True)
    
    # Tombol Export ke Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Utilization_Report')
    
    st.download_button(
        label="📥 Download All Records (Excel)",
        data=buffer.getvalue(),
        file_name=f"AeroSynch_Report_{date.today()}.xlsx",
        mime="application/vnd.ms-excel",
        use_container_width=True
    )
else:
    st.info("Belum ada data tersimpan.")