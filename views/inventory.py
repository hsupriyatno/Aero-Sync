import streamlit as st
import pandas as pd
from datetime import date # Penting agar date.today() berfungsi
import sqlite3
import os

def create_connection():
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

            with st.form(key="form_pn_v3"):
                st.write("### Register / Update Part Number")
                
                c1, c2 = st.columns(2)
                pn_input = c1.text_input("Part Number (P/N)", value=st.session_state.edit_data_pn.get('part_number', ''))
                ata_input = c2.text_input("ATA Chapter", value=st.session_state.edit_data_pn.get('ata_chapter', ''))
                
                c3, c4 = st.columns(2)
                desc_input = c3.text_input("Description", value=st.session_state.edit_data_pn.get('description', ''))
                
                current_cat = st.session_state.edit_data_pn.get('category', 'HT')
                cat_options = ["HT", "OC", "CM"]
                cat_index = cat_options.index(current_cat) if current_cat in cat_options else 0
                cat_input = c4.selectbox("Category", cat_options, index=cat_index)
                
                st.markdown("---")
                c5, c6 = st.columns(2)
                tbo_h = c5.number_input("TBO Hours", value=float(st.session_state.edit_data_pn.get('tbo_hours', 0.0)))
                tbo_c = c6.number_input("TBO Cycles", value=float(st.session_state.edit_data_pn.get('tbo_cycles', 0)))

                c7, c8 = st.columns(2)
                s_life = c7.number_input("Shelf Life (months)", value=int(st.session_state.edit_data_pn.get('shelf_life', 0)))
                tbo_cal = c8.number_input("TBO Calendar (Days)", value=int(st.session_state.edit_data_pn.get('tbo_calendar', 0)))
                
                date_reg = st.date_input("Date Registered", value=date.today())
                submitted = st.form_submit_button("Save Part Number")
                
                if submitted:
                    if not pn_input:
                        st.error("Part Number tidak boleh kosong!")
                    else:
                        conn = create_connection()
                        curr = conn.cursor()
                        try:
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

            st.write("---")
            st.write("#### 📑 Registered Part Number List")
            
            conn = create_connection()
            try:
                df_pn = pd.read_sql("SELECT * FROM master_part_number", conn)
            except:
                df_pn = pd.DataFrame() 
            conn.close()

            if not df_pn.empty:
                h1, h2, h3, h4, h5 = st.columns([1, 3, 4, 2, 2])
                h1.markdown("**ID**")
                h2.markdown("**P/N**")
                h3.markdown("**Description**")
                h4.markdown("**Cat**")
                h5.markdown("**Action**")
                
                for idx, row in df_pn.iterrows():
                    r = st.columns([1, 3, 4, 2, 2])
                    display_id = row['id'] if 'id' in row else idx
                    r[0].write(display_id)
                    r[1].write(row['part_number'])
                    r[2].write(row['description'])
                    r[3].write(row['category'])
                    
                    be, bd = r[4].columns(2)
                    if be.button("📝", key=f"ed_pn_{idx}"):
                        st.session_state.edit_mode_pn = True
                        st.session_state.edit_data_pn = row.to_dict()
                        st.rerun()
                    
                    if bd.button("🗑️", key=f"dl_pn_{idx}"):
                        c = create_connection()
                        c.execute(f"DELETE FROM master_part_number WHERE part_number='{row['part_number']}'")
                        c.commit()
                        c.close()
                        st.rerun()

        # ==========================================
        # --- TAB 2: MASTER SERIAL NUMBER ---
        # ==========================================
        with tab_sn:
            st.write("### 🆕 Register New Serial Number")
            conn = create_connection()
            
            df_pn_opts = pd.read_sql("SELECT part_number FROM master_part_number", conn)
            pn_list = df_pn_opts['part_number'].tolist() if not df_pn_opts.empty else ["N/A"]
            
            with st.form("form_add_sn"):
                sel_pn = st.selectbox("Select Part Number", options=pn_list)
                c1, c2 = st.columns(2)
                sn_input = c1.text_input("Serial Number (S/N)")
                loc_input = c1.selectbox("Initial Location", ["HO Store", "Field", "Transit"])
                stat_input = c1.selectbox("Condition", ["S", "U", "AR", "SCRAP"])
                tsn_input = c1.number_input("TSN", value=0.0)
                csn_input = c2.number_input("CSN", value=0)
                dsn_input = c2.number_input("Date Since New", value=0)
                tso_input = c2.number_input("TSO", value=0.0)
                cso_input = c2.number_input("CSO", value=0)
                dso_input = c2.number_input("Date Since Overhaul", value=0)
                
                if st.form_submit_button("Register S/N"):
                    curr = conn.cursor()
                    curr.execute("""INSERT INTO master_serial_number 
                                   (part_number, serial_number, current_location, status, tsn, csn, dsn, tso, cso, dso) 
                                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                                 (sel_pn, sn_input, loc_input, stat_input, tsn_input, csn_input, dsn_input, tso_input, cso_input, dso_input))
                    conn.commit()
                    st.rerun()

            st.divider()
            
            df_sn_list = pd.read_sql("SELECT * FROM master_serial_number ORDER BY id DESC", conn)
            
            if not df_sn_list.empty:
                st.write("#### 🆔 Registered Serial Number List")
                
                st.markdown("""
                <style>
                .sn-table { width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 15px; }
                .sn-table th { background-color: #1f4e79; color: white; padding: 6px; border: 1px solid #ddd; }
                .sn-table td { padding: 4px; border: 1px solid #ddd; text-align: center; vertical-align: middle; }
                .sn-table tr:nth-child(even) { background-color: #f9f9f9; }
                </style>
                """, unsafe_allow_html=True)

                full_html = """<table class="sn-table">
                                <thead>
                                    <tr>
                                        <th>ID</th><th>P/N</th><th>S/N</th><th>Location</th><th>Stat</th>
                                        <th>TSN</th><th>CSN</th><th>DSN</th><th>TSO</th><th>CSO</th><th>DSO</th>
                                    </tr>
                                </thead>
                                <tbody>"""

                for _, row in df_sn_list.iterrows():
                    pn = str(row.get('part_number', '-'))
                    sn = str(row.get('serial_number', '-'))
                    loc = str(row.get('current_location', '-'))
                    stat = str(row.get('status', '-'))
                    
                    row_html = "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                        row['id'], pn, sn, loc, stat, row['tsn'], row['csn'], row['dsn'], row['tso'], row['cso'], row['dso']
                    )
                    full_html += row_html

                full_html += "</tbody></table>"
                st.markdown(full_html, unsafe_allow_html=True)
                st.info("💡 Untuk mengedit atau menghapus data, gunakan panel kontrol di bawah ini.")
                
                st.write("#### 🛠️ Action Controls")
                col_id, col_ed, col_dl = st.columns([2, 1, 1])
                
                id_options = df_sn_list['id'].tolist()
                selected_id_action = col_id.selectbox("Pilih ID Komponen untuk Aksi:", options=id_options, key="sn_action_select")
                
                matching_rows = df_sn_list[df_sn_list['id'] == selected_id_action]
                
                if not matching_rows.empty:
                    selected_row = matching_rows.iloc[0]
                    
                    if col_ed.button("📝 Edit Selected ID", use_container_width=True):
                        st.session_state.update({
                            'edit_mode': True, 'edit_id': selected_row['id'], 'edit_pn': selected_row['part_number'], 
                            'edit_sn': selected_row['serial_number'], 'edit_loc': selected_row['current_location'], 'edit_stat': selected_row['status'],
                            'edit_tsn': selected_row['tsn'], 'edit_csn': selected_row['csn'], 'edit_dsn': selected_row['dsn'], 
                            'edit_tso': selected_row['tso'], 'edit_cso': selected_row['cso'], 'edit_dso': selected_row['dso']
                        })
                        st.rerun()
                        
                    if col_dl.button("🗑️ Delete Selected ID", use_container_width=True):
                        try:
                            curr = conn.cursor()
                            curr.execute("DELETE FROM master_serial_number WHERE id = ?", (selected_id_action,))
                            conn.commit()
                            st.success(f"ID {selected_id_action} berhasil dihapus!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Gagal menghapus: {err}")
                else:
                    st.warning("Silakan pilih ID Komponen terlebih dahulu.")

            # --- FORM EDIT MASTER S/N (SUDAH DIPERBAIKI TOTAL DAN DITUTUP) ---
            if st.session_state.get('edit_mode'):
                with st.expander("🛠️ EDIT DATA SERIAL NUMBER", expanded=True):
                    with st.form("form_edit_sn"):
                        st.write(f"Editing ID: {st.session_state['edit_id']}")
                        new_pn = st.text_input("Part Number", value=st.session_state['edit_pn'])
                        new_sn = st.text_input("Serial Number", value=st.session_state['edit_sn'])
                        new_loc = st.text_input("Location", value=st.session_state['edit_loc'])
                        
                        stat_opts = ["S", "US", "AR", "SCRAP"]
                        current_stat = st.session_state['edit_stat']
                        stat_idx = stat_opts.index(current_stat) if current_stat in stat_opts else 0
                        new_stat = st.selectbox("Status", stat_opts, index=stat_idx)
                        
                        new_tsn = st.number_input("TSN", value=float(st.session_state['edit_tsn']))
                        new_csn = st.number_input("CSN", value=int(st.session_state['edit_csn']))
                        new_dsn = st.number_input("DSN", value=int(st.session_state['edit_dsn']))
                        new_tso = st.number_input("TSO", value=float(st.session_state['edit_tso']))
                        new_cso = st.number_input("CSO", value=int(st.session_state['edit_cso']))
                        new_dso = st.number_input("DSO", value=int(st.session_state['edit_dso']))

                        c_save, c_cancel = st.columns(2)
                        if c_save.form_submit_button("✅ Save Changes"):
                            try:
                                curr = conn.cursor()
                                curr.execute("""UPDATE master_serial_number SET 
                                               part_number=?, serial_number=?, current_location=?, status=?, 
                                               tsn=?, csn=?, dsn=?, tso=?, cso=?, dso=? WHERE id=?""",
                                             (new_pn, new_sn, new_loc, new_stat, new_tsn, new_csn, new_dsn, new_tso, new_cso, new_dso, st.session_state['edit_id']))
                                conn.commit()
                                st.session_state['edit_mode'] = False
                                st.success("Data komponen berhasil diperbarui!")
                                st.rerun()
                            except Exception as err:
                                st.error(f"Gagal memperbarui database: {err}")
                    
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
                pn_list = pd.read_sql("SELECT part_number FROM master_part_number", conn)['part_number'].tolist() if conn else []
                if conn: conn.close()
                
                sel_pn_in = c2.selectbox("Part Number", options=pn_list if pn_list else ["N/A"])
                sn_in = c2.text_input("Serial Number Incoming")
                loc_in = st.selectbox("Storage Destination", ["HO Store", "CGK Store"])
                
                if st.form_submit_button("Confirm Receipt"):
                    conn = create_connection()
                    if conn:
                        curr = conn.cursor()
                        curr.execute("UPDATE master_serial_number SET current_location=?, status='S' WHERE serial_number=?", (loc_in, sn_in))
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
                sn_avail = []
                if conn:
                    df_avail = pd.read_sql("SELECT serial_number FROM master_serial_number WHERE current_location LIKE '%Store%'", conn)
                    sn_avail = df_avail['serial_number'].tolist() if not df_avail.empty else ["No Stock"]
                    conn.close()
                
                sel_sn_out = c2.selectbox("Select S/N to Issue", options=sn_avail if sn_avail else ["No Stock"])
                ac_reg = c2.text_input("Install on Aircraft (Registration)")
                
                if st.form_submit_button("Confirm Issue"):
                    if sel_sn_out != "No Stock":
                        conn = create_connection()
                        if conn:
                            curr = conn.cursor()
                            curr.execute("UPDATE master_serial_number SET current_location='Aircraft', status='S' WHERE serial_number=?", (sel_sn_out,))
                            curr.execute("INSERT INTO inventory_transaction (date, doc_number, serial_number, store_location, status, remark) VALUES (?,?,?,?,?,?)",
                                         (str(dt_out), doc_out, sel_sn_out, ac_reg, 'OUT', f"Installed on {ac_reg}"))
                            conn.commit()
                            st.success(f"S/N {sel_sn_out} issued to {ac_reg}")
                            conn.close()

        with tab_hist:
            conn = create_connection()
            if conn:
                df_hist = pd.read_sql("SELECT * FROM inventory_transaction ORDER BY id DESC", conn)
                st.dataframe(df_hist, use_container_width=True)
                conn.close()