# Pastikan import di bagian paling atas file seperti ini:
# Pastikan import di bagian paling atas file seperti ini:
import streamlit as st
import pandas as pd
from datetime import date # Penting agar date.today() berfungsi
import sqlite3
import os

def create_connection():
    # Sesuaikan nama file database dengan yang Anda gunakan di AERO-SYNCH
    db_file = "aircraft.db" 
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        st.error(f"Gagal koneksi ke database: {e}")
    return conn


def show(page_name):
    if page_name == "Parts Catalog":
        st.subheader("📦 Inventory Management: Parts Catalog")
        tab_pn, tab_sn = st.tabs(["📑 Master Part Number", "🆔 Master Serial Number"])

        # ==========================================
        # --- TAB 1: MASTER PART NUMBER ---
        # ==========================================
        with tab_pn:
            if 'edit_mode_pn' not in st.session_state:
                st.session_state.edit_mode_pn = False
            if 'edit_data_pn' not in st.session_state:
                st.session_state.edit_data_pn = {}

            # Gunakan FORM agar tombol submit terbaca
            with st.form(key="form_pn_v3"):
                st.write("### Register / Update Part Number")
                
                c1, c2 = st.columns(2)
                pn_input = c1.text_input("Part Number (P/N)", value=st.session_state.edit_data_pn.get('part_number', ''))
                ata_input = c2.text_input("ATA Chapter", value=st.session_state.edit_data_pn.get('ata_chapter', ''))
                
                c3, c4 = st.columns(2)
                desc_input = c3.text_input("Description", value=st.session_state.edit_data_pn.get('description', ''))
                cat_input = c4.selectbox("Category", ["HT", "OC", "CM"], 
                                       index=["HT", "OC", "CM"].index(st.session_state.edit_data_pn.get('category', 'HT')))
                
                st.markdown("---")
                c5, c6 = st.columns(2)
                tbo_h = c5.number_input("TBO Hours", value=float(st.session_state.edit_data_pn.get('tbo_hours', 0.0)))
                tbo_c = c6.number_input("TBO Cycles", value=float(st.session_state.edit_data_pn.get('tbo_cycles', 0.0)))

                c7, c8 = st.columns(2)
                s_life = c7.number_input("Shelf Life (months)", value=int(st.session_state.edit_data_pn.get('shelf_life', 0)))
                tbo_cal = c8.number_input("TBO Calendar (Days)", value=int(st.session_state.edit_data_pn.get('tbo_calendar', 0)))
                
                # Perbaikan error datetime: pakai date.today() langsung
                date_reg = st.date_input("Date Registered", value=date.today())
                
                # TOMBOL SUBMIT (Wajib ada di dalam form)
                submitted = st.form_submit_button("Save Part Number")
                
                if submitted:
                    if not pn_input:
                        st.error("Part Number tidak boleh kosong!")
                    else:
                        conn = create_connection()
                        curr = conn.cursor()
                        try:
                            # Logika simpan data
                            curr.execute("""
                                INSERT OR REPLACE INTO master_part_number 
                                (part_number, description, ata_chapter, category, tbo_hours, tbo_cycles, shelf_life, tbo_calendar, date_registered)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                                (pn_input, desc_input, ata_input, cat_input, tbo_h, tbo_c, s_life, tbo_cal, str(date_reg)))
                            conn.commit()
                            st.success(f"Data {pn_input} Berhasil Disimpan!")
                            st.session_state.edit_mode_pn = False
                            st.session_state.edit_data_pn = {}
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error Database: {e}")
                        finally:
                            conn.close()

            # --- TAMPILAN TABEL ---
            st.write("---")
            st.write("#### 📑 Registered Part Number List")
            
            conn = create_connection()
            # Gunakan try-except untuk handle kolom ID jika tidak ada
            try:
                df_pn = pd.read_sql("SELECT * FROM master_part_number", conn)
            except:
                df_pn = pd.DataFrame() # Jika tabel belum ada
            conn.close()

            if not df_pn.empty:
                # PERBAIKAN: Ganti .bold() dengan Markdown **
                h1, h2, h3, h4, h5 = st.columns([1, 3, 4, 2, 2])
                h1.markdown("**ID**")
                h2.markdown("**P/N**")
                h3.markdown("**Description**")
                h4.markdown("**Cat**")
                h5.markdown("**Action**")
                
                for idx, row in df_pn.iterrows():
                    r = st.columns([1, 3, 4, 2, 2])
                    # Cek jika kolom 'id' ada, jika tidak pakai index
                    display_id = row['id'] if 'id' in row else idx
                    r[0].write(display_id)
                    r[1].write(row['part_number'])
                    r[2].write(row['description'])
                    r[3].write(row['category'])
                    
                    # Tombol Aksi
                    be, bd = r[4].columns(2)
                    if be.button("📝", key=f"ed_pn_{idx}"):
                        st.session_state.edit_mode_pn = True
                        st.session_state.edit_data_pn = row.to_dict()
                        st.rerun()
                    
                    if bd.button("🗑️", key=f"dl_pn_{idx}"):
                        # Logika delete sederhana
                        c = create_connection()
                        c.execute(f"DELETE FROM master_part_number WHERE part_number='{row['part_number']}'")
                        c.commit()
                        c.close()
                        st.rerun()


        # --- TAB 2: MASTER SERIAL NUMBER ---
        with tab_sn:
            st.write("### 🆕 Register New Serial Number")
            conn = create_connection()
            # Ambil opsi P/N dari master
            df_pn_opts = pd.read_sql("SELECT part_number FROM master_part_number", conn)
            pn_list = df_pn_opts['part_number'].tolist() if not df_pn_opts.empty else ["N/A"]
            
            with st.form("form_add_sn"):
                sel_pn = st.selectbox("Select Part Number", options=pn_list)
                c1, c2 = st.columns(2)
                sn_input = c1.text_input("Serial Number (S/N)")
                loc_input = c1.selectbox("Initial Location", ["HO Store", "Field", "Transit"])
                stat_input = c2.selectbox("Condition", ["S", "U", "AR", "SCRAP"])
                
                if st.form_submit_button("Register S/N"):
                    curr = conn.cursor()
                    curr.execute("INSERT INTO master_serial_number (part_number, serial_number, current_location, status) VALUES (?,?,?,?)",
                                 (sel_pn, sn_input, loc_input, stat_input))
                    conn.commit()
                    st.rerun()

            st.divider()
            # Tampilkan Tabel S/N
            df_sn_list = pd.read_sql("SELECT * FROM master_serial_number ORDER BY id DESC", conn)
            if not df_sn_list.empty:
                st.write("#### 🆔 Registered Serial Number List")
                # Header Tabel
                h = st.columns([1, 3, 3, 2, 2, 2])
                cols = ["ID", "P/N", "S/N", "Location", "Status", "Action"]
                for i, col_name in enumerate(cols): h[i].markdown(f"**{col_name}**")
                
                for _, row in df_sn_list.iterrows():
                    r = st.columns([1, 3, 3, 2, 2, 2])
                    r[0].write(row['id'])
                    r[1].write(row['part_number'])
                    r[2].write(row['serial_number'])
                    r[3].write(row['current_location'])
                    r[4].write(row['status'])
                    
                    btn_edit, btn_del = r[5].columns(2)
                    if btn_edit.button("📝", key=f"ed_{row['id']}"):
                        st.session_state.update({'edit_mode':True, 'edit_id':row['id'], 'edit_pn':row['part_number'], 
                                                 'edit_sn':row['serial_number'], 'edit_loc':row['current_location'], 'edit_stat':row['status']})
                        st.rerun()
                    if btn_del.button("🗑️", key=f"dl_{row['id']}"):
                        delete_sn(row['id'])
            # --- FORM EDIT MASTER S/N (Floating Expander) ---
            if st.session_state.get('edit_mode'):
                with st.expander("🛠️ EDIT DATA SERIAL NUMBER", expanded=True):
                    with st.form("form_edit_sn"):
                        st.write(f"Editing ID: {st.session_state['edit_id']}")
                        new_pn = st.text_input("Part Number", value=st.session_state['edit_pn'])
                        new_sn = st.text_input("Serial Number", value=st.session_state['edit_sn'])
                        new_loc = st.text_input("Location", value=st.session_state['edit_loc'])
                        new_stat = st.selectbox("Status", ["S", "US", "AR", "SCRAP"], 
                                                index=["S", "US", "AR", "SCRAP"].index(st.session_state['edit_stat']) if st.session_state['edit_stat'] in ["S", "US", "AR", "SCRAP"] else 0)
                
                        c_save, c_cancel = st.columns(2)
                        if c_save.form_submit_button("✅ Save Changes"):
                            update_sn(st.session_state['edit_id'], new_pn, new_sn, new_loc, new_stat)
                            st.session_state['edit_mode'] = False
                    
                        if c_cancel.form_submit_button("❌ Cancel"):
                            st.session_state['edit_mode'] = False
                            st.rerun()
            conn.close()

    # ==========================================
    # HALAMAN: INCOMING/OUTGOING
    # ==========================================
    elif page_name == "Incoming/Outgoing":
        st.subheader("🔁 Stock Mutation: Incoming & Outgoing")
        tab_in, tab_out, tab_hist = st.tabs(["📥 Incoming", "📤 Outgoing", "📜 History"])

        with tab_in:
            with st.form("form_incoming"):
                c1, c2 = st.columns(2)
                doc = c1.text_input("Doc Number (PO/RO/Note)")
                dt_in = c1.date_input("Date Received", key="dt_in")
                
                conn = create_connection()
                pn_list = pd.read_sql("SELECT part_number FROM master_part_number", conn)['part_number'].tolist()
                conn.close()
                
                sel_pn_in = c2.selectbox("Part Number", options=pn_list)
                sn_in = c2.text_input("Serial Number Incoming")
                loc_in = st.selectbox("Storage Destination", ["HO Store", "CGK Store"])
                
                if st.form_submit_button("Confirm Receipt"):
                    conn = create_connection()
                    curr = conn.cursor()
                    # 1. Update/Insert ke Master S/N
                    curr.execute("UPDATE master_serial_number SET current_location=?, status='S' WHERE serial_number=?", (loc_in, sn_in))
                    # 2. Catat Log
                    curr.execute("INSERT INTO inventory_transaction (date, doc_number, part_number, serial_number, store_location, status) VALUES (?,?,?,?,?,?)",
                                 (str(dt_in), doc, sel_pn_in, sn_in, loc_in, 'IN'))
                    conn.commit()
                    conn.close()
                    st.success(f"S/N {sn_in} received at {loc_in}")

        with tab_out:
            with st.form("form_outgoing"):
                c1, c2 = st.columns(2)
                doc_out = c1.text_input("Work Order / Reference")
                dt_out = c1.date_input("Date Issue")
                
                conn = create_connection()
                # Hanya S/N yang ada di Store yang bisa keluar
                df_avail = pd.read_sql("SELECT serial_number FROM master_serial_number WHERE current_location LIKE '%Store%'", conn)
                sn_avail = df_avail['serial_number'].tolist() if not df_avail.empty else ["No Stock"]
                
                sel_sn_out = c2.selectbox("Select S/N to Issue", options=sn_avail)
                ac_reg = c2.text_input("Install on Aircraft (Registration)")
                
                if st.form_submit_button("Confirm Issue"):
                    if sel_sn_out != "No Stock":
                        curr = conn.cursor()
                        curr.execute("UPDATE master_serial_number SET current_location='Aircraft', status='S' WHERE serial_number=?", (sel_sn_out,))
                        curr.execute("INSERT INTO inventory_transaction (date, doc_number, serial_number, store_location, status, remark) VALUES (?,?,?,?,?,?)",
                                     (str(dt_out), doc_out, sel_sn_out, ac_reg, 'OUT', f"Installed on {ac_reg}"))
                        conn.commit()
                        st.success(f"S/N {sel_sn_out} issued to {ac_reg}")
                    conn.close()

        with tab_hist:
            conn = create_connection()
            df_hist = pd.read_sql("SELECT * FROM inventory_transaction ORDER BY id DESC", conn)
            st.dataframe(df_hist, use_container_width=True)
            conn.close()                   