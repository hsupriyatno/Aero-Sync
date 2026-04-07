import streamlit as st
from database import create_connection
import datetime
import pandas as pd
from fpdf import FPDF

# --- FUNGSI GENERATE NOMOR GRN ---
def generate_grn_number():
    conn = create_connection()
    curr = conn.cursor()
    try:
        curr.execute("SELECT COUNT(*) FROM grn_log")
        count = curr.fetchone()[0] + 1
    except:
        count = 1
    finally:
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
    return pdf.output(dest='S').encode('latin-1') 

def show(page_name):
    # --- PRE-LOADING DATA ---
    conn = create_connection()
    try:
        df_master_sn = pd.read_sql("SELECT * FROM master_serial_number", conn)
    except:
        df_master_sn = pd.DataFrame()
    finally:
        conn.close()

    # ==========================================
    # HALAMAN: PARTS CATALOG
    # ==========================================
    if page_name == "Parts Catalog":
        st.subheader("📦 Inventory Management: Parts Catalog")
        tab_pn, tab_sn = st.tabs(["📑 Master Part Number", "🆔 Master Serial Number"])

        with tab_pn:
            if 'edit_mode_pn' not in st.session_state:
                st.session_state.edit_mode_pn = False
                st.session_state.edit_data_pn = {}

            # Perbaikan Duplicate Key: Key form harus berbeda antara mode input dan edit
            form_key = "form_pn_edit" if st.session_state.edit_mode_pn else "form_pn_new"
            form_label = "Update Part Number" if st.session_state.edit_mode_pn else "Register New Part Number"

            with st.form(key=form_key):
                col1, col2 = st.columns(2)
                pn = col1.text_input("Part Number", value=st.session_state.edit_data_pn.get('part_number', ''))
                desc = col1.text_input("Description", value=st.session_state.edit_data_pn.get('description', ''))
                ata = col2.text_input("ATA Chapter", value=st.session_state.edit_data_pn.get('ata_chapter', ''))
                
                cat_list = ["HT", "OC", "CM"]
                cat_idx = cat_list.index(st.session_state.edit_data_pn.get('category', 'HT')) if st.session_state.edit_data_pn.get('category') in cat_list else 0
                cat = col2.selectbox("Category", cat_list, index=cat_idx)
                
                tbo = col1.number_input("TBO Hours", step=0.1, value=float(st.session_state.edit_data_pn.get('tbo', 0.0)))
                cbo = col2.number_input("TBO Cycles", step=1.0, value=float(st.session_state.edit_data_pn.get('cbo', 0.0)))
                dbo = col2.number_input("TBO Calendar (Days)", step=1, value=int(st.session_state.edit_data_pn.get('dbo', 0)))
                
                shelf = col1.number_input("Shelf Life (months)", step=1, value=int(st.session_state.edit_data_pn.get('shelf', 0)))
                date_reg = col2.date_input("Date Registered", value=datetime.date.today())
                
                submitted = st.form_submit_button(form_label)
                if submitted:
                    conn = create_connection()
                    curr = conn.cursor()
                    try:
                        if st.session_state.edit_mode_pn:
                            query = "UPDATE master_part_number SET description=?, ata_chapter=?, category=?, tbo=?, cbo=?, dbo=?, shelf=? WHERE part_number=?"
                            params = (desc, ata, cat, tbo, cbo, dbo, shelf, pn)
                        else:
                            query = "INSERT INTO master_part_number (part_number, description, ata_chapter, category, tbo, cbo, dbo, shelf, date_registered) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                            params = (pn, desc, ata, cat, tbo, cbo, dbo, shelf, str(date_reg))
                        
                        curr.execute(query, params)
                        conn.commit()
                        st.success("Data berhasil disimpan!")
                        st.session_state.edit_mode_pn = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Database Error: {e}")
                    finally:
                        conn.close()

    # ==========================================
    # HALAMAN: INCOMING/OUTGOING
    # ==========================================
    elif page_name == "Incoming/Outgoing":
        st.subheader("🔁 Stock Mutation: Incoming & Outgoing")
        tab_in, tab_out, tab_hist = st.tabs(["📥 Incoming", "📤 Outgoing", "📜 History"])

        with tab_in:
            # MEMULAI FORM
            with st.form(key="form_incoming_aircraft_final"):
                col1, col2 = st.columns(2)
                
                # --- FIELD YANG SEBELUMNYA HILANG KITA KEMBALIKAN ---
                doc_no = col1.text_input("Doc Number (PO/RO)")
                date_rec = col1.date_input("Date Received")
                
                # Ambil list PN (pake try-except supaya kalau tabel error, field gak hilang)
                pn_options = []
                try:
                    conn = create_connection()
                    df_pn = pd.read_sql("SELECT part_number FROM master_part_number", conn)
                    pn_options = df_pn["part_number"].tolist()
                    conn.close()
                except:
                    pn_options = ["Master P/N Belum Terisi"]

                sel_pn = col2.selectbox("Select P/N", options=pn_options)
                sn_in = col2.text_input("S/N Incoming")
                
                src = col1.text_input("Received From (Vendor/Aircraft)")
                loc = col2.selectbox("Storage Location", ["HO Store", "CGK Store"])
                cond = st.radio("Condition", ["S (Serviceable)", "U (Unserviceable)"], horizontal=True)

                # --- TOMBOL SUBMIT (WAJIB ADA DI SINI) ---
                submit_btn = st.form_submit_button("Confirm Receipt")

                if submit_btn:
                    if not sn_in or "Belum Terisi" in str(sel_pn):
                        st.warning("Mohon lengkapi P/N dan S/N terlebih dahulu.")
                    else:
                        # PROSES SIMPAN KE AIRCRAFT.DB
                        conn = create_connection()
                        curr = conn.cursor()
                        try:
                            # 1. Update Lokasi (Pakai try per kolom agar tidak crash)
                            try:
                                curr.execute("UPDATE master_serial_number SET status=?, current_location='Store', location=? WHERE serial_number=?", 
                                           (cond[0], loc, sn_in))
                            except: pass # Lewati jika kolom belum ada
                            
                            # 2. Catat Transaksi
                            curr.execute("""
                                INSERT INTO inventory_transaction (date, doc_number, part_number, serial_number, store_location, status) 
                                VALUES (?,?,?,?,?,?)
                            """, (str(date_rec), doc_no, sel_pn, sn_in, loc, cond[0]))
                            
                            conn.commit()
                            st.success(f"✅ Data S/N {sn_in} Berhasil Disimpan!")
                        except Exception as e:
                            st.error(f"Gagal simpan: {e}")
                        finally:
                            conn.close()
        with tab_out:
            st.write("📤 **Aircraft Installation / Parts Issuance**")
            with st.form(key="form_outgoing_aircraft"):
                c1, c2 = st.columns(2)
                date_out = c1.date_input("Date Out / Installed")
                doc_ref = c1.text_input("Reference (Work Order/REQ)")
                
                # Ambil list S/N yang statusnya ada di 'Store' (Serviceable)
                sn_options = []
                try:
                    conn = create_connection()
                    query = "SELECT serial_number FROM master_serial_number WHERE current_location = 'Store'"
                    df_sn = pd.read_sql(query, conn)
                    sn_options = df_sn["serial_number"].tolist()
                    conn.close()
                except:
                    sn_options = []

                sel_sn = c2.selectbox("Select S/N to Issue", options=sn_options if sn_options else ["No Stock Available"])
                ac_reg = c2.text_input("Installed on Aircraft (e.g. PK-OCA)")
                rem = st.text_area("Remark / Reason")

                submit_out = st.form_submit_button("Confirm Issue")

                if submit_out:
                    if "No Stock" in str(sel_sn) or not ac_reg:
                        st.warning("Mohon pilih S/N dan isi Registrasi Pesawat.")
                    else:
                        conn = create_connection()
                        curr = conn.cursor()
                        try:
                            # Update status S/N menjadi terpasang di pesawat
                            curr.execute("""
                                UPDATE master_serial_number 
                                SET current_location='Aircraft', location=? 
                                WHERE serial_number=?
                            """, (ac_reg, sel_sn))
                            
                            # Catat di transaksi sebagai Outgoing
                            curr.execute("""
                                INSERT INTO inventory_transaction (date, doc_number, serial_number, store_location, remark, status) 
                                VALUES (?,?,?,?,?,?)
                            """, (str(date_out), doc_ref, sel_sn, ac_reg, rem, 'OUT'))
                            
                            conn.commit()
                            st.success(f"✅ S/N {sel_sn} berhasil dikeluarkan ke {ac_reg}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal Outgoing: {e}")
                        finally:
                            conn.close()

        with tab_hist:
            st.write("📜 **Transaction Logs (Aircraft.db)**")
            
            # Buat koneksi untuk membaca history
            conn = create_connection()
            try:
                # Kita ambil data terbaru ada di paling atas (ORDER BY id DESC)
                df_history = pd.read_sql("SELECT * FROM inventory_transaction ORDER BY id DESC", conn)
                
                if not df_history.empty:
                    # Menampilkan tabel yang bisa di-search dan di-filter
                    st.dataframe(df_history, use_container_width=True, hide_index=True)
                    
                    # Opsi download history ke Excel/CSV jika Bapak butuh
                    csv = df_history.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download History (.csv)", data=csv, file_name="inventory_history.csv", mime="text/csv")
                else:
                    st.info("Belum ada data transaksi masuk atau keluar.")
                    
            except Exception as e:
                st.error(f"Gagal memuat history: {e}")
                # Tombol darurat jika tabel ternyata belum ada di aircraft.db
                if st.button("Initialize History Table"):
                    curr = conn.cursor()
                    curr.execute("""
                        CREATE TABLE IF NOT EXISTS inventory_transaction (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date TEXT, 
                            doc_number TEXT, 
                            part_number TEXT, 
                            serial_number TEXT, 
                            store_location TEXT, 
                            received_from TEXT,
                            status TEXT, 
                            remark TEXT
                        )
                    """)
                    conn.commit()
                    st.rerun()
            finally:
                conn.close()                   