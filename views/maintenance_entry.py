
import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
from database import (
    create_connection,
    get_tasks_by_ac_type,
    save_maintenance_package,    # Pastikan nama ini sama dengan di database.py
    get_all_maintenance_packages,
    delete_maintenance_package
)
def get_current_totals(ac_reg):
    conn = create_connection()
    try:
        query_init = f"SELECT tsn, csn, tsn_e1, csn_e1, tsn_e2, csn_e2 FROM catalog WHERE ac_reg = '{ac_reg}'"
        df_init = pd.read_sql(query_init, conn)
        query_accum = f"SELECT SUM(flight_hours) as total_fh, SUM(landings) as total_ld FROM aml_utilization WHERE ac_reg = '{ac_reg}'"
        df_accum = pd.read_sql(query_accum, conn)
        if not df_init.empty:
            tsn = df_init['tsn'].iloc[0] or 0.0
            csn = df_init['csn'].iloc[0] or 0
            tsn_e1 = df_init['tsn_e1'].iloc[0] or 0.0
            csn_e1 = df_init['csn_e1'].iloc[0] or 0
            tsn_e2 = df_init['tsn_e2'].iloc[0] or 0.0
            csn_e2 = df_init['csn_e2'].iloc[0] or 0
            
            accum_fh = df_accum['total_fh'].iloc[0] or 0.0
            accum_ld = df_accum['total_ld'].iloc[0] or 0
            base_fh = tsn + accum_fh
            base_ld = csn + accum_ld
            base_e1h = tsn_e1 + accum_fh
            base_e1c = csn_e1 + accum_ld
            base_e2h = tsn_e2 + accum_fh
            base_e2c = csn_e2 + accum_ld
            return base_fh, base_ld, base_e1h, base_e1c, base_e2h, base_e2c
        return 0.0, 0, 0.0, 0, 0.0, 0
    finally:
        conn.close()
def show(page_name):
    if page_name == "Update Maintenance Tasks":
        show_update_maintenance_tasks()
        return
    elif page_name == "Maintenance Package / Work Pack":
        show_maintenance_package()
        return
    elif page_name == "AML Entry":
        st.subheader("📝 Aircraft Maintenance Log (AML) Entry")
        st.subheader("1. Aircraft Utilization (Parent)")
        conn = create_connection()
        try:
            ac_list = pd.read_sql("SELECT ac_reg FROM catalog", conn)['ac_reg'].tolist()
        finally:
            conn.close()
        # Input Data Utama
        col1, col2, col3, col4 = st.columns(4)
        aml_no = col1.text_input("AML No", key="main_aml_no")
        selected_ac = col2.selectbox("A/C Reg", ac_list)
        ac_type = col3.text_input("A/C Type") 
        date_entry = col4.date_input("Date")
        col_e, col_f, col_g, col_h = st.columns(4)
        departure = col_e.text_input("Departure")
        arrival = col_f.text_input("Arrival")
        input_fh = col_g.number_input("Flight Hours", min_value=0.0, step=0.1, format="%.2f")
        input_ld = col_h.number_input("Landings", min_value=0, step=1)
        # Kalkulasi Totals
        base_fh, base_ld, base_e1h, base_e1c, base_e2h, base_e2c = get_current_totals(selected_ac)
        current_total_af_h = base_fh + input_fh
        current_total_af_l = base_ld + input_ld
        current_total_e1_h = base_e1h + input_fh
        current_total_e1_c = base_e1c + input_ld
        current_total_e2_h = base_e2h + input_fh
        current_total_e2_c = base_e2c + input_ld
        st.info("💡 Auto-Calculated Totals")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.text_input("Total AF Hours", value=f"{current_total_af_h:.2f}", disabled=True)
        c2.text_input("Total AF Landings", value=str(int(current_total_af_l)), disabled=True)
        c3.text_input("Total E1 Hours", value=f"{current_total_e1_h:.2f}", disabled=True)
        c4.text_input("Total E1 Cycles", value=str(int(current_total_e1_c)), disabled=True)
        c5.text_input("Total E2 Hours", value=f"{current_total_e2_h:.2f}", disabled=True)
        c6.text_input("Total E2 Cycles", value=str(int(current_total_e2_c)), disabled=True)
        st.divider()
        st.subheader("2. Detailed Reports (Child)")
        tab1, tab2, tab3 = st.tabs(["🔥 Engine Parameter", "👨‍✈️ Pilot Report", "⚙️ Component Replacement"])
        with tab1:
            colm1, colm2, colm3 = st.columns(3)
            press_alt = colm1.text_input("Pressure Altitude") 
            oat = colm2.text_input("OAT")
            ias = colm3.text_input("IAS")
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                st.markdown("**Engine 1**")
                tq1, np1, t51, ng1, ff1, ot1, op1, oa1 = [st.number_input(f"{n} 1", key=f"{n}1") for n in ["TQ","NP","T5","NG","FF","OT","OP","OA"]]
            with col_e2:
                st.markdown("**Engine 2**")
                tq2, np2, t52, ng2, ff2, ot2, op2, oa2 = [st.number_input(f"{n} 2", key=f"{n}2") for n in ["TQ","NP","T5","NG","FF","OT","OP","OA"]]
                pass
        with tab2:
            st.caption("Input maksimal 3 temuan pilot")
            pilot_reports = []
            for i in range(1, 4):
                # LOGIKA AUTO-NUMBERING
                # Jika aml_no diisi, format jadi [AML]-1. Jika kosong, tetap PENDING-1
                display_id = f"{aml_no}-{i}" if aml_no else f"PENDING-{i}"
                with st.expander(f"Pilot Report #{i} ({display_id})"):
                    col_a, col_b = st.columns([1, 3])
                    # Gunakan value=display_id agar otomatis berubah saat aml_no diketik
                    def_id = col_a.text_input(f"Defect ID {i}", value=display_id, disabled=True, key=f"def_id_val_{i}")
                    def_desc = col_b.text_input(f"Description {i}", key=f"def_desc_{i}")
                    rect = st.text_area(f"Rectification {i}", key=f"rect_{i}", height=70)
                    lame = st.text_input(f"LAME {i}", key=f"lame_{i}")
                    # --- LOGIKA DEFERRED DEFECT (Input Manual) ---
                    is_deferred = False
                    dd_manual_no = None
                    def_cat, due_date = None, None
                    if def_desc:
                        with st.popover(f"📂 Defer this Defect (#{i})"):
                            st.markdown("### Manual Deferred Entry")
                            # Sesuai permintaan: User isi manual nomor dari buku hard copy
                            dd_manual_no = st.text_input(f"DD Log No (Manual) {i}", key=f"dd_manual_{i}")
                            c1, c2 = st.columns(2)
                            def_cat = c1.selectbox(f"Category {i}", ["A", "B", "C", "D"], key=f"cat_{i}")
                            due_date = c2.date_input(f"Due Date {i}", key=f"due_{i}")
                            if dd_manual_no:
                                is_deferred = True
                    pilot_reports.append({
                        "id": display_id, # ID Otomatis (DHC6-OCG-001-1)
                        "desc": def_desc, 
                        "rect": rect, 
                        "lame": lame,
                        "deferred": is_deferred,
                        "dd_no": dd_manual_no, # ID Manual dari Buku
                        "cat": def_cat,
                        "due": due_date
                    })
        with tab3:
            st.caption("Input maksimal 7 penggantian komponen")
            comp_replacements = []
            for j in range(1, 8):
                with st.expander(f"Component Replacement #{j}"):
                    c1, c2, c3 = st.columns(3)
                    pos = c1.selectbox(f"Pos {j}", ["", "ONLY", "LH", "RH", "Center", "E1", "E2"], key=f"pos_{j}")
                    p_desc = c2.text_input(f"Part Desc {j}", key=f"p_desc_{j}")
                    grn = c3.text_input(f"GRN No {j}", key=f"grn_{j}")
                    col_rem, col_ins = st.columns(2)
                    # Komponen yang dilepas (Off P/N)
                    rem_pn = col_rem.text_input(f"Off P/N {j}", key=f"rem_pn_{j}")
                    rem_sn = col_rem.text_input(f"Off S/N {j}", key=f"rem_sn_{j}")
                    # Komponen yang dipasang (On P/N)
                    ins_pn = col_ins.text_input(f"On P/N {j}", key=f"ins_pn_{j}")
                    ins_sn = col_ins.text_input(f"On S/N {j}", key=f"ins_sn_{j}")
                    comp_replacements.append({
                        "pos": pos, 
                        "p_desc": p_desc, 
                        "rem_pn": rem_pn, 
                        "rem_sn": rem_sn, 
                        "ins_pn": ins_pn, 
                        "ins_sn": ins_sn, 
                        "grn": grn
                    })
