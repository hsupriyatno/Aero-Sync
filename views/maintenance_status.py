import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
from datetime import datetime, timedelta
from database import create_connection
import base64

# ==========================================
# 1. FUNGSI PENDUKUNG (DATA & EXPORT)
# ==========================================

def generate_pdf_report(df_input):
    """Fungsi Generator PDF untuk AD Status"""
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(26, 58, 95)
    pdf.cell(0, 10, "AIRWORTHINESS DIRECTIVE STATUS REPORT", ln=True, align='C')
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 8)
    pdf.set_fill_color(240, 240, 240)
    widths = [15, 35, 75, 20, 35, 25, 25, 20, 27]
    headers = ["Reg", "AD Number", "Subject", "Type", "Last Compliance", "Next FH", "Next Date", "Rem FH", "Status"]

    for i in range(len(headers)):
        pdf.cell(widths[i], 8, headers[i], border=1, align='C', fill=True)
    pdf.ln()
    pdf.set_font("Arial", '', 7)
    for _, row in df_input.iterrows():
        # Clean data dari newline untuk PDF
        lc = str(row.get('Last Compliance', '')).replace("\n", " ")
        pdf.cell(widths[0], 7, str(row.get('Registration', '')), border=1, align='C')
        pdf.cell(widths[1], 7, str(row.get('AD Number', '')), border=1, align='C')
        pdf.cell(widths[2], 7, str(row.get('Subject', ''))[:45], border=1)
        pdf.cell(widths[3], 7, str(row.get('Type', '')), border=1, align='C')
        pdf.cell(widths[4], 7, lc, border=1, align='C')
        pdf.cell(widths[5], 7, str(row.get('Next Due (FH)', '')), border=1, align='C')
        pdf.cell(widths[6], 7, str(row.get('Next Due (Date)', '')), border=1, align='C')
        pdf.cell(widths[7], 7, str(row.get('Rem FH', '')), border=1, align='C')
        pdf.cell(widths[8], 7, str(row.get('Status', '')), border=1, align='C')
        pdf.ln()
        # Bagian akhir fungsi:
        # Gunakan dest='S' untuk mendapatkan string output
        output = pdf.output(dest='S')
    
        # Pastikan yang dikembalikan adalah string, bukan bytes di sini
        if isinstance(output, bytes):
            return output.decode('latin-1')
        return output

