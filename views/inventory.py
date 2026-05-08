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
    """Fungsi untuk mengambil histori penerbangan"""
    conn = create_connection()
    try:
        query = """
        SELECT date AS [Date], aml_no AS [AML No], flight_hours AS [FH], 
               landings AS [FC], ac_tsn AS [TSN], ac_csn AS [CSN],
               departure AS [From], arrival AS [To]
        FROM aml_utilization
        WHERE ac_reg = ? AND date BETWEEN ? AND ?
        ORDER BY date DESC, aml_no DESC
        """
        df = pd.read_sql(query, conn, params=(ac_reg, start_date, end_date))
        return df
    except Exception as e:
        st.error(f"Gagal mengambil histori: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def generate_pdf_report(df_input):
    """Generator PDF yang aman dari backslash error"""
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
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 2. FUNGSI TAMPILAN UTAMA (SHOW)
# ==========================================

def show(page_name):
    # CSS Master
    st.markdown("""
        <style>
        .report-table { width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 20px; }
        .report-table th { background-color: #1a3a5f; color: white; border: 1px solid #ddd; padding: 8px; }
        .report-table td { border: 1px solid #ddd; padding: 4px; text-align: center; }
        .status-badge { padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 10px; }
        .normal { background-color: #d4edda; color: #155724; }
        .overdue { background-color: #f8d7da; color: #721c24; }
        .soon { background-color: #fff3cd; color: #856404; }
        .metric-card { background: #f8f9fa; padding: 10px; border-radius: 8px; border-left: 5px solid #1a3a5f; }
        </style>
    """, unsafe_allow_html=True)

    conn = create_connection()

    try:
        df_util_global = get_utilization_data()

        # --- AIRCRAFT UTILIZATION RECORD ---
        if page_name == "Aircraft Utilization Record":
            st.header("✈️ Aircraft Utilization Record")
            
            # Metrics
            cols = st.columns(len(df_util_global))
            for i, row in df_util_global.iterrows():
                with cols[i]:
                    st.markdown(f"""<div class="metric-card"><small>{row['Type']}</small><br><b>{row['Registration']}</b><br>
                        TSN: {row['Current TSN']:.2f}<br>CSN: {int(row['Current CSN'])}</div>""", unsafe_allow_html=True)
            
            st.divider()
            st.dataframe(df_util_global, use_container_width=True, hide_index=True)
            
            # History Filter
            st.markdown("### 🔍 Detailed Utilization History")
            c1, c2, c3 = st.columns(3)
            with c1:
                sel_reg = st.selectbox("Select Reg:", df_util_global['Registration'].unique(), key="util_sel")
            with c2:
                s_date = st.date_input("Start:", value=datetime(2026, 1, 1), key="util_start")
            with c3:
                e_date = st.date_input("End:", value=datetime.now(), key="util_end")

            df_hist = get_detailed_history(sel_reg, s_date.strftime('%Y-%m-%d'), e_date.strftime('%Y-%m-%d'))
            if not df_hist.empty:
                st.dataframe(df_hist, use_container_width=True, hide_index=True)
            else:
                st.info("No flight records found.")

        # --- AIRWORTHINESS DIRECTIVE STATUS ---
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
                html_table = '<table class="report-table"><thead><tr><th>Reg</th><th>AD Number</th><th>Subject</th><th>Type</th><th>Last Compliance</th><th>Next FH</th><th>Status</th></tr></thead><tbody>'
                
                for _, row in df_ad.iterrows():
                    ac_info = df_util_global[df_util_global['Registration'] == row['ac_reg']]
                    curr_fh = ac_info['Current TSN'].values[0] if not ac_info.empty else 0
                    
                    due_fh = row['fh_done'] + row['interval_fh'] if row['date_done'] and row['interval_fh'] > 0 else "-"
                    rem_fh = round(due_fh - curr_fh, 2) if isinstance(due_fh, (int, float)) else "-"
                    
                    st_label, badge = "NORMAL", "normal"
                    if isinstance(rem_fh, (int, float)):
                        if rem_fh <= 0: st_label, badge = "OVERDUE", "overdue"
                        elif rem_fh < 50: st_label, badge = "DUE SOON", "soon"

                    status_list.append({
                        "Registration": row['ac_reg'], "AD Number": row['ad_number'], "Subject": row['subject'],
                        "Type": row['compliance_type'], "Last Compliance": f"{row['date_done']} ({row['fh_done']})",
                        "Next Due (FH)": due_fh, "Rem FH": rem_fh, "Status": st_label
                    })

                    html_table += "<tr><td>{}</td><td>{}</td><td style='text-align:left'>{}</td><td>{}</td><td>{} ({})</td><td>{}</td><td><span class='status-badge {}'>{}</span></td></tr>".format(
                        row['ac_reg'], row['ad_number'], row['subject'], row['compliance_type'], row['date_done'], row['fh_done'], due_fh, badge, st_label
                    )
                
                html_table += "</tbody></table>"
                st.markdown(html_table, unsafe_allow_html=True)
                
                df_final = pd.DataFrame(status_list)
                c1, c2 = st.columns(2)
                with c1:
                    pdf = generate_pdf_report(df_final)
                    st.download_button("📕 Download PDF", pdf, "AD_Report.pdf", "application/pdf")
                with c2:
                    csv = df_final.to_csv(index=False).encode('utf-8')
                    st.download_button("📊 Download CSV", csv, "AD_Report.csv", "text/csv")

        # --- COMPONENT STATUS ---
        elif page_name == "Component Status":
            st.header("⚙️ Component Status")
            selected_reg = st.selectbox("Select Aircraft:", df_util_global['Registration'].unique(), key="comp_sel")
            
            query_comp = f"""
                SELECT i.component_name, i.part_number, i.parent_sn, i.position,
                       i.install_af_hours, i.tsn_at_install, i.tso, m.tbo_hours
                FROM installed_components i
                LEFT JOIN master_part_number m ON i.part_number = m.part_number
                WHERE i.ac_reg = '{selected_reg}'
            """
            df_comp = pd.read_sql(query_comp, conn)
            
            if not df_comp.empty:
                ac_now = df_util_global[df_util_global['Registration'] == selected_reg]['Current TSN'].values[0]
                res_list = []
                for _, r in df_comp.iterrows():
                    usage = ac_now - r['install_af_hours']
                    curr_tsn = r['tsn_at_install'] + usage
                    rem = r['tbo_hours'] - (r['tso'] + usage) if r['tbo_hours'] > 0 else 0
                    
                    res_list.append({
                        "Component": r['component_name'], "P/N": r['part_number'], "S/N": r['parent_sn'],
                        "Position": r['position'], "Current TSN": round(curr_tsn, 2), 
                        "Remaining FH": round(rem, 2) if rem > 0 else "N/A"
                    })
                st.table(pd.DataFrame(res_list))

    except Exception as e:
        st.error(f"Error pada halaman {page_name}: {e}")
    finally:
        conn.close()
