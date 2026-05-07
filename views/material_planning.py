import streamlit as st
import pandas as pd
from datetime import datetime
from database import create_connection
import numpy as np
from scipy.stats import poisson

def show_scheduled_removal():
    st.subheader("📅 Scheduled Component Removal Forecast")
    
    col1, col2 = st.columns(2)
    threshold_hrs = col1.number_input("Threshold Remaining Hours:", value=500)
    threshold_days = col2.number_input("Threshold Remaining Days:", value=90)

    conn = create_connection()
    
    # Query ini sudah menggunakan nama kolom yang benar: tsn_at_install
    query = """
        SELECT 
            i.ac_reg, i.component_name, i.part_number, i.serial_number,
            COALESCE(i.tsn_at_install, 0) as tsn_at_install,
            i.install_date,
            COALESCE(m.tbo_hours, 0) as tbo_h, 
            COALESCE(m.tbo_calendar, 0) as tbo_c,
            (SELECT COALESCE(SUM(flight_hours), 0) FROM aml_utilization WHERE ac_reg = i.ac_reg) as total_flown
        FROM installed_components i
        LEFT JOIN master_part_number m ON i.part_number = m.part_number
    """
    
    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Error Database: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()

    if not df.empty:
        forecast_list = []
        today = datetime.now().date()

        for _, row in df.iterrows():
            # Logika: TSN saat pasang + Total jam terbang sejak terpasang
            used_hrs = row['tsn_at_install'] + row['total_flown']
            
            # Hitung Remaining Hours
            if row['tbo_h'] > 0:
                rem_hrs = row['tbo_h'] - used_hrs
            else:
                rem_hrs = 999999 # Jika TBO tidak diset, anggap aman
            
            # Hitung Remaining Days (Placeholder jika belum ada tanggal install)
            rem_days = 99999
            if row['install_date'] and row['tbo_c'] > 0:
                try:
                    install_dt = pd.to_datetime(row['install_date']).date()
                    days_used = (today - install_dt).days
                    rem_days = (row['tbo_c'] * 30.44) - days_used
                except:
                    pass

            # Filter Threshold
            if rem_hrs <= threshold_hrs or rem_days <= threshold_days:
                forecast_list.append({
                    "A/C": row['ac_reg'],
                    "Component": row['component_name'],
                    "P/N": row['part_number'],
                    "S/N": row['serial_number'],
                    "Used Hrs": round(used_hrs, 2),
                    "Rem Hrs": round(rem_hrs, 2),
                    "Rem Days": int(rem_days) if rem_days != 99999 else "-",
                    "Status": "🔴 CRITICAL" if rem_hrs < 100 else "🟡 WARNING"
                })

        if forecast_list:
            st.dataframe(pd.DataFrame(forecast_list), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Semua komponen dalam batas aman.")
    else:
        st.info("Tidak ada data komponen atau database kosong.")

def show_unscheduled_removal_forecasting():

    st.subheader("📈 Unscheduled Removal Forecasting (MTBUR Analysis)")
    st.write("Analisis ini membantu memprediksi kebutuhan stok berdasarkan data unscheduled removal dan TAT.")

    # 1. Pilih Part Number yang mau dianalisa
    conn = create_connection()
    pn_list = pd.read_sql_query("SELECT DISTINCT part_number FROM component_history", conn)
    selected_pn = st.selectbox("Select Part Number for Analysis:", pn_list['part_number'])

    # 2. Ambil Parameter Pendukung
    col1, col2, col3 = st.columns(3)
    qpa = col1.number_input("QPA (Qty Per Aircraft):", value=1, min_value=1)
    tat = col2.number_input("Average TAT (Days):", value=30)
    confidence = col3.slider("Service Level (Confidence):", 0.80, 0.99, 0.95)

    # 3. Hitung Statistik dari Database
    # Ambil Total Unscheduled Removal
    query_ur = f"SELECT COUNT(*) as total_ur FROM component_history WHERE part_number = '{selected_pn}' AND reason_removal = 'Unscheduled'"
    ur_count = pd.read_sql_query(query_ur, conn).iloc[0]['total_ur']
    
    # Ambil Total Fleet FH (Asumsi untuk tipe pesawat yang menggunakan PN tersebut)
    query_fh = "SELECT SUM(flight_hours) as total_fh FROM aml_utilization"
    total_fh = pd.read_sql_query(query_fh, conn).iloc[0]['total_fh'] or 1 # Avoid div by zero
    
    conn.close()

    # 4. Kalkulasi MTBUR & Removal Rate
    mtbur = (total_fh * qpa) / ur_count if ur_count > 0 else total_fh * qpa
    removal_rate_1000 = (ur_count * 1000) / (total_fh * qpa) if total_fh > 0 else 0
    
    # 5. Poisson untuk Ideal Floating
    # Lambda = (Expected Removals selama TAT)
    # Formula: (Removal Rate per hour) * QPA * (TAT in hours)
    daily_fh = total_fh / 365 # Estimasi FH per hari fleet
    lambda_tat = (ur_count / total_fh) * (daily_fh * tat)

    # Mencari jumlah stok (k) agar probabilitas akumulatif >= confidence level
    ideal_stock = poisson.ppf(confidence, lambda_tat)

    # --- TAMPILKAN HASIL ---
    c1, c2, c3 = st.columns(3)
    c1.metric("MTBUR", f"{round(mtbur, 0)} FH")
    c2.metric("Removal Rate", f"{round(removal_rate_1000, 3)} /1000 FH")
    c3.metric("Ideal Floating Stock", f"{int(ideal_stock)} EA")

    st.write(f"💡 *Berdasarkan data, probabilitas kebutuhan selama {tat} hari TAT adalah {int(ideal_stock)} unit untuk mencapai service level {int(confidence*100)}%.*")

def show(page):
    # Gunakan nama yang persis sama dengan sidebar (cek ejaan Forecasting)
    if page == "Scheduled Component Removal":
        show_scheduled_removal()
    elif page == "Unscheduled Removal Forecasting" or page == "Unscheduled Removal Forcasting":
        show_unscheduled_removal_forecasting()
    elif page == "Material Requisition":
        st.subheader("📝 Material Requisition Module")
        st.info("Form permintaan barang akan muncul di sini.")
    else:
        st.info(f"Sub-modul '{page}' sedang dalam tahap pengembangan.")