def get_utilization_data():
    conn = create_connection()
    query = """
    SELECT
        c.ac_reg AS [Registration], c.ac_type AS [Type],
        c.tsn AS [Start TSN], c.csn AS [Start CSN],
        IFNULL(SUM(a.flight_hours), 0) AS [Accumulated FH],
        IFNULL(SUM(a.landings), 0) AS [Accumulated FC],
        (c.tsn + IFNULL(SUM(a.flight_hours), 0)) AS [Current TSN],
        (c.csn + IFNULL(SUM(a.landings), 0)) AS [Current CSN]
    FROM catalog c
    LEFT JOIN aml_utilization a ON c.ac_reg = a.ac_reg
    GROUP BY c.ac_reg
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_detailed_history(ac_reg, start_date, end_date):
    """
    Mengambil data histori pemakaian pesawat berdasarkan rentang tanggal.
    Digunakan untuk tabel 'Detailed Utilization History'.
    """
    conn = create_connection()

    try:
        query = """
        SELECT
            date AS [Date],
            aml_no AS [AML No],
            flight_hours AS [FH],
            landings AS [FC],
            ac_tsn AS [TSN],
            ac_csn AS [CSN],
            departure AS [From],
            arrival AS [To]
        FROM aml_utilization
        WHERE ac_reg = ? AND date BETWEEN ? AND ?
        ORDER BY date DESC, aml_no DESC
        """
        # Menggunakan params untuk keamanan SQL Injection
        df = pd.read_sql(query, conn, params=(ac_reg, start_date, end_date))
        return df
    except Exception as e:
        st.error(f"Error saat mengambil histori: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# ==========================================
# 2. FUNGSI TAMPILAN UTAMA
# ==========================================

def show(page_name):
    # CSS untuk Tabel AD Status agar ada garis dan rapi
    st.markdown("""
        <style>
        .report-table { width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 20px; }
        .report-table th { background-color: #1a3a5f; color: white; border: 1px solid #ddd; padding: 8px; }
        .report-table td { border: 1px solid #ddd; padding: 6px; text-align: center; }
        .status-badge { padding: 2px 8px; border-radius: 4px; font-weight: bold; }
        .normal { background-color: #d4edda; color: #155724; }
        .overdue { background-color: #f8d7da; color: #721c24; }
        .soon { background-color: #fff3cd; color: #856404; }
        </style>
    """, unsafe_allow_html=True)

    conn = create_connection()
    try:
        df_util_global = get_utilization_data()
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

        # --- AD STATUS ---
        elif page_name == "Airworthiness Directive Status":
            st.header("📋 Airworthiness Directive Status")
            query_ad = """
                SELECT m.ad_number, m.ac_type, m.subject, m.compliance_type,
                       m.interval_fh, m.interval_days, c.ac_reg, c.date_done, c.fh_done
                FROM ad_catalog m
                LEFT JOIN ad_compliance c ON m.ad_number = c.ad_number
                WHERE c.comp_id = (SELECT MAX(comp_id) FROM ad_compliance WHERE ad_number = m.ad_number AND ac_reg = c.ac_reg)
                OR c.comp_id IS NULL
            """
            df_ad = pd.read_sql(query_ad, conn)

            if not df_ad.empty:
                status_list = []
                # Membangun tabel HTML secara manual agar garis muncul
                html_table = '<table class="report-table"><thead><tr><th>Reg</th><th>AD Number</th><th>Subject</th><th>Type</th><th>Last Compliance</th><th>Next FH</th><th>Status</th></tr></thead><tbody>'
               
# --- MULAI PERULANGAN DATA AD ---
                for _, row in df_ad.iterrows():
                    ac_info = df_util_global[df_util_global['Registration'] == row['ac_reg']]
                    curr_fh = ac_info['Current TSN'].values[0] if not ac_info.empty else 0
                    
                    due_fh = row['fh_done'] + row['interval_fh'] if row['date_done'] and row['interval_fh'] > 0 else "-"
                    rem_fh = round(due_fh - curr_fh, 2) if isinstance(due_fh, (int, float)) else "-"
                    
                    st_label = "NORMAL"
                    badge_class = "normal"
                    if isinstance(rem_fh, (int, float)):
                        if rem_fh <= 0:
                            st_label = "OVERDUE"; badge_class = "overdue"
                        elif rem_fh < 50:
                            st_label = "DUE SOON"; badge_class = "soon"

                    # --- PERBAIKAN UTAMA: Hindari f-string untuk data variabel ---
                    txt_date = str(row['date_done'])
                    txt_fh = str(row['fh_done'])
                    # Pakai penggabungan string manual (+) agar aman 100% dari backslash error
                    lc_display = txt_date + " (" + txt_fh + " FH)"

                    # Data untuk Export
                    status_list.append({
                        "Registration": row['ac_reg'], "AD Number": row['ad_number'], "Subject": row['subject'],
                        "Type": row['compliance_type'], "Last Compliance": lc_display,
                        "Next Due (FH)": due_fh, "Rem FH": rem_fh, "Status": st_label
                    })

                    # Gunakan .format() untuk merakit baris HTML tabel
                    # Cara ini jauh lebih stabil di server Streamlit Bapak
                    html_row = "<tr><td>{}</td><td>{}</td><td style='text-align:left'>{}</td><td>{}</td><td>{}</td><td>{}</td><td><span class='status-badge {}'>{}</span></td></tr>".format(
                        row['ac_reg'], row['ad_number'], row['subject'], row['compliance_type'], 
                        lc_display, due_fh, badge_class, st_label
                    )
                    html_table += html_row
                
                # --- PENUTUP TABEL (DI LUAR LOOP) ---
                # 1. Olah dulu teksnya di variabel terpisah (Aman dari Backslash)
                lc_raw = str(row.get('Last Compliance', ''))
                lc_clean = lc_raw.replace('\n', '<br>') 

                # 2. Baru panggil variabelnya di dalam f-string
                html_table += f"<td>{lc_clean}</td>"
                st.markdown(html_table, unsafe_allow_html=True)
                df_final = pd.DataFrame(status_list)

                # Tombol Download
                # Ambil output string dari fungsi
                # 1. Ambil output string dari fungsi
                pdf_str = generate_pdf_report(df_final)

                # 2. Konversi ke Bytes secara manual agar stabil di server
                # Ini adalah cara paling aman untuk fpdf
                pdf_bytes = pdf_str.encode('latin-1') 

                st.download_button(
                    label="📕 Download PDF Report",
                    data=pdf_bytes,           # Gunakan data yang sudah jadi bytes
                    file_name="AD_Report.pdf",
                    mime="application/pdf"
                )



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
        # Menutup koneksi dengan aman
        if 'conn' in locals():
            conn.close()
        