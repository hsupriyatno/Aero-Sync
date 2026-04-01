import streamlit as st
from database import create_connection
import datetime
import pandas as pd
import io
from fpdf2 import FPDF
# --- FUNGSI GENERATE NOMOR GRN ---
def generate_grn_number():
    conn = create_connection()
    curr = conn.cursor()
    # Pastikan tabel grn_log sudah ada di database Bapak
    try:
        curr.execute("SELECT COUNT(*) FROM grn_log")
        count = curr.fetchone()[0] + 1
    except:
        count = 1
    conn.close()
    today = datetime.date.today()
    return f"GRN/{today.year}/{today.strftime('%m')}/{count:03d}"

# --- FUNGSI BUAT PDF GRN ---
def create_grn_pdf(grn_info):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "GOOD RECEIVE NOTE (GRN)", 1, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    
    details = [
        ["GRN Number", grn_info['grn_no']],
        ["Date Received", grn_info['date']],
        ["Document Ref", grn_info['doc_ref']],
        ["Part Number", grn_info['pn']],
        ["Serial Number", grn_info['sn']],
        ["Condition", grn_info['status']],
        ["Received From", grn_info['source']],
        ["Storage Loc", grn_info['loc']]
    ]
    
    for row in details:
        pdf.cell(50, 10, row[0], 1)
        pdf.cell(140, 10, str(row[1]), 1, 1)
    
    pdf.ln(20)
    pdf.cell(95, 10, "Received By (Storeman),", 0, 0, 'C')
    pdf.cell(95, 10, "Inspected By (Part Inspector),", 0, 1, 'C')
    pdf.ln(20)
    pdf.cell(95, 10, "____________________", 0, 0, 'C')
    pdf.cell(95, 10, "____________________", 0, 1, 'C')
    return pdf.output(dest="S").encode("latin-1")

