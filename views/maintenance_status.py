import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
from datetime import datetime
from database import create_connection
# JIKA fungsi get_component_status_report ditaruh di database.py, biarkan ini. 
# Namun di bawah ini kita akan pakai integrasi langsung agar filter per registrasi pesawat (A/C Reg) berjalan sempurna.

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
        lc = str(row.get('Last Compliance', '')).replace("\n", " ").replace("<br>", " ")
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
        
    output = pdf.output(dest='S')
    if isinstance(output, str):
        return output.encode('latin-1')
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
    conn = create_connection()
    try:
        query = """
        SELECT
            date AS [Date], aml_no AS [AML No], flight_hours AS [FH], landings AS [FC],
            ac_tsn AS [TSN], ac_csn AS [CSN], departure AS [From], arrival AS [To]
        FROM aml_utilization
        WHERE ac_reg = ? AND date BETWEEN ? AND ?
        ORDER BY date DESC, aml_no DESC
        """
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
    st.markdown("""
        <style>
        .report-table { width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 20px; }
        .report-table th { background-color: #1a3a5f; color: white; border: 1px solid #ddd; padding: 8px; }
        .report-table td { border: 1px solid #ddd; padding: 6px; text-align: center; }
        .status-badge { padding: 2px 8px; border-radius: 4px; font-weight: bold; }
        .normal { background-color: #d4edda; color: #155724; }
        .overdue { background-color: #f8d7da; color: #721c24; }
        .soon { background-color: #fff3cd; color: #856404; }
        .metric-card { border: 1px solid #e6ebf4; border-radius: 8px; padding: 12px; background: #fafafa; }
        .section-font { font-size: 16px; font-weight: bold; color: #1E3A8A; margin-top: 10px; }
        </style>
    """, unsafe_allow_html=True)

    try:
        # === HALAMAN 1: AIRCRAFT UTILIZATION RECORD ===
        if page_name == "Aircraft Utilization Record":
            st.header("✈️ Aircraft Utilization Record")
            df_util = get_utilization_data()
            
            if not df_util.empty:
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
                st.markdown('<p class="section-font">Detailed Utilization Table</p>', unsafe_allow_html=True)
                st.dataframe(df_util, use_container_width=True, hide_index=True)
            
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_util.to_excel(writer, index=False, sheet_name='Utilization_Report')
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
                
                st.divider()
                st.markdown('<p class="section-font">🔍 Filter Detailed Utilization History</p>', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    list_reg = df_util['Registration'].unique()
                    selected_reg = st.selectbox("Select A/C Reg:", list_reg, key="reg_util_filter")
                with col2:
                    start_d = st.date_input("Start Date:", value=datetime(2026, 1, 1), key="start_util")
                with col3:
                    end_d = st.date_input("End Date:", value=datetime.now(), key="end_util")

                if selected_reg:
                    df_history = get_detailed_history(selected_reg, start_d.strftime('%Y-%m-%d'), end_d.strftime('%Y-%m-%d'))

                    if not df_history.empty:
                        st.write(f"Showing results for **{selected_reg}** from **{start_d}** to **{end_d}**")
                        st.dataframe(df_history, use_container_width=True, hide_index=True)
                        
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
            else:
                st.info("Data Aircraft Catalog belum diisi.")

        # === HALAMAN 2: AD STATUS ===
        elif page_name == "Airworthiness Directive Status":
            st.header("📋 Airworthiness Directive Status")
            df_util_global = get_utilization_data()
            
            conn = create_connection()
            query_ad = """
                SELECT m.ad_number, m.ac_type, m.subject, m.compliance_type,
                       m.interval_fh, m.interval_days, c.ac_reg, c.date_done, c.fh_done
                FROM ad_catalog m
                LEFT JOIN ad_compliance c ON m.ad_number = c.ad_number
                WHERE c.comp_id = (SELECT MAX(comp_id) FROM ad_compliance WHERE ad_number = m.ad_number AND ac_reg = c.ac_reg)
                OR c.comp_id IS NULL
            """
            df_ad = pd.read_sql(query_ad, conn)
            conn.close()

            if not df_ad.empty:
                status_list = []
                html_table = '<table class="report-table"><thead><tr><th>Reg</th><th>AD Number</th><th>Subject</th><th>Type</th><th>Last Compliance</th><th>Next FH</th><th>Status</th></tr></thead><tbody>'
                
                for _, row in df_ad.iterrows():
                    ac_info = df_util_global[df_util_global['Registration'] == row['ac_reg']]
                    curr_fh = ac_info['Current TSN'].values[0] if not ac_info.empty else 0
                    
                    due_fh = row['fh_done'] + row['interval_fh'] if row['date_done'] and row['interval_fh'] > 0 else "-"
                    rem_fh = round(due_fh - curr_fh, 2) if isinstance(due_fh, (int, float)) else "-"
                    
                    st_label = "NORMAL"; badge_class = "normal"
                    if isinstance(rem_fh, (int, float)):
                        if rem_fh <= 0:
                            st_label = "OVERDUE"; badge_class = "overdue"
                        elif rem_fh < 50:
                            st_label = "DUE SOON"; badge_class = "soon"

                    txt_date = str(row.get('date_done', ''))
                    txt_fh = str(row.get('fh_done', ''))
                    lc_display = f"{txt_date} ({txt_fh} FH)" if row['date_done'] else "-"
                    lc_clean = lc_display.replace('\n', '<br>') 

                    status_list.append({
                        "Registration": row['ac_reg'], "AD Number": row['ad_number'], "Subject": row['subject'],
                        "Type": row['compliance_type'], "Last Compliance": lc_clean,
                        "Next Due (FH)": due_fh, "Rem FH": rem_fh, "Status": st_label
                    })

                    row_html = "<tr><td>{}</td><td>{}</td><td style='text-align:left'>{}</td><td>{}</td><td>{}</td><td>{}</td><td><span class='status-badge {}'>{}</span></td></tr>".format(
                        row['ac_reg'], row['ad_number'], row['subject'], row['compliance_type'], 
                        lc_clean, due_fh, badge_class, st_label
                    )
                    html_table += row_html

                html_table += "</tbody></table>"
                st.markdown(html_table, unsafe_allow_html=True)
                
                df_final = pd.DataFrame(status_list)
                try:
                    pdf_bytes = generate_pdf_report(df_final)
                    st.download_button(
                        label="📕 Download PDF Report",
                        data=pdf_bytes,
                        file_name="AD_Status_Report.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Gagal memproses PDF: {e}")
            else:
                st.info("Database AD kosong.")
                
        # === HALAMAN 3: COMPONENT STATUS (Bagian yang Di-update) ===
        elif page_name == "Component Status":
            st.header("✈️ Component Status")
            df_util = get_utilization_data()
            list_reg = df_util['Registration'].unique()
            
            # Filter Registrasi Pesawat
            selected_reg = st.selectbox("Select Aircraft Registration:", list_reg, key="reg_comp")
            st.subheader(f"📊 Detailed Component Status - {selected_reg}")
            
            conn = create_connection()
            curr = conn.cursor()
            
            # Ambil Base Data Catalog Pesawat
            curr.execute("SELECT tsn, csn FROM catalog WHERE ac_reg = ?", (selected_reg,))
            base_data = curr.fetchone()
   
            # Ambil Total Akumulasi Jam Terbang dari AML
            curr.execute("SELECT SUM(flight_hours), SUM(landings) FROM aml_utilization WHERE ac_reg = ?", (selected_reg,))
            acc_data = curr.fetchone()
            
            current_ac_hrs = (base_data[0] or 0) + (acc_data[0] or 0)
            current_ac_cyc = (base_data[1] or 0) + (acc_data[1] or 0)
            st.info(f"**Current Airframe Status:** TSN: {current_ac_hrs:.2f} Hours / CSN: {int(current_ac_cyc)} Cycles")

            # 🛠️ INTEGRASI QUERY OTOMATIS BARU LANGSUNG DI SINI:
            # Menggabungkan data installed_components dengan akumulasi waktu real-time
            query = f"""
                SELECT
                    i.component_name, 
                    i.part_number, 
                    i.serial_number, 
                    i.position,
                    i.install_date,
                    -- Menghitung TSN & CSN Aktual Terupdate lewat SQL
                    (i.tsn_at_install + ({current_ac_hrs} - i.install_af_hours)) AS actual_tsn,
                    (i.csn_at_install + ({current_ac_cyc} - i.install_af_cycles)) AS actual_csn,
                    -- Menghitung TSO & CSO Aktual
                    (IFNULL(m_sn.tso, 0) + ({current_ac_hrs} - i.install_af_hours)) AS actual_tso,
                    (IFNULL(m_sn.cso, 0) + ({current_ac_cyc} - i.install_af_cycles)) AS actual_cso,
                    m_pn.tbo_hours, 
                    m_pn.tbo_cycles, 
                    m_pn.tbo_calendar
                FROM installed_components i
                LEFT JOIN master_part_number m_pn ON i.part_number = m_pn.part_number
                LEFT JOIN master_serial_number m_sn ON i.part_number = m_sn.part_number AND i.serial_number = m_sn.serial_number
                WHERE i.ac_reg = '{selected_reg}'
            """

            df = pd.read_sql_query(query, conn)
            df = df.fillna(0)

            if not df.empty:
                status_list = []
                today = datetime.now().date()
                
                for _, row in df.iterrows():
                    # Proteksi matematika memastikan nilai tidak negatif
                    total_tsn = max(0.0, row['actual_tsn'])
                    total_csn = max(0, int(row['actual_csn']))
                    
                    cur_tso = max(0.0, row['actual_tso'])
                    cur_cso = max(0, int(row['actual_cso']))
                    
                    days_since = (today - pd.to_datetime(row['install_date']).date()).days if row['install_date'] else 0

                    # Kalkulasi Sisa Masa Pakai (Remaining Limit)
                    rem_hrs = max(0.0, row['tbo_hours'] - cur_tso) if row['tbo_hours'] > 0 else 0
                    rem_cyc = max(0, int(row['tbo_cycles'] - cur_cso)) if row['tbo_cycles'] > 0 else 0
                    rem_mon = max(0.0, row['tbo_calendar'] - (days_since / 30.44)) if row['tbo_calendar'] > 0 else 0

                    # Format Gabungan String Tampilan Kolom agar rapi (\n)
                    tbo_combined = f"{int(row['tbo_hours'])} H\n{int(row['tbo_cycles'])} C\n{int(row['tbo_calendar'])} M"
                    tsn_combined = f"{total_tsn:.2f} TSN\n{total_csn} CSN\n{int(days_since)} DSN"
                    tso_combined = f"{cur_tso:.2f} TSO\n{cur_cso} CSO\n{int(days_since)} DSO"
                    rem_combined = f"{rem_hrs:.2f} H\n{rem_cyc} C\n{round(rem_mon, 1)} M"

                    status_list.append({
                        "Part Description": row['component_name'],
                        "P/N": row['part_number'],
                        "S/N": row['serial_number'],
                        "Pos": row['position'],
                        "TBO (H/C/M)": tbo_combined,
                        "TSN/CSN/DSN": tsn_combined,
                        "Current Status": tso_combined,
                        "Remaining": rem_combined
                    })

                df_final = pd.DataFrame(status_list)
                
                # Tombol Export Excel
                col_space, col_btn = st.columns([5, 1])
                with col_btn:
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_final.to_excel(writer, index=False, sheet_name='Status')
                    st.download_button(label="📥 Export Excel", data=buffer.getvalue(), file_name=f"Status_{selected_reg}.xlsx")

                # Tampilkan Tabel Data Utama Streamlit
                st.dataframe(
                    df_final, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "TBO (H/C/M)": st.column_config.TextColumn(help="Time Between Overhaul (Hours / Cycles / Months)"),
                        "TSN/CSN/DSN": st.column_config.TextColumn(help="Time Since New / Cycles Since New / Days Since New"),
                        "Current Status": st.column_config.TextColumn(help="Current Time Since Overhaul (TSO / CSO / DSO)"),
                        "Remaining": st.column_config.TextColumn(help="Remaining Life Limits")
                    }
                )
            else:
                st.info("Belum ada data komponen aktif yang terpasang di pesawat ini.")
            conn.close()

    except Exception as e:
        st.error(f"Error pada halaman {page_name}: {e}")