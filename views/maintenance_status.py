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

def show_ad_status():
    st.subheader("📋 Airworthiness Directive Status")
    
    conn = create_connection()
    # Join dengan data utilization terbaru jika ada untuk menghitung remaining
    query = "SELECT ac_reg, ad_number, subject, last_done_fh, next_due_fh, status FROM airworthiness_directives"
    df = pd.read_sql(query, conn)
    conn.close()
    
    if not df.empty:
        # Contoh perhitungan sederhana untuk Remaining (bisa diimprove dengan data FH aktual)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Beri highlight untuk AD yang mendekati Due Date
        st.warning("⚠️ Perhatian: Terdapat AD yang mendekati limit pengerjaan (Maintenance Forecast).")
    else:
        st.info("Belum ada data AD yang terdaftar.")

def show(page_name):
    # --- Tambahkan CSS yang lebih kuat di bagian atas page ---
    st.markdown("""
        <style>
        /* Mengatur seluruh tabel di dalam div compact-table */
        .compact-table table {
            font-size: 11px !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        }
        /* Mengatur kerapatan baris dan padding sel */
        .compact-table td, .compact-table th {
            padding: 2px 4px !important;
            line-height: 1.1 !important;
            vertical-align: middle !important;
        }
        /* Menghilangkan spasi antar baris di elemen <br> */
        .compact-table br {
            content: "";
            margin: 0;
            display: block;
        }
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
                    # Gunakan SATU selectbox saja di sini
                    selected_reg = st.selectbox("Select A/C Reg:", list_reg, key="reg_util_filter")
                
                with col2:
                    start_d = st.date_input("Start Date:", value=datetime(2026, 1, 1), key="start_util")
                
                with col3:
                    end_d = st.date_input("End Date:", value=datetime.now(), key="end_util")

            # HAPUS baris 'list_reg = ...' dan 'selected_reg = ...' yang tadinya ada di sini (di luar kolom)

            # Eksekusi Query menggunakan variabel dari selectbox di atas
            if selected_reg:
                df_history = get_detailed_history(
                    selected_reg, 
                    start_d.strftime('%Y-%m-%d'), 
                    end_d.strftime('%Y-%m-%d')
                )
                
                if not df_history.empty:
                    st.write(f"Showing results for **{selected_reg}** from **{start_d}** to **{end_d}**")
                    st.dataframe(df_history, use_container_width=True, hide_index=True)
                    
                    # Tombol download
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
    
            conn = create_connection()
    
            # 1. Ambil data Utilization terakhir untuk setiap pesawat
            # Ini untuk menghitung 'Current FH' secara real-time
            query_util = """
                SELECT c.ac_reg, c.ac_type, 
                    (c.tsn + IFNULL(SUM(u.flight_hours), 0)) as current_fh
                FROM catalog c
                LEFT JOIN aml_utilization u ON c.ac_reg = u.ac_reg
                GROUP BY c.ac_reg
            """
            df_util = pd.read_sql(query_util, conn)

            # 2. Query Gabungan: Master AD + Compliance Terakhir
            # Kita ambil pengerjaan TERAKHIR (MAX date_done) untuk setiap AD di setiap pesawat
            query_status = """
                SELECT 
                    m.ad_number, m.ac_type, m.subject, m.compliance_type, 
                    m.interval_fh, m.interval_days,
                    c.ac_reg, c.date_done, c.fh_done, c.remarks
                FROM ad_catalog m
                LEFT JOIN ad_compliance c ON m.ad_number = c.ad_number
                WHERE c.comp_id = (
                    SELECT MAX(comp_id) 
                    FROM ad_compliance 
                    WHERE ad_number = m.ad_number AND ac_reg = c.ac_reg
                ) OR c.comp_id IS NULL
            """
            df_ad = pd.read_sql(query_status, conn)
    
            if not df_ad.empty:
                status_data = []
                today = datetime.now().date()

                for _, row in df_ad.iterrows():
                    # Cari jam terbang pesawat saat ini dari df_util
                    ac_info = df_util[df_util['ac_reg'] == row['ac_reg']]
                    curr_fh = ac_info['current_fh'].values[0] if not ac_info.empty else 0

                    # --- LOGIKA KALKULASI DUE ---
                    due_fh = "-"
                    due_date = "-"
                    rem_fh = "-"
                    rem_days = "-"
                    status_label = "⚪ NO DATA"

                    if row['date_done']: # Jika sudah pernah dikerjakan
                        last_date = datetime.strptime(row['date_done'], '%Y-%m-%d').date()
                
                        # A. Kalkulasi berdasarkan Hours (FH)
                        if row['interval_fh'] > 0:
                            due_fh = row['fh_done'] + row['interval_fh']
                            rem_fh = round(due_fh - curr_fh, 2)
                
                        # B. Kalkulasi berdasarkan Calendar (Days)
                        if row['interval_days'] > 0:
                            due_date = last_date + timedelta(days=row['interval_days'])
                            rem_days = (due_date - today).days

                        # C. Penentuan Status Warna
                        if (isinstance(rem_fh, float) and rem_fh <= 0) or (isinstance(rem_days, int) and rem_days <= 0):
                            status_label = "🔴 OVERDUE"
                        elif (isinstance(rem_fh, float) and rem_fh < 50) or (isinstance(rem_days, int) and rem_days < 30):
                            status_label = "🟡 DUE SOON"
                        else:
                            status_label = "🟢 NORMAL"
            
                    if row['compliance_type'] == "One-time" and row['date_done']:
                        status_label = "🔵 COMPLIED"

                    status_data.append({
                        "Registration": row['ac_reg'] if row['ac_reg'] else "N/A",
                        "AD Number": row['ad_number'],
                        "Subject": row['subject'],
                        "Type": row['compliance_type'],
                        "Last Compliance": f"{row['date_done']}\n({row['fh_done']} FH)",
                        "Next Due (FH)": due_fh,
                        "Next Due (Date)": due_date,
                        "Rem FH": rem_fh,
                        "Rem Days": rem_days,
                        "Status": status_label
                    })

                df_final = pd.DataFrame(status_data)

                # --- Tampilan Tabel ---
                st.dataframe(
                    df_final,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Status": st.column_config.TextColumn("Status", help="Green: OK, Yellow: <50h/30d, Red: Overdue"),
                        "Last Compliance": st.column_config.TextColumn("Last Compliance", width="medium"),
                    }
                )
        
                # Tombol Export
                st.divider()
                st.download_button("📊 Download AD Status Report", df_final.to_csv(index=False), "AD_Status_Report.csv", "text/csv")

            else:
                st.info("Belum ada data AD Compliance yang tercatat.")

            conn.close()

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
    
            curr.execute("SELECT tsn, csn FROM catalog WHERE ac_reg = ?", (selected_reg,))
            base_data = curr.fetchone()
    
            curr.execute("SELECT SUM(flight_hours), SUM(landings) FROM aml_utilization WHERE ac_reg = ?", (selected_reg,))
            acc_data = curr.fetchone()
    
            current_ac_hrs = (base_data[0] or 0) + (acc_data[0] or 0)
            current_ac_cyc = (base_data[1] or 0) + (acc_data[1] or 0)

            st.info(f"**Current Airframe Status:** TSN: {current_ac_hrs:.2f} Hours / CSN: {int(current_ac_cyc)} Cycles")

            # 2. Query Data Gabungan
            # Tambahkan filter 'AND i.parent_sn != 0' dan 'AND i.parent_sn != '''
            query = f"""
                SELECT 
                    i.component_name, i.part_number, i.parent_sn, i.position,
                    i.install_af_hours, i.install_af_cycles,
                    i.tsn_at_install, i.csn_at_install, i.tso, i.cso, i.install_date,
                    m.tbo_hours, m.tbo_cycles, m.tbo_calendar
                FROM installed_components i
                LEFT JOIN master_part_number m ON i.part_number = m.part_number
                WHERE i.ac_reg = '{selected_reg}' 
                AND i.parent_sn IS NOT NULL 
                AND i.parent_sn != '' 
                AND i.parent_sn != '0'
            """
            df = pd.read_sql_query(query, conn)
            df = df.fillna(0) # Mengisi semua data NaN/NULL dengan angka 0
            df = df[df['parent_sn'] != 0]
            df = df[df['parent_sn'] != '0']
            df = df[df['component_name'] != 0]

            cols_to_fix = ['install_af_cycles', 'csn_at_install', 'cso', 'm.tbo_cycles']
            for col in cols_to_fix:
                if col in df.columns:
                    df[col] = df[col].fillna(0).astype(int)

            if not df.empty:
                status_list = []
                today = datetime.now().date()

                for _, row in df.iterrows():
                    # Kalkulasi Selisih Jam Pesawat sejak pemasangan
                    diff_hrs = current_ac_hrs - row['install_af_hours']
                    diff_cyc = current_ac_cyc - row['install_af_cycles']
            
                    # 1. Total Since New (TSN/CSN/DSN)
                    # Rumus: Jam saat install + pemakaian sejak install
                    total_tsn = (row['tsn_at_install'] or 0) + diff_hrs
                    total_csn = (row['csn_at_install'] or 0) + diff_cyc
                    # DSN dihitung sejak install_date sampai hari ini
                    days_since = (today - pd.to_datetime(row['install_date']).date()).days if row['install_date'] else 0
            
                    # 2. Current Status (TSO/CSO/DSO)
                    cur_tso = (row['tso'] or 0) + diff_hrs
                    cur_cso = (row['cso'] or 0) + diff_cyc
            
                    # 3. Remaining Calculation (Berdasarkan TBO)
                    rem_hrs = (row['tbo_hours'] or 0) - cur_tso if row['tbo_hours'] else 0
                    rem_cyc = (row['tbo_cycles'] or 0) - cur_cso if row['tbo_cycles'] else 0
                    rem_mon = (row['tbo_calendar'] or 0) - (days_since/30.44) if row['tbo_calendar'] else 0

                    # Formatting Multiline untuk tabel rapat
                    tbo_combined = f"{row['tbo_hours'] or 0} H\n{int(row['tbo_cycles'] or 0)} C\n{int(row['tbo_calendar'] or 0)} M"
                    
                    # KOLOM BARU: TSN/CSN/DSN
                    tsn_combined = f"{total_tsn:.2f} TSN\n{int(total_csn)} CSN\n{int(days_since)} DSN"
                    
                    tso_combined = f"{cur_tso:.2f} TSO\n{int(cur_cso)} CSO\n{int(days_since)} DSO"
                    rem_combined = f"{rem_hrs:.2f} H\n{int(rem_cyc)} C\n{max(0, round(rem_mon, 1))} M"

                    status_list.append({
                        "Part Description": row['component_name'],
                        "P/N": row['part_number'],
                        "S/N": row['parent_sn'],
                        "Pos": row['position'],
                        "TBO (H/C/M)": tbo_combined,
                        "TSN/CSN/DSN": tsn_combined,          # Ditambahkan
                        "Current (TSO/CSO/DSO)": tso_combined,
                        "Remaining": rem_combined
                    })
                
                df_final = pd.DataFrame(status_list)
                
                # --- INI DIA BAGIAN YANG TADI TERLEWAT, PAK ---
                df_final = pd.DataFrame(status_list)

                # 3. Tombol Export
                col_space, col_btn = st.columns([5, 1])
                with col_btn:
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_final.to_excel(writer, index=False, sheet_name='Status')
                    st.download_button(label="📥 Export Excel", data=buffer.getvalue(), file_name=f"Status_{selected_reg}.xlsx")

                # 4. TAMPILAN TABEL DENGAN INLINE STYLE
                html_table = df_final.to_html(escape=False, index=False).replace("\\n", "<br>")
    
                styled_table = f"""
                <style>
                    .my-custom-table {{
                        width: 100%;
                        border-collapse: collapse;
                        font-size: 11px !important;
                        font-family: sans-serif;
                    }}
                    .my-custom-table th {{
                        background-color: #f0f2f6;
                        text-align: left;
                        padding: 4px !important;
                        border: 1px solid #dee2e6;
                    }}
                    .my-custom-table td {{
                        padding: 2px 4px !important;
                        line-height: 1.1 !important;
                        border: 1px solid #dee2e6;
                        vertical-align: middle;
                    }}
                </style>
                <div class="my-custom-table">
                    {html_table.replace('class="dataframe"', 'class="my-custom-table"')}
                </div>
                """
                st.components.v1.html(styled_table, height=500, scrolling=True)

            else:
                st.info("Belum ada data komponen.")

    except Exception as e:
        st.error(f"Error pada halaman {page_name}: {e}")
    finally:
        conn.close()