def show(page_name):
    # --- PRE-LOADING DATA ---
    conn = create_connection()
    # Tambahkan error handling jika kolom current_location belum ada
    try:
        df_master_sn = pd.read_sql("SELECT * FROM master_serial_number", conn)
    except:
        st.error("Database mismatch: Pastikan kolom 'current_location' sudah ada di tabel master_serial_number.")
        df_master_sn = pd.DataFrame()
    conn.close()

    # ==========================================
    # HALAMAN: PARTS CATALOG
    # ==========================================
    if page_name == "Parts Catalog":
        st.subheader("📦 Inventory Management: Parts Catalog")
        tab_pn, tab_sn = st.tabs(["📑 Master Part Number", "🆔 Master Serial Number"])

        with tab_pn:
            st.info("Input Part Number baru di sini sebelum mendaftarkan Serial Number.")
            with st.form("form_master_pn"):
                col1, col2 = st.columns(2)
                pn = col1.text_input("Part Number")
                desc = col1.text_input("Description")
                ata = col2.text_input("ATA Chapter")
                cat = col2.selectbox("Category", ["HT", "OC"])
                tbo_h = col1.number_input("TBO Hours", step=0.1)
                tbo_c = col2.number_input("TBO Cycles", step=1.0)
                tbo_cal = col2.number_input("TBO Calendar (Days)", step=1)
                shelf = col1.number_input("Shelf Life (months)", step=1)
                date_reg = col2.date_input("Date Registered", value=datetime.date.today())
                
                if st.form_submit_button("Register New Part Number"):
                    if pn:
                        conn = create_connection()
                        curr = conn.cursor()
                        query = """INSERT INTO master_part_number 
                                   (part_number, description, ata_chapter, category, tbo_hours, tbo_cycles, tbo_calendar, shelf, date_registered) 
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                        curr.execute(query, (pn, desc, ata, cat, tbo_h, tbo_c, tbo_cal, shelf, date_reg))
                        conn.commit()
                        conn.close()
                        st.success(f"P/N {pn} berhasil diregistrasi!")
                        st.rerun()
                    else:
                        st.error("P/N tidak boleh kosong.")

            st.markdown("---")
            st.subheader("📋 Registered Parts List")
            conn = create_connection()
            df_pn = pd.read_sql("SELECT * FROM master_part_number ORDER BY date_registered DESC", conn)
            conn.close()
            st.dataframe(df_pn, use_container_width=True, hide_index=True)

        with tab_sn:
            st.info("Serial Number hanya bisa didaftarkan untuk Part Number yang sudah ada.")
            conn = create_connection()
            curr = conn.cursor()
            curr.execute("SELECT part_number FROM master_part_number")
            existing_pn = [row[0] for row in curr.fetchall()]
            conn.close()

            if not existing_pn:
                st.warning("Belum ada Part Number terdaftar.")
            else:
                with st.form("form_master_sn"):
                    col_a, col_b = st.columns(2)
                    selected_pn_input = col_a.selectbox("Select Part Number", existing_pn)
                    sn = col_b.text_input("Serial Number")
            
                    c1, c2, c3 = st.columns(3)
                    tsn = c1.number_input("TSN", step=0.1)
                    csn = c2.number_input("CSN", step=0.1)
                    dsn = c3.number_input("DSN", step=0.1)
                    tso = c1.number_input("TSO", step=0.1)
                    cso = c2.number_input("CSO", step=0.1)
                    dso = c3.number_input("DSO", step=0.1)
                    date_registered = c1.date_input("Date Registered_sn", value=datetime.date.today())
                    status_sn = c2.selectbox("Status Initial", ["S", "U"])
                    location_sn = st.text_input("Initial Location", value="Store")

                    if st.form_submit_button("Register New Serial Number"):
                        if sn:
                            conn = create_connection()
                            curr = conn.cursor()
                            try:
                                query = """INSERT INTO master_serial_number 
                                           (part_number, serial_number, tsn, csn, dsn, tso, cso, dso, status, current_location, date_registered) 
                                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                                curr.execute(query, (selected_pn_input, sn, tsn, csn, dsn, tso, cso, dso, status_sn, location_sn, date_registered))
                                conn.commit()
                                st.success(f"S/N {sn} berhasil diregistrasi!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Gagal simpan: {e}")
                            finally:
                                conn.close()

    # ==========================================
    # HALAMAN: PARTS IN STOCK
    # ==========================================
    elif page_name == "Parts In Stock":
        st.subheader("📦 Store Inventory: Serviceable Parts")
        if not df_master_sn.empty:
            df_stock = df_master_sn[(df_master_sn["status"] == 'S') & (df_master_sn["current_location"] != 'Aircraft')]
            if df_stock.empty:
                st.info("Tidak ada part Serviceable di gudang.")
            else:
                st.dataframe(df_stock, use_container_width=True)

    # ==========================================
    # HALAMAN: INCOMING/OUTGOING
    # ==========================================
    elif page_name == "Incoming/Outgoing":
        st.subheader("🔁 Stock Mutation: Incoming & Outgoing")
        tab_in, tab_out, tab_history = st.tabs(["📥 Incoming (Received)", "📤 Outgoing (Issued)", "📜 Transaction History"])

        # --- TAB 1: INCOMING ---
        with tab_in:
            st.write("### 📥 Receive Part to Inventory")
            with st.form("form_receive"):
                col1, col2 = st.columns(2)
                doc_no = col1.text_input("Document Number (PO/RO/Release Cert)")
                date_rec = col1.date_input("Date Received", datetime.date.today())
                
                conn = create_connection()
                df_pn_list = pd.read_sql("SELECT part_number FROM master_part_number", conn)
                conn.close()
                
                selected_pn = col2.selectbox("Select P/N", df_pn_list["part_number"].unique()) if not df_pn_list.empty else col2.warning("No P/N")
                sn_input = col2.text_input("Serial Number (Incoming)")

                st.divider()
                c1, c2 = st.columns(2)
                source_type = c1.selectbox("Received From", ["Vendor", "Workshop", "Aircraft", "Other Store"])
                source_detail = c2.text_input("Detail Source (Name/Reg)")
                part_status = c1.radio("Condition", ["S", "U"], horizontal=True)
                loc_stored = c2.selectbox("Storage Destination", ["HO Store", "CGK Store", "HLP Store", "BPN Store"])
                
                submitted_in = st.form_submit_button("Confirm Receipt", key="btn_confirm_in")

            if submitted_in:
                if sn_input and source_detail:
                    grn_no = generate_grn_number() 
                    conn = create_connection()
                    curr = conn.cursor()
                    
                    # Update/Insert Logic
                    curr.execute("""
                        UPDATE master_serial_number 
                        SET status=?, current_location='Store', location=? 
                        WHERE part_number=? AND serial_number=?
                    """, (part_status, loc_stored, selected_pn, sn_input))
                    
                    curr.execute("INSERT INTO grn_log (grn_number, date_created, part_number, serial_number) VALUES (?,?,?,?)",
                                (grn_no, str(date_rec), selected_pn, sn_input))
                    
                    conn.commit()
                    conn.close()

                    st.session_state['last_grn'] = {
                        'grn_no': grn_no, 'date': str(date_rec), 'doc_ref': doc_no,
                        'pn': selected_pn, 'sn': sn_input, 'status': "SERVICEABLE" if part_status == 'S' else "UNSERVICEABLE",
                        'source': f"{source_type} ({source_detail})", 'loc': loc_stored
                    }
                    st.success(f"✅ Berhasil! Nomor GRN: {grn_no}")

            if 'last_grn' in st.session_state:
                g = st.session_state['last_grn']
                btn_pdf = create_grn_pdf(g)
                st.download_button("📄 Print GRN Document", data=btn_pdf, file_name=f"GRN_{g['grn_no']}.pdf", mime="application/pdf")

        # --- TAB 2: OUTGOING ---
        with tab_out:
            st.write("### 📤 Issue Part from Inventory")
            if not df_master_sn.empty:
                df_serviceable = df_master_sn[(df_master_sn["status"] == 'S') & (df_master_sn["current_location"] != 'Aircraft')]
                if df_serviceable.empty:
                    st.warning("Tidak ada barang Serviceable.")
                else:
                    out_sn = st.selectbox("Select S/N to Issue", df_serviceable["serial_number"].unique())
                    with st.form("form_out"):
                        out_date = st.date_input("Date Issuance", datetime.date.today())
                        out_ref = st.text_input("Aircraft Reg / Destination")
                        if st.form_submit_button("Submit Issuance"):
                            conn = create_connection()
                            curr = conn.cursor()
                            curr.execute("UPDATE master_serial_number SET current_location='Aircraft', location=? WHERE serial_number=?", (out_ref, out_sn))
                            curr.execute("INSERT INTO inventory_transaction (date, serial_number, status, remark) VALUES (?,?,'ISSUED',?)", (str(out_date), out_sn, out_ref))
                            conn.commit()
                            conn.close()
                            st.success("Part Issued!")
                            st.rerun()

        # --- TAB 3: HISTORY ---
        with tab_history:
            conn = create_connection()
            try:
                df_hist = pd.read_sql("SELECT * FROM inventory_transaction ORDER BY date DESC", conn)
                st.dataframe(df_hist, use_container_width=True)
            except:
                st.info("Belum ada riwayat transaksi.")
            conn.close()
