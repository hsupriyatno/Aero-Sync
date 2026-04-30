import streamlit as st
import pandas as pd
import io
from datetime import datetime  # Pastikan baris ini ada
from database import create_connection

def get_utilization_data():
    """Fungsi helper untuk menghitung Current TSN/CSN secara realtime"""
    conn = create_connection()
    query = """
    SELECT 
        c.ac_reg AS [Registration], 
        c.ac_type AS [Type],
        c.tsn AS [Start TSN],
        c.csn AS [Start CSN],
        IFNULL(SUM(a.flight_hours), 0) AS [Accumulated FH],
        IFNULL(SUM(a.landings), 0) AS [Accumulated FC],
        (c.tsn + IFNULL(SUM(a.flight_hours), 0)) AS [Current TSN],
        (c.csn + IFNULL(SUM(a.landings), 0)) AS [Current CSN],
        MAX(a.date) AS [Last Flight]
    FROM catalog c
    LEFT JOIN aml_utilization a ON c.ac_reg = a.ac_reg
    GROUP BY c.ac_reg
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_detailed_history(ac_reg, start_date, end_date):
    """Mengambil riwayat detail pergerakan pesawat dari aml_utilization"""
    conn = create_connection()
    query = f"""
    SELECT 
        aml_no AS [AML NO],
        date AS [Date],
        flight_hours AS [FH],
        landings AS [FC],
        ac_tsn AS [TSN],
        ac_csn AS [CSN]
    FROM aml_utilization
    WHERE ac_reg = '{ac_reg}' 
    AND date BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY date DESC, aml_no DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def show(page_name):
    # --- CSS Injection Tetap Sama ---
    st.markdown("""
        <style>
        .section-font { font-size:20px !important; font-weight: bold; margin-top: 10px; color: #1E3A8A; }
        .metric-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #1E3A8A; }
        </style>
    """, unsafe_allow_html=True)

    conn = create_connection() # Pindahkan koneksi ke sini agar bisa dipakai semua sub-menu

    try:
        # PENTING: Ambil data registrasi di luar blok IF agar tersedia untuk semua halaman
        df_util = get_utilization_data()
        
        if df_util.empty:
            st.warning("Data Aircraft Catalog kosong.")
            return

        # Buat selectbox global di bagian paling atas jika halaman adalah salah satu dari sub-menu maintenance
        # Atau jika Bapak ingin selectbox hanya muncul di sub-menu tertentu, definisikan ulang di tiap sub-menu.
        
        # === HALAMAN 1: AIRCRAFT UTILIZATION RECORD ===
        if page_name == "Aircraft Utilization Record":
            st.header("✈️ Aircraft Utilization Record")
            
            df_util = get_utilization_data()
            
            if not df_util.empty:
                # Menampilkan Summary dalam bentuk Metric Cards
                st.markdown('<p class="section-font">Fleet Summary Status</p>', unsafe_allow_html=True)
                cols = st.columns(len(df_util))
                
                for i, row in df_util.iterrows():
                    with cols[i]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <small>{row['Type']}</small><br>
                            <span style="font-size: 20px; font-weight: bold;">{row['Registration']}</span><br>
                            <span style="color: #1E3A8A;">TSN: {row['Current TSN']:.2f}</span><br>
                            <span style="color: #666;">CSN: {int(row['Current CSN'])}</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.divider()
                
                # Menampilkan Tabel Detail
                st.markdown('<p class="section-font">Detailed Utilization Table</p>', unsafe_allow_html=True)
                st.dataframe(df_util, use_container_width=True, hide_index=True)
                
                # --- Tombol Export Excel ---
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_util.to_excel(writer, index=False, sheet_name='Utilization_Report')
                    
                    # Tambahan opsional: Formatting agar kolom Excel otomatis pas lebarnya
                    workbook  = writer.book
                    worksheet = writer.sheets['Utilization_Report']
                    for i, col in enumerate(df_util.columns):
                        column_len = max(df_util[col].astype(str).str.len().max(), len(col)) + 2
                        worksheet.set_column(i, i, column_len)

                st.download_button(
                    label="📊 Download Report (Excel)",
                    data=buffer.getvalue(),
                    file_name=f"Utilization_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("Data Aircraft Catalog belum diisi.")

            # --- BAGIAN BARU: DETAILED UTILIZATION HISTORY ---
            st.divider()
            st.markdown('<p class="section-font">🔍 Filter Detailed Utilization History</p>', unsafe_allow_html=True)
            
            # Form Filter
            with st.container():
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    list_reg = df_util['Registration'].unique()
                    selected_reg = st.selectbox("Select A/C Reg:", list_reg)
                
                with col2:
                    # Default ke awal tahun 2026 sesuai permintaan Bapak
                    start_d = st.date_input("Start Date:", value=datetime(2026, 1, 1))
                
                with col3:
                    end_d = st.date_input("End Date:", value=datetime.now())

            list_reg = df_util['Registration'].unique()
            selected_reg = st.selectbox("Select A/C Reg:", list_reg, key="reg_util")

            # Eksekusi Query saat variabel dipilih
            if selected_reg:
                df_history = get_detailed_history(
                    selected_reg, 
                    start_d.strftime('%Y-%m-%d'), 
                    end_d.strftime('%Y-%m-%d')
                )
                
                if not df_history.empty:
                    st.write(f"Showing results for **{selected_reg}** from **{start_d}** to **{end_d}**")
                    st.dataframe(df_history, use_container_width=True, hide_index=True)
                    
                    # Tombol download khusus untuk hasil filter ini
                    buffer_hist = io.BytesIO()
                    with pd.ExcelWriter(buffer_hist, engine='xlsxwriter') as writer:
                        df_history.to_excel(writer, index=False, sheet_name='History')
                    
                    st.download_button(
                        label=f"📊 Export History {selected_reg} (Excel)",
                        data=buffer_hist.getvalue(),
                        file_name=f"History_{selected_reg}_{start_d}_to_{end_d}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning(f"Tidak ada data penerbangan untuk {selected_reg} pada periode tersebut.")

        # === HALAMAN 2: AIRWORTHINESS DIRECTIVES STATUS ===
        elif page_name == "Airworthiness Directive Status":
            st.header("✈️ Airworthiness Directive Status")
            st.info("Modul Monitoring AD sedang dikembangkan.")

        # === HALAMAN 3: SERVICE BULLETIN STATUS ===
        elif page_name == "Service Bulletin Status":
            st.header("✈️ Service Bulletin Status")
            st.info("Modul Monitoring SB sedang dikembangkan.")

        # === HALAMAN 4: COMPONENT STATUS ===
        elif page_name == "Component Status":
            st.header("✈️ Component Status")
    
            df_util = get_utilization_data()
            list_reg = df_util['Registration'].unique()
            selected_reg = st.selectbox("Select Aircraft Registration:", list_reg, key="reg_comp")
    
            st.subheader(f"📊 Detailed Component Status - {selected_reg}")

            # 1. Hitung Jam Terbang Real-time
            conn = create_connection()
            curr = conn.cursor()
    
            # Ambil Start TSN/CSN dari catalog
            curr.execute("SELECT tsn, csn FROM catalog WHERE ac_reg = ?", (selected_reg,))
            base_data = curr.fetchone()
    
            # Ambil Akumulasi dari aml_utilization
            curr.execute("SELECT SUM(flight_hours), SUM(landings) FROM aml_utilization WHERE ac_reg = ?", (selected_reg,))
            acc_data = curr.fetchone()
    
            current_ac_hrs = (base_data[0] or 0) + (acc_data[0] or 0)
            current_ac_cyc = (base_data[1] or 0) + (acc_data[1] or 0)

            # Header sesuai permintaan: TSN & CSN
            st.info(f"**Current Airframe Status:** TSN: {current_ac_hrs:.2f} Hours / CSN: {int(current_ac_cyc)} Cycles")

            # 2. Query Data Gabungan
            query = f"""
                SELECT 
                    i.component_name, i.part_number, i.serial_number, i.position,
                    i.install_af_hours, i.install_af_cycles,
                    i.tsn_at_install, i.csn_at_install, i.tso, i.cso, i.install_date,
                    m.tbo_hours, m.tbo_cycles, m.tbo_calendar
                FROM installed_components i
                LEFT JOIN master_part_number m ON i.part_number = m.part_number
                WHERE i.ac_reg = '{selected_reg}'
            """
            df = pd.read_sql_query(query, conn)

            if not df.empty:
                status_list = []
                today = datetime.now().date()

                for _, row in df.iterrows():
                    # Kalkulasi Selisih (Delta)
                    diff_hrs = current_ac_hrs - row['install_af_hours']
                    diff_cyc = current_ac_cyc - row['install_af_cycles']
            
                    # 1. Current Status (TSO, CSO, DSO)
                    cur_tso = (row['tso'] or 0) + diff_hrs
                    cur_cso = (row['cso'] or 0) + diff_cyc
                    # DSO (Days Since Overhaul/Install)
                    days_since = (today - pd.to_datetime(row['install_date']).date()).days if row['install_date'] else 0
            
                    # 2. Remaining Calculation
                    rem_hrs = (row['tbo_hours'] or 0) - cur_tso if row['tbo_hours'] else 0
                    rem_cyc = (row['tbo_cycles'] or 0) - cur_cso if row['tbo_cycles'] else 0
                    rem_mon = (row['tbo_calendar'] or 0) - (days_since/30.44) if row['tbo_calendar'] else 0

                    # Menggabungkan data ke bawah (Multiline) menggunakan string format
                    tbo_combined = f"{row['tbo_hours'] or 0} H\n{int(row['tbo_cycles'] or 0)} C\n{int(row['tbo_calendar'] or 0)} M"
                    current_combined = f"{cur_tso:.2f} TSO\n{int(cur_cso)} CSO\n{int(days_since)} DSO"
                    rem_combined = f"{rem_hrs:.2f} H\n{int(rem_cyc)} C\n{max(0, round(rem_mon, 1))} M"

                    status_list.append({
                        "Part Description": row['component_name'],
                        "P/N": row['part_number'],
                        "S/N": row['serial_number'],
                        "Pos": row['position'],
                        "TBO (H/C/M)": tbo_combined,
                        "Current (TSO/CSO/DSO)": current_combined,
                        "Remaining": rem_combined
                    })
        
                # Tampilkan tabel dengan styling agar pindah baris (\n) terbaca
                df_final = pd.DataFrame(status_list)
        
                # Menggunakan st.table atau st.dataframe dengan pengaturan whitespace
                st.write(
                    df_final.to_html(escape=False).replace("\\n", "<br>"), 
                    unsafe_allow_html=True
                )
        
            else:
                st.info("Belum ada data komponen.")
            conn.close()

    except Exception as e:
        st.error(f"Error pada halaman {page_name}: {e}")
    finally:
        conn.close()