# =========================================================================
        # TOMBOL SUBMIT AML ENTRY (SUDAH DIPERBAIKI LOGIKA TRY-EXCEPT-FINALLY & INDENTASI)
        # =========================================================================
        if st.button("💾 Submit AML Entry", use_container_width=True, type="primary"):
            if aml_no:
                try:
                    conn = create_connection()
                    curr = conn.cursor()
                    
                    # --- 1. SIMPAN DATA PARENT (AML Utilization) ---
                    query_aml = """
                        INSERT INTO aml_utilization 
                        (aml_no, ac_type, ac_reg, date, departure, arrival, flight_hours, landings, ac_tsn, ac_csn) 
                        VALUES (?,?,?,?,?,?,?,?,?,?)
                    """
                    curr.execute(query_aml, (
                        aml_no, 
                        ac_type, 
                        selected_ac, 
                        str(date_entry), 
                        departure, 
                        arrival, 
                        float(input_fh), 
                        int(input_ld),
                        float(current_total_af_h), 
                        int(current_total_af_l)
                    ))
                    
                    # Simpan Engine Parameter
                    curr.execute("""
                        INSERT INTO aml_engine_param 
                        (aml_no, press_alt, oat, ias, tq1, np1, t51, ng1, ff1, ot1, op1, oa1, tq2, np2, t52, ng2, ff2, ot2, op2, oa2) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (aml_no, press_alt, oat, ias, tq1, np1, t51, ng1, ff1, ot1, op1, oa1, tq2, np2, t52, ng2, ff2, ot2, op2, oa2))
                    
                    # Simpan Pilot Report
                    for report in pilot_reports:
                        if report['desc']: 
                            curr.execute("""
                                INSERT INTO aml_pilot_report (aml_no, defect_id, defect_desc, rectification, lame, status)
                                VALUES (?, ?, ?, ?, ?, 'OPEN')
                            """, (aml_no, report['id'], report['desc'], report['rect'], report['lame']))

                            if report['deferred']:
                                curr.execute("""
                                    INSERT INTO deferred_defects 
                                    (aml_no, ac_reg, defect_no, description, rectification, category, due_date)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (aml_no, selected_ac, report['dd_no'], report['desc'], report['rect'], report['cat'], str(report['due'])))
                                
                    # --- 2. LOGIKA OTOMATIS COMPONENT REPLACEMENT ---
                    for comp in comp_replacements:
                        if comp['pos'] and comp['ins_pn']:
                            
                            # A. LOGIKA MENCAPOT (PCE-RB1257)
                            if comp['rem_sn'] and comp['rem_pn']:
                                curr.execute("""
                                    UPDATE component_history
                                    SET remove_date = ?, 
                                        remove_af_hours = ?
                                    WHERE ac_reg = ? 
                                    AND part_number = ? 
                                    AND serial_number = ? 
                                    AND remove_date IS NULL
                                """, (str(date_entry), float(current_total_af_h), selected_ac, comp['rem_pn'], comp['rem_sn']))
                                
                                curr.execute("""
                                    DELETE FROM installed_components 
                                    WHERE ac_reg = ? AND part_number = ? AND serial_number = ?
                                """, (selected_ac, comp['rem_pn'], comp['rem_sn']))

                                curr.execute("""
                                    UPDATE master_serial_number
                                    SET status = 'U',
                                        current_location = 'Store',
                                        location = 'HO Store'
                                    WHERE part_number = ? AND serial_number = ?
                                """, (comp['rem_pn'], comp['rem_sn']))

                            # B. LOGIKA MEMASANG (PCE-RB1259)
                            if comp['ins_pn'] and comp['ins_sn']:
                                curr.execute("""
                                    INSERT INTO component_history 
                                    (ac_reg, part_number, serial_number, install_date, install_af_hours, install_af_cycles, reason_removal)
                                    VALUES (?, ?, ?, ?, ?, ?, 'Unscheduled')
                                """, (selected_ac, comp['ins_pn'], comp['ins_sn'], str(date_entry), float(current_total_af_h), int(current_total_af_l)))
                                
                                # FIXED: Menyuplai 13 buah tanda tanya (?) dan parameter agar presisi dengan tabel
                                curr.execute("""
                                    INSERT INTO installed_components 
                                    (ac_reg, component_name, position, part_number, serial_number, parent_sn,
                                     install_date, install_af_hours, install_af_cycles, tsn_at_install, csn_at_install, tso, cso)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    selected_ac, comp['p_desc'], comp['pos'], comp['ins_pn'], comp['ins_sn'], "Airframe",
                                    str(date_entry), float(current_total_af_h), int(current_total_af_l), 0.0, 0.0, 0.0, 0
                                ))

                                curr.execute("""
                                    UPDATE master_serial_number
                                    SET status = 'S',
                                        current_location = 'Aircraft',
                                        location = ?
                                    WHERE part_number = ? AND serial_number = ?
                                """, (selected_ac, comp['ins_pn'], comp['ins_sn']))

                    # Commit transaksi jika semua sukses tanpa error
                    conn.commit()
                    st.success(f"✔️ AML No. {aml_no} Berhasil Disimpan ke database!")
                    st.rerun()

                except Exception as aml_err:
                    conn.rollback()
                    st.error(f"❌ Gagal menyimpan AML: {aml_err}")
                finally:
                    conn.close()
            else:
                st.warning("⚠️ Harap isi nomor AML No terlebih dahulu sebelum submit!")

        # --- LIST RECORDS (DILUAR BLOK SUBMIT - BERDIRI SENDIRI DENGAN INDENTASI LEVEL HALAMAN) ---
        st.divider()
        st.subheader("📋 Registered AML Records")
        
        conn = create_connection()
        try:
            try:
                df_regs = pd.read_sql("SELECT DISTINCT ac_reg FROM aml_utilization WHERE ac_reg IS NOT NULL AND ac_reg != '' ORDER BY ac_reg", conn)
                list_registrasi = ["All Aircraft"] + df_regs['ac_reg'].tolist()
            except Exception:
                list_registrasi = ["All Aircraft"]
            
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                filter_ac = st.selectbox("✈️ Filter Registrasi Pesawat:", options=list_registrasi, index=0)
            with col_filter2:
                search_aml = st.text_input("🔍 Cari Nomor AML:", value="", placeholder="Ketik nomor AML...")
            
            query = "SELECT aml_no, ac_reg, date, flight_hours, landings FROM aml_utilization WHERE 1=1"
            params = []
            
            if filter_ac != "All Aircraft":
                query += " AND ac_reg = ?"
                params.append(filter_ac)
            if search_aml.strip() != "":
                query += " AND aml_no LIKE ?"
                params.append(f"%{search_aml.strip()}%")
                
            query += " ORDER BY date DESC"
            df_aml = pd.read_sql(query, conn, params=params)
            
            if not df_aml.empty:
                st.caption(f"Menampilkan {len(df_aml)} record yang cocok.")
                with st.container(height=450, border=True):
                    for idx, row in enumerate(df_aml.iterrows()):
                        actual_row = row[1] 
                        with st.expander(f"AML: {actual_row['aml_no']} | {actual_row['ac_reg']} | {actual_row['date']}"):
                            c_inf, c_del = st.columns([4, 1])
                            c_inf.write(f"Hours: {actual_row['flight_hours']} | Ldgs: {actual_row['landings']}")
                            
                            if c_del.button("🗑️ Delete", key=f"del_{actual_row['aml_no']}_{idx}"):
                                curr = conn.cursor()
                                try:
                                    curr.execute("DELETE FROM aml_engine_param WHERE aml_no = ?", (actual_row['aml_no'],))
                                    curr.execute("DELETE FROM aml_pilot_report WHERE aml_no = ?", (actual_row['aml_no'],))
                                    curr.execute("DELETE FROM aml_component_replacement WHERE aml_no = ?", (actual_row['aml_no'],))
                                    curr.execute("DELETE FROM deferred_defects WHERE aml_no = ?", (actual_row['aml_no'],))
                                    curr.execute("DELETE FROM aml_utilization WHERE aml_no = ?", (actual_row['aml_no'],))
                                    conn.commit()
                                    st.success(f"Record {actual_row['aml_no']} Bersih Total!")
                                    st.rerun()
                                except Exception as e:
                                    conn.rollback()
                                    st.error(f"Gagal hapus total: {e}")
            else:
                st.warning("❌ Tidak ada data AML yang cocok.")
                
        except Exception as main_err:
            st.error(f"Error pada sistem pembacaan data: {main_err}")
        finally:
            conn.close()
    elif page_name == "AD Compliance Entry":
        st.subheader("🔍 Airworthiness Directive (AD) Compliance Entry")
        conn = create_connection()
        # 1. Pastikan query mengambil 'ac_type' sesuai perubahan terakhir Bapak
        df_ad = pd.read_sql_query("SELECT ad_number, ac_type FROM ad_catalog WHERE status = 'Active'", conn)
        if not df_ad.empty:
            # Pindahkan Form ke sini agar rapi
            with st.form("form_compliance"):
                selected_ad = st.selectbox("Select AD Number", df_ad['ad_number'].tolist())
                # 2. Perbaikan KeyError: Gunakan 'ac_type' bukan 'ac_reg'
                # Kita cari ac_type dari baris yang dipilih
                mask = df_ad['ad_number'] == selected_ad
                a_type = df_ad[mask]['ac_type'].values[0]
                st.info(f"Target Aircraft Type: {a_type}")
                # 3. Pilih Registrasi Pesawat yang sesuai dengan Tipe tersebut
                df_fleet = pd.read_sql_query("SELECT ac_reg FROM catalog WHERE ac_type = ?", conn, params=(a_type,))
                list_reg = df_fleet['ac_reg'].tolist() if not df_fleet.empty else []
                selected_reg = st.selectbox("Select Aircraft Registration", list_reg)
                col1, col2 = st.columns(2)
                date_done = col1.date_input("Date Performed")
                fh_done = col2.number_input("Compliance FH", min_value=0.0, step=0.1)
                remarks = st.text_input("Maintenance Release / Form Number", placeholder="e.g., CRS-2026-001")
                # 4. WAJIB: Tambahkan tombol Submit di dalam blok 'with st.form'
                submitted = st.form_submit_button("Update Compliance")
                if submitted:
                    if selected_reg:
                        curr = conn.cursor()
                        # Simpan data ke tabel ad_compliance
                        curr.execute("""
                            INSERT INTO ad_compliance (ad_number, ac_type, ac_reg, date_done, fh_done, remarks) 
                            VALUES (?,?,?,?,?,?)
                        """, (selected_ad, a_type, selected_reg, str(date_done), fh_done, remarks))
                        conn.commit()
                        st.success(f"✅ Success! Compliance record for {selected_reg} updated.")
                        st.rerun()
                    else:
                        st.error("Gagal! Pilih Aircraft Registration terlebih dahulu.")
        else:
            st.warning("Belum ada AD di Catalog. Silakan isi di menu Catalog terlebih dahulu.")
        conn.close()
    elif page_name == "SB Compliance Entry":
        st.subheader("🔍 Service Bulletin (SB) Compliance Entry")
        conn = create_connection()
        # 1. Pastikan query mengambil 'ac_type' sesuai perubahan terakhir Bapak
        df_sb = pd.read_sql_query("SELECT sb_number, ac_type FROM sb_catalog WHERE status = 'Active'", conn)
        if not df_sb.empty:
            # Pindahkan Form ke sini agar rapi
            with st.form("form_compliance"):
                selected_sb = st.selectbox("Select SB Number", df_sb['sb_number'].tolist())
                # 2. Perbaikan KeyError: Gunakan 'ac_type' bukan 'ac_reg'
                # Kita cari ac_type dari baris yang dipilih
                mask = df_sb['sb_number'] == selected_sb
                a_type = df_sb[mask]['ac_type'].values[0]
                st.info(f"Target Aircraft Type: {a_type}")
                # 3. Pilih Registrasi Pesawat yang sesuai dengan Tipe tersebut
                df_fleet = pd.read_sql_query("SELECT ac_reg FROM catalog WHERE ac_type = ?", conn, params=(a_type,))
                list_reg = df_fleet['ac_reg'].tolist() if not df_fleet.empty else []
                selected_reg = st.selectbox("Select Aircraft Registration", list_reg)
                col1, col2 = st.columns(2)
                date_done = col1.date_input("Date Performed")
                fh_done = col2.number_input("Compliance FH", min_value=0.0, step=0.1)
                remarks = st.text_input("Maintenance Release / Form Number", placeholder="e.g., CRS-2026-001")
                # 4. WAJIB: Tambahkan tombol Submit di dalam blok 'with st.form'
                submitted = st.form_submit_button("Update Compliance")
                if submitted:
                    if selected_reg:
                        curr = conn.cursor()
                        # Simpan data ke tabel sb_compliance
                        curr.execute("""
                            INSERT INTO sb_compliance (sb_number, ac_type, ac_reg, date_done, fh_done, remarks) 
                            VALUES (?,?,?,?,?,?)
                        """, (selected_sb, a_type, selected_reg, str(date_done), fh_done, remarks))
                        conn.commit()
                        st.success(f"✅ Success! Compliance record for {selected_reg} updated.")
                        st.rerun()
                    else:
                        st.error("Gagal! Pilih Aircraft Registration terlebih dahulu.")
        else:
            st.warning("Belum ada SB di Catalog. Silakan isi di menu Catalog terlebih dahulu.")
        conn.close()
def show_update_maintenance_tasks():
    st.header("🛠️ Update Maintenance Tasks")
    conn = create_connection()
    try:
        # 1. Ambil data katalog (Pastikan kolom task_description ada)
        df_catalog = pd.read_sql("SELECT task_id, task_title, task_description, duration_days FROM maintenance_catalog", conn)
        df_ac = pd.read_sql("SELECT ac_reg FROM catalog", conn)
        if df_catalog.empty:
            st.warning("Maintenance Catalog kosong!")
            return
        with st.form("form_update_task"):
            col1, col2 = st.columns(2)
            with col1:
                registration = st.selectbox("Select Aircraft", df_ac['ac_reg'])
                selected_task_id = st.selectbox("Task ID", df_catalog['task_id'].unique())
                # --- LOGIKA OTOMATIS: Ambil Title & Desc dari Catalog berdasarkan Task ID ---
                mask = df_catalog['task_id'] == selected_task_id
                task_info = df_catalog[mask].iloc[0] if any(mask) else None
                # Kita definisikan variabel penampung agar bisa dipakai di bagian simpan
                current_title = task_info['task_title'] if task_info is not None else ""
                current_desc = task_info['task_description'] if task_info is not None else ""
                current_duration = task_info['duration_days'] if task_info is not None else 0
                # Tampilkan ke layar (Data ini otomatis berubah saat Task ID diganti)
                st.text_input("Task Title", value=current_title, disabled=True)
                st.text_area("Task Description", value=current_desc, disabled=True, height=100)
            with col2:
                ld_h = st.number_input("Last Done Hours", min_value=0.0)
                ld_d = st.date_input("Last Done Date", date.today())
                int_h = st.number_input("Interval Hours", min_value=0.0)
                int_cal = st.number_input("Interval Days", min_value=0)
                due_h = ld_h + int_h
                due_d = ld_d + timedelta(days=int_cal)
                st.write(f"**Calculated Due:** {due_h:.2f} Hours | {due_d.strftime('%Y-%m-%d')}")
                if st.form_submit_button("💾 Save to Schedule"):
                    try:
                        curr = conn.cursor()
                        query_save = """
                            INSERT OR REPLACE INTO maintenance_schedule 
                            (ac_reg, task_id, task_description, last_done_hours, last_done_date, next_due_hours, next_due_date, duration_days)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        curr.execute(query_save, (
                            registration, 
                            selected_task_id, 
                            current_desc, 
                            ld_h, 
                            str(ld_d), 
                            due_h, 
                            str(due_d),
                            current_duration  # Masukkan variabel durasi di sini
                        ))
                        conn.commit()
                        st.success("✅ Jadwal Berhasil Diperbarui!")
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Gagal menyimpan ke database: {e}")
    finally:
        conn.close()
    st.divider()
    st.subheader("📋 Current Maintenance Schedule")
    conn = create_connection()
    try:
        # Ambil data dari tabel schedule
        query = "SELECT rowid, ac_reg, task_id, last_done_hours, last_done_date, next_due_hours, next_due_date FROM maintenance_schedule ORDER BY next_due_date ASC"
        df_sched = pd.read_sql(query, conn)
        if not df_sched.empty:
            for _, row in df_sched.iterrows():
                # Kita buat expander untuk tiap baris data agar hemat tempat
                with st.expander(f"📌 {row['ac_reg']} | {row['task_id']} (Due: {row['next_due_date']})"):
                    col_a, col_b, col_c = st.columns([3, 1, 1])
                    with col_a:
                        st.write(f"**Last Done:** {row['last_done_hours']} FH / {row['last_done_date']}")
                        st.write(f"**Next Due:** {row['next_due_hours']} FH / {row['next_due_date']}")
                    # --- FUNGSI EDIT ---
                    if col_b.button("📝 Edit", key=f"edit_{row['rowid']}"):
                        st.info("Gunakan form di atas untuk update data ini (Fitur auto-fill bisa ditambahkan jika perlu)")
                    # --- FUNGSI DELETE ---
                    if col_c.button("🗑️ Delete", key=f"del_task_{row['rowid']}"):
                        curr = conn.cursor()
                        curr.execute("DELETE FROM maintenance_schedule WHERE rowid = ?", (row['rowid'],))
                        conn.commit()
                        st.success(f"Data {row['task_id']} berhasil dihapus!")
                        st.rerun() # Refresh halaman
        else:
            st.info("Belum ada jadwal perawatan yang terdaftar.")
    except Exception as e:
        st.error(f"Gagal memuat tabel: {e}")
    finally:
        conn.close()
def show_maintenance_package():
    st.title("🛠️ Maintenance Package / Work Pack")
    # --- 1. INISIALISASI SESSION STATE (Penting!) ---
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False
        st.session_state.pkg_to_edit = {}
    # --- 2. LOGIKA PENGISIAN FORM ---
    # Jika sedang mode edit, gunakan data lama. Jika tidak, kosongkan.
    default_name = st.session_state.pkg_to_edit.get("name", "")
    default_tasks = st.session_state.pkg_to_edit.get("tasks", [])
    default_ac = st.session_state.pkg_to_edit.get("ac_type", "DHC6-300")
    # Aircraft Type di luar form agar trigger task list
    ac_type = st.selectbox("Select Aircraft Type", ["DHC6-300", "DHC6-400", "Bell-412"], 
                           index=["DHC6-300", "DHC6-400", "Bell-412"].index(default_ac) if st.session_state.edit_mode else 0)
    available_tasks = get_tasks_by_ac_type(ac_type)
    # --- 3. FORM INPUT ---
    with st.form("create_package_form", clear_on_submit=False):
        st.write("### Edit Mode" if st.session_state.edit_mode else "### Create Mode")
        pkg_name = st.text_input("Package Name", value=default_name)
        if not available_tasks.empty:
            # Pastikan default_tasks ada di dalam list available_tasks agar tidak error
            valid_defaults = [t for t in default_tasks if t in available_tasks['task_id'].tolist()]
            selected_tasks = st.multiselect(
                "Select Tasks",
                options=available_tasks['task_id'].tolist(),
                default=valid_defaults,
                format_func=lambda x: f"{x} - {available_tasks.loc[available_tasks['task_id']==x, 'task_title'].values[0]}"
            )
        else:
            st.warning("No tasks found.")
            selected_tasks = []
        # Tombol berubah nama jika sedang edit
        label = "Update Package" if st.session_state.edit_mode else "Save Package"
        submit = st.form_submit_button(label)
        if submit:
            if pkg_name and selected_tasks:
                # Jika edit, hapus yang lama dulu
                if st.session_state.edit_mode:
                    delete_maintenance_package(st.session_state.pkg_to_edit["id"])
                # Simpan data baru
                success = save_maintenance_package(pkg_name, ac_type, selected_tasks)
                if success:
                    st.success("✅ Success!")
                    # Reset Mode Edit
                    st.session_state.edit_mode = False
                    st.session_state.pkg_to_edit = {}
                    st.rerun()
            else:
                st.error("Please fill all fields.")
    # --- 4. MONITORING TABLE & REVISE BUTTON ---
    st.divider()
    df_pkgs = get_all_maintenance_packages()
    if not df_pkgs.empty:
        st.dataframe(df_pkgs, use_container_width=True, hide_index=True)
        with st.expander("🛠️ Manage Packages"):
            col1, col2 = st.columns([2, 1])
            selected_id = col1.selectbox("Select ID to Revise/Delete", df_pkgs['package_id'])
            
            if st.button("📝 Revise Now", use_container_width=True):
                # Ambil data dari baris yang dipilih
                row = df_pkgs[df_pkgs['package_id'] == selected_id].iloc[0]
                # Simpan ke session state
                st.session_state.edit_mode = True
                st.session_state.pkg_to_edit = {
                    "id": selected_id,
                    "name": row['package_name'],
                    "ac_type": row['ac_type'],
                    "tasks": row['tasks'].split(", ") # Pecah string jadi list
                }
                st.rerun() # Pemicu utama agar form di atas terisi data
            if st.button("🗑️ Delete", type="primary", use_container_width=True):
                if delete_maintenance_package(selected_id):
                    st.rerun()


# --- LIST RECORDS (Sudah Di-upgrade: Dual Filter AC Reg & AML No + Scrollbar) ---
        st.divider()
        st.subheader("📋 Registered AML Records")
        conn = create_connection()
        try:
            try:
                df_regs = pd.read_sql("SELECT DISTINCT ac_reg FROM aml_utilization WHERE ac_reg IS NOT NULL AND ac_reg != '' ORDER BY ac_reg", conn)
                list_registrasi = ["All Aircraft"] + df_regs['ac_reg'].tolist()
            except:
                list_registrasi = ["All Aircraft"]
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                filter_ac = st.selectbox("✈️ Filter Registrasi Pesawat:", options=list_registrasi, index=0)
            with col_filter2:
                search_aml = st.text_input("🔍 Cari Nomor AML:", value="", placeholder="Ketik nomor AML (misal: 5480)...")
            query = "SELECT aml_no, ac_reg, date, flight_hours, landings FROM aml_utilization WHERE 1=1"
            params = []
            if filter_ac != "All Aircraft":
                query += " AND ac_reg = ?"
                params.append(filter_ac)
            if search_aml.strip() != "":
                query += " AND aml_no LIKE ?"
                params.append(f"%{search_aml.strip()}%")
            query += " ORDER BY date DESC"
            df_aml = pd.read_sql(query, conn, params=params)
            if not df_aml.empty:
                st.caption(f"Menampilkan {len(df_aml)} record yang cocok.")
                # Kontainer Box Tinggi Tetap agar Ringan
                with st.container(height=450, border=True):
                    for idx, row in enumerate(df_aml.iterrows()):
                        actual_row = row[1] 
                        with st.expander(f"AML: {actual_row['aml_no']} | {actual_row['ac_reg']} | {actual_row['date']}"):
                            c_inf, c_del = st.columns([4, 1])
                            c_inf.write(f"Hours: {actual_row['flight_hours']} | Ldgs: {actual_row['landings']}")
                            if c_del.button("🗑️ Delete", key=f"del_{actual_row['aml_no']}_{idx}"):
                                curr = conn.cursor()
                                try:
                                    curr.execute("DELETE FROM aml_engine_param WHERE aml_no = ?", (actual_row['aml_no'],))
                                    curr.execute("DELETE FROM aml_pilot_report WHERE aml_no = ?", (actual_row['aml_no'],))
                                    curr.execute("DELETE FROM aml_component_replacement WHERE aml_no = ?", (actual_row['aml_no'],))
                                    curr.execute("DELETE FROM deferred_defects WHERE aml_no = ?", (actual_row['aml_no'],))
                                    curr.execute("DELETE FROM aml_utilization WHERE aml_no = ?", (actual_row['aml_no'],))
                                    conn.commit()
                                    st.success(f"Record {actual_row['aml_no']} Bersih Total!")
                                    st.rerun()
                                except Exception as e:
                                    conn.rollback()
                                    st.error(f"Gagal hapus total: {e}")
            else:
                st.warning("❌ Tidak ada data AML yang cocok dengan kombinasi filter Bapak.")
        finally:
            conn.close()
    elif page_name == "AD Compliance Entry":
        st.subheader("🔍 Airworthiness Directive (AD) Compliance Entry")
        conn = create_connection()
        # 1. Pastikan query mengambil 'ac_type' sesuai perubahan terakhir Bapak
        df_ad = pd.read_sql_query("SELECT ad_number, ac_type FROM ad_catalog WHERE status = 'Active'", conn)
        if not df_ad.empty:
            # Pindahkan Form ke sini agar rapi
            with st.form("form_compliance"):
                selected_ad = st.selectbox("Select AD Number", df_ad['ad_number'].tolist())
                # 2. Perbaikan KeyError: Gunakan 'ac_type' bukan 'ac_reg'
                # Kita cari ac_type dari baris yang dipilih
                mask = df_ad['ad_number'] == selected_ad
                a_type = df_ad[mask]['ac_type'].values[0]
                st.info(f"Target Aircraft Type: {a_type}")
                # 3. Pilih Registrasi Pesawat yang sesuai dengan Tipe tersebut
                df_fleet = pd.read_sql_query("SELECT ac_reg FROM catalog WHERE ac_type = ?", conn, params=(a_type,))
                list_reg = df_fleet['ac_reg'].tolist() if not df_fleet.empty else []
                selected_reg = st.selectbox("Select Aircraft Registration", list_reg)
                col1, col2 = st.columns(2)
                date_done = col1.date_input("Date Performed")
                fh_done = col2.number_input("Compliance FH", min_value=0.0, step=0.1)
                remarks = st.text_input("Maintenance Release / Form Number", placeholder="e.g., CRS-2026-001")
                # 4. WAJIB: Tambahkan tombol Submit di dalam blok 'with st.form'
                submitted = st.form_submit_button("Update Compliance")
                if submitted:
                    if selected_reg:
                        curr = conn.cursor()
                        # Simpan data ke tabel ad_compliance
                        curr.execute("""
                            INSERT INTO ad_compliance (ad_number, ac_type, ac_reg, date_done, fh_done, remarks) 
                            VALUES (?,?,?,?,?,?)
                        """, (selected_ad, a_type, selected_reg, str(date_done), fh_done, remarks))
                        conn.commit()
                        st.success(f"✅ Success! Compliance record for {selected_reg} updated.")
                        st.rerun()
                    else:
                        st.error("Gagal! Pilih Aircraft Registration terlebih dahulu.")
        else:
            st.warning("Belum ada AD di Catalog. Silakan isi di menu Catalog terlebih dahulu.")
        conn.close()
    elif page_name == "SB Compliance Entry":
        st.subheader("🔍 Service Bulletin (SB) Compliance Entry")
        conn = create_connection()
        # 1. Pastikan query mengambil 'ac_type' sesuai perubahan terakhir Bapak
        df_sb = pd.read_sql_query("SELECT sb_number, ac_type FROM sb_catalog WHERE status = 'Active'", conn)
        if not df_sb.empty:
            # Pindahkan Form ke sini agar rapi
            with st.form("form_compliance"):
                selected_sb = st.selectbox("Select SB Number", df_sb['sb_number'].tolist())
                # 2. Perbaikan KeyError: Gunakan 'ac_type' bukan 'ac_reg'
                # Kita cari ac_type dari baris yang dipilih
                mask = df_sb['sb_number'] == selected_sb
                a_type = df_sb[mask]['ac_type'].values[0]
                st.info(f"Target Aircraft Type: {a_type}")
                # 3. Pilih Registrasi Pesawat yang sesuai dengan Tipe tersebut
                df_fleet = pd.read_sql_query("SELECT ac_reg FROM catalog WHERE ac_type = ?", conn, params=(a_type,))
                list_reg = df_fleet['ac_reg'].tolist() if not df_fleet.empty else []
                selected_reg = st.selectbox("Select Aircraft Registration", list_reg)
                col1, col2 = st.columns(2)
                date_done = col1.date_input("Date Performed")
                fh_done = col2.number_input("Compliance FH", min_value=0.0, step=0.1)
                remarks = st.text_input("Maintenance Release / Form Number", placeholder="e.g., CRS-2026-001")
                # 4. WAJIB: Tambahkan tombol Submit di dalam blok 'with st.form'
                submitted = st.form_submit_button("Update Compliance")
                if submitted:
                    if selected_reg:
                        curr = conn.cursor()
                        # Simpan data ke tabel sb_compliance
                        curr.execute("""
                            INSERT INTO sb_compliance (sb_number, ac_type, ac_reg, date_done, fh_done, remarks) 
                            VALUES (?,?,?,?,?,?)
                        """, (selected_sb, a_type, selected_reg, str(date_done), fh_done, remarks))
                        conn.commit()
                        st.success(f"✅ Success! Compliance record for {selected_reg} updated.")
                        st.rerun()
                    else:
                        st.error("Gagal! Pilih Aircraft Registration terlebih dahulu.")
        else:
            st.warning("Belum ada SB di Catalog. Silakan isi di menu Catalog terlebih dahulu.")
        conn.close()
def show_update_maintenance_tasks():
    st.header("🛠️ Update Maintenance Tasks")
    conn = create_connection()
    try:
        # 1. Ambil data katalog (Pastikan kolom task_description ada)
        df_catalog = pd.read_sql("SELECT task_id, task_title, task_description, duration_days FROM maintenance_catalog", conn)
        df_ac = pd.read_sql("SELECT ac_reg FROM catalog", conn)
        if df_catalog.empty:
            st.warning("Maintenance Catalog kosong!")
            return
        with st.form("form_update_task"):
            col1, col2 = st.columns(2)
            with col1:
                registration = st.selectbox("Select Aircraft", df_ac['ac_reg'])
                selected_task_id = st.selectbox("Task ID", df_catalog['task_id'].unique())
                # --- LOGIKA OTOMATIS: Ambil Title & Desc dari Catalog berdasarkan Task ID ---
                mask = df_catalog['task_id'] == selected_task_id
                task_info = df_catalog[mask].iloc[0] if any(mask) else None
                # Kita definisikan variabel penampung agar bisa dipakai di bagian simpan
                current_title = task_info['task_title'] if task_info is not None else ""
                current_desc = task_info['task_description'] if task_info is not None else ""
                current_duration = task_info['duration_days'] if task_info is not None else 0
                # Tampilkan ke layar (Data ini otomatis berubah saat Task ID diganti)
                st.text_input("Task Title", value=current_title, disabled=True)
                st.text_area("Task Description", value=current_desc, disabled=True, height=100)
            with col2:
                ld_h = st.number_input("Last Done Hours", min_value=0.0)
                ld_d = st.date_input("Last Done Date", date.today())
                int_h = st.number_input("Interval Hours", min_value=0.0)
                int_cal = st.number_input("Interval Days", min_value=0)
                due_h = ld_h + int_h
                due_d = ld_d + timedelta(days=int_cal)
                st.write(f"**Calculated Due:** {due_h:.2f} Hours | {due_d.strftime('%Y-%m-%d')}")
                if st.form_submit_button("💾 Save to Schedule"):
                    try:
                        curr = conn.cursor()
                        query_save = """
                            INSERT OR REPLACE INTO maintenance_schedule 
                            (ac_reg, task_id, task_description, last_done_hours, last_done_date, next_due_hours, next_due_date, duration_days)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        curr.execute(query_save, (
                            registration, 
                            selected_task_id, 
                            current_desc, 
                            ld_h, 
                            str(ld_d), 
                            due_h, 
                            str(due_d),
                            current_duration  # Masukkan variabel durasi di sini
                        ))
                        conn.commit()
                        st.success("✅ Jadwal Berhasil Diperbarui!")
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Gagal menyimpan ke database: {e}")
    finally:
        conn.close()
    st.divider()
    st.subheader("📋 Current Maintenance Schedule")
    conn = create_connection()
    try:
        # Ambil data dari tabel schedule
        query = "SELECT rowid, ac_reg, task_id, last_done_hours, last_done_date, next_due_hours, next_due_date FROM maintenance_schedule ORDER BY next_due_date ASC"
        df_sched = pd.read_sql(query, conn)
        if not df_sched.empty:
            for _, row in df_sched.iterrows():
                # Kita buat expander untuk tiap baris data agar hemat tempat
                with st.expander(f"📌 {row['ac_reg']} | {row['task_id']} (Due: {row['next_due_date']})"):
                    col_a, col_b, col_c = st.columns([3, 1, 1])
                    with col_a:
                        st.write(f"**Last Done:** {row['last_done_hours']} FH / {row['last_done_date']}")
                        st.write(f"**Next Due:** {row['next_due_hours']} FH / {row['next_due_date']}")
                    # --- FUNGSI EDIT ---
                    if col_b.button("📝 Edit", key=f"edit_{row['rowid']}"):
                        st.info("Gunakan form di atas untuk update data ini (Fitur auto-fill bisa ditambahkan jika perlu)")
                    # --- FUNGSI DELETE ---
                    if col_c.button("🗑️ Delete", key=f"del_task_{row['rowid']}"):
                        curr = conn.cursor()
                        curr.execute("DELETE FROM maintenance_schedule WHERE rowid = ?", (row['rowid'],))
                        conn.commit()
                        st.success(f"Data {row['task_id']} berhasil dihapus!")
                        st.rerun() # Refresh halaman
        else:
            st.info("Belum ada jadwal perawatan yang terdaftar.")
    except Exception as e:
        st.error(f"Gagal memuat tabel: {e}")
    finally:
        conn.close()
def show_maintenance_package():
    st.title("🛠️ Maintenance Package / Work Pack")
    # --- 1. INISIALISASI SESSION STATE (Penting!) ---
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False
        st.session_state.pkg_to_edit = {}
    # --- 2. LOGIKA PENGISIAN FORM ---
    # Jika sedang mode edit, gunakan data lama. Jika tidak, kosongkan.
    default_name = st.session_state.pkg_to_edit.get("name", "")
    default_tasks = st.session_state.pkg_to_edit.get("tasks", [])
    default_ac = st.session_state.pkg_to_edit.get("ac_type", "DHC6-300")
    # Aircraft Type di luar form agar trigger task list
    ac_type = st.selectbox("Select Aircraft Type", ["DHC6-300", "DHC6-400", "Bell-412"], 
                           index=["DHC6-300", "DHC6-400", "Bell-412"].index(default_ac) if st.session_state.edit_mode else 0)
    available_tasks = get_tasks_by_ac_type(ac_type)
    # --- 3. FORM INPUT ---
    with st.form("create_package_form", clear_on_submit=False):
        st.write("### Edit Mode" if st.session_state.edit_mode else "### Create Mode")
        pkg_name = st.text_input("Package Name", value=default_name)
        if not available_tasks.empty:
            # Pastikan default_tasks ada di dalam list available_tasks agar tidak error
            valid_defaults = [t for t in default_tasks if t in available_tasks['task_id'].tolist()]
            
            selected_tasks = st.multiselect(
                "Select Tasks",
                options=available_tasks['task_id'].tolist(),
                default=valid_defaults,
                format_func=lambda x: f"{x} - {available_tasks.loc[available_tasks['task_id']==x, 'task_title'].values[0]}"
            )
        else:
            st.warning("No tasks found.")
            selected_tasks = []
        # Tombol berubah nama jika sedang edit
        label = "Update Package" if st.session_state.edit_mode else "Save Package"
        submit = st.form_submit_button(label)
        if submit:
            if pkg_name and selected_tasks:
                # Jika edit, hapus yang lama dulu
                if st.session_state.edit_mode:
                    delete_maintenance_package(st.session_state.pkg_to_edit["id"])
                # Simpan data baru
                success = save_maintenance_package(pkg_name, ac_type, selected_tasks)
                if success:
                    st.success("✅ Success!")
                    # Reset Mode Edit
                    st.session_state.edit_mode = False
                    st.session_state.pkg_to_edit = {}
                    st.rerun()
            else:
                st.error("Please fill all fields.")
    # --- 4. MONITORING TABLE & REVISE BUTTON ---
    st.divider()
    df_pkgs = get_all_maintenance_packages()
    if not df_pkgs.empty:
        st.dataframe(df_pkgs, use_container_width=True, hide_index=True)
        
        with st.expander("🛠️ Manage Packages"):
            col1, col2 = st.columns([2, 1])
            selected_id = col1.selectbox("Select ID to Revise/Delete", df_pkgs['package_id'])
            
            if st.button("📝 Revise Now", use_container_width=True):
                # Ambil data dari baris yang dipilih
                row = df_pkgs[df_pkgs['package_id'] == selected_id].iloc[0]
                
                # Simpan ke session state
                st.session_state.edit_mode = True
                st.session_state.pkg_to_edit = {
                    "id": selected_id,
                    "name": row['package_name'],
                    "ac_type": row['ac_type'],
                    "tasks": row['tasks'].split(", ") # Pecah string jadi list
                }
                st.rerun() # Pemicu utama agar form di atas terisi data

            if st.button("🗑️ Delete", type="primary", use_container_width=True):
                if delete_maintenance_package(selected_id):
                    st.rerun()