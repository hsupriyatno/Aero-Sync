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
            used_hrs = row['tsn_at_install'] + row['total_flown']
            if row['tbo_h'] > 0:
                rem_hrs = row['tbo_h'] - used_hrs
            else:
                rem_hrs = 999999
            
            rem_days = 99999
            if row['install_date'] and row['tbo_c'] > 0:
                try:
                    install_dt = pd.to_datetime(row['install_date']).date()
                    days_used = (today - install_dt).days
                    rem_days = (row['tbo_c'] * 30.44) - days_used
                except:
                    pass

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

    conn = create_connection()
    
    # Ambil list Part Number
    pn_list = pd.read_sql_query("SELECT DISTINCT part_number FROM component_history", conn)
    if pn_list.empty:
        st.info("Belum ada data di component_history untuk analisis MTBUR.")
        conn.close()
        return
        
    selected_pn = st.selectbox("Select Part Number for Analysis:", pn_list['part_number'])

    # 🟢 LOGIKA OTOMATISASI TAT: Ambil rata-rata TAT aktual khusus untuk Part Number yang dipilih
    try:
        query_tat = "SELECT AVG(tat_days) as avg_tat FROM inventory_rotable_tat WHERE part_number = ? AND status = 'Closed'"
        df_tat_val = pd.read_sql_query(query_tat, conn, params=(selected_pn,))
        db_tat = df_tat_val.iloc[0]['avg_tat']
        # Jika database belum punya riwayat TAT untuk P/N ini, default ke 30 hari
        calculated_tat = int(round(db_tat)) if (db_tat is not None and pd.notna(db_tat)) else 30
    except:
        calculated_tat = 30

    col1, col2, col3 = st.columns(3)
    qpa = col1.number_input("QPA (Qty Per Aircraft):", value=1, min_value=1)
    
    # Tampilkan nilai TAT hasil kalkulasi otomatis, tapi tetap izinkan user mengubah jika diperlukan
    tat = col2.number_input("Average TAT (Days):", value=calculated_tat, help="Otomatis mengambil rata-rata riwayat shop visit P/N ini.")
    confidence = col3.slider("Service Level (Confidence):", 0.80, 0.99, 0.95)

    # Hitung Statistik Unscheduled Removal
    query_ur = "SELECT COUNT(*) as total_ur FROM component_history WHERE part_number = ? AND reason_removal = 'Unscheduled'"
    df_ur = pd.read_sql_query(query_ur, conn, params=(selected_pn,))
    ur_count = df_ur.iloc[0]['total_ur'] if not df_ur.empty else 0
    
    # Hitung Total Fleet FH
    query_fh = "SELECT SUM(flight_hours) as total_fh FROM aml_utilization"
    df_fh = pd.read_sql_query(query_fh, conn)
    total_fh = df_fh.iloc[0]['total_fh'] if (not df_fh.empty and df_fh.iloc[0]['total_fh'] is not None) else 1

    # Kalkulasi MTBUR & Removal Rate
    mtbur = (total_fh * qpa) / ur_count if ur_count > 0 else total_fh * qpa
    removal_rate_1000 = (ur_count * 1000) / (total_fh * qpa) if total_fh > 0 else 0
    
    # Poisson untuk Ideal Floating Stock
    daily_fh = total_fh / 365
    lambda_tat = (ur_count / total_fh) * (daily_fh * tat) if total_fh > 0 else 0
    ideal_stock = poisson.ppf(confidence, lambda_tat) if lambda_tat > 0 else 0

    # Tampilkan Hasil Analisis
    c1, c2, c3 = st.columns(3)
    c1.metric("MTBUR", f"{round(mtbur, 0)} FH")
    c2.metric("Removal Rate", f"{round(removal_rate_1000, 3)} /1000 FH")
    c3.metric("Ideal Floating Stock", f"{int(ideal_stock)} EA")

    st.write(f"💡 *Berdasarkan data, probabilitas kebutuhan selama {tat} hari TAT adalah {int(ideal_stock)} unit untuk mencapai service level {int(confidence*100)}%.*")
    conn.close()

# 🟢 REKOMENDASI TAMBAHAN: FUNGSI BARU UNTUK MONITORING LOG LENGKAP TAT ROTABLE
def show_rotable_tat_dashboard():
    st.subheader("📦 Rotable Component Turn Around Time (TAT) Dashboard")
    st.write("Rangkuman durasi pengerjaan komponen semenjak keluar STORE (Unserviceable) hingga kembali (Serviceable).")
    
    conn = create_connection()
    try:
        # 1. Tampilkan Rata-rata TAT per Part Number
        st.write("#### 📊 Average TAT Summary per Part Number")
        query_avg = """
            SELECT part_number as [Part Number], description as [Description],
                   COUNT(id) as [Total History], ROUND(AVG(tat_days), 1) as [Avg TAT (Days)]
            FROM inventory_rotable_tat WHERE tat_days IS NOT NULL AND status = 'Closed'
            GROUP BY part_number, description ORDER BY [Avg TAT (Days)] DESC
        """
        df_avg = pd.read_sql_query(query_avg, conn)
        if not df_avg.empty:
            st.dataframe(df_avg, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada riwayat komponen yang berstatus 'Closed' (Kembali ke gudang).")

        st.divider()
        
        # 2. Tampilkan Detail Log dengan Box Scroll Biar Ringan
        st.write("#### 📜 Detailed Shop Visit History Log")
        search_pn = st.text_input("🔍 Cari Nomor Part atau Serial Number:", placeholder="Ketik nomor part/serial...")
        
        query_log = "SELECT ro_no, part_number, serial_number, description, quantity, uom, date_sent, date_received, tat_days, status FROM inventory_rotable_tat"
        params = []
        if search_pn.strip() != "":
            query_log += " WHERE part_number LIKE ? OR serial_number LIKE ?"
            params.extend([f"%{search_pn.strip()}%", f"%{search_pn.strip()}%"])
        query_log += " ORDER BY date_sent DESC"
        
        df_log = pd.read_sql_query(query_log, conn, params=params)
        
        # Kotak scroll setinggi 350px biar super ringan dibuka di laptop/HP
        with st.container(height=350, border=True):
            if not df_log.empty:
                st.dataframe(df_log, use_container_width=True, hide_index=True)
            else:
                st.caption("Tidak ada log transaksi rotable.")
    finally:
        conn.close()

# 🟢 SINKRONISASI PENGALIHAN PAGE DI SINI
# Ganti fungsi show() paling bawah milik Bapak menjadi seperti ini:
def show(page):
    page_id = page.lower().replace(" ", "")
    
    if "scheduledcomponent" in page_id:
        show_scheduled_removal()
        
    elif "unscheduled" in page_id:
        # 🟢 KITA JADIKAN 2 TAB DI SINI AGAR SINKRON DENGAN SIDEBAR BAPAK
        tab1, tab2 = st.tabs(["📈 MTBUR Forecasting Analysis", "📦 Rotable TAT Dashboard"])
        
        with tab1:
            show_unscheduled_removal_forecasting()
        with tab2:
            show_rotable_tat_dashboard()
            
    elif "requisition" in page_id:
        st.subheader("📝 Material Requisition Module")
        st.info("Form permintaan barang akan muncul di sini.")
    else:
        st.info(f"Sub-modul '{page}' sedang dalam tahap pengembangan.")