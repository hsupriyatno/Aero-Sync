import streamlit as st
from database import create_connection
import pandas as pd
import streamlit as st
from datetime import date, timedelta, datetime # Tambahkan datetime untuk jaga-jaga

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
    # --- LOGIKA PEMISAH HALAMAN ---
    if page_name == "Update Maintenance Tasks":
        show_update_maintenance_tasks() # Panggil fungsi planning
        return # STOP di sini, jangan lanjut ke kode AML di bawah
    
    # --- KODE DI BAWAH INI HANYA JALAN JIKA BUKAN PLANNING ---
    st.subheader("📝 Aircraft Maintenance Log (AML) Entry")
    st.subheader("1. Aircraft Utilization (Parent)")
    conn = create_connection()

    ac_list = pd.read_sql("SELECT ac_reg FROM catalog", conn)['ac_reg'].tolist()
    conn.close()
    
    col1, col2, col3, col4 = st.columns(4)
    aml_no = col1.text_input("AML No", key="main_aml_no") # Variabel aml_no didefinisikan di sini
    selected_ac = col2.selectbox("A/C Reg", ac_list)
    ac_type = col3.text_input("A/C Type") 
    date_entry = col4.date_input("Date")

    col_e, col_f, col_g, col_h = st.columns(4)
    with col_e: departure = st.text_input("Departure")
    with col_f: arrival = st.text_input("Arrival")
    with col_g: input_fh = st.number_input("Flight Hours", min_value=0.0, step=0.1, format="%.2f")
    with col_h: input_ld = st.number_input("Landings", min_value=0, step=1)

    base_fh, base_ld, base_e1h, base_e1c, base_e2h, base_e2c = get_current_totals(selected_ac)

    current_total_af_h = base_fh + input_fh
    current_total_af_l = base_ld + input_ld
    current_total_e1_h = base_e1h + input_fh
    current_total_e1_c = base_e1c + input_ld
    current_total_e2_h = base_e2h + input_fh
    current_total_e2_c = base_e2c + input_ld

    st.write("---")
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
                pos = c1.selectbox(f"Pos {j}", ["", "E1", "E2", "AF", "AV"], key=f"pos_{j}")
                p_desc = c2.text_input(f"Part Desc {j}", key=f"p_desc_{j}")
                grn = c3.text_input(f"GRN No {j}", key=f"grn_{j}")
                col_rem, col_ins = st.columns(2)
                rem_pn, rem_sn = col_rem.text_input(f"Off P/N {j}", key=f"rem_pn_{j}"), col_rem.text_input(f"Off S/N {j}", key=f"rem_sn_{j}")
                ins_pn, ins_sn = col_ins.text_input(f"On P/N {j}", key=f"ins_pn_{j}"), col_ins.text_input(f"On S/N {j}", key=f"ins_sn_{j}")
                comp_replacements.append({"pos": pos, "p_desc": p_desc, "rem_pn": rem_pn, "rem_sn": rem_sn, "ins_pn": ins_pn, "ins_sn": ins_sn, "grn": grn})

    if st.button("💾 Submit AML Entry", use_container_width=True, type="primary"):
        if aml_no:
            try:
                conn = create_connection()
                curr = conn.cursor()

                curr.execute("INSERT INTO aml_utilization (aml_no, ac_type, ac_reg, date, departure, arrival, flight_hours, landings) VALUES (?,?,?,?,?,?,?,?)", 
                             (aml_no, ac_type, selected_ac, str(date_entry), departure, arrival, input_fh, input_ld))
                
                curr.execute("INSERT INTO aml_engine_param (aml_no, press_alt, oat, ias, tq1, np1, t51, ng1, ff1, ot1, op1, oa1, tq2, np2, t52, ng2, ff2, ot2, op2, oa2) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", 
                             (aml_no, press_alt, oat, ias, tq1, np1, t51, ng1, ff1, ot1, op1, oa1, tq2, np2, t52, ng2, ff2, ot2, op2, oa2))

                for report in pilot_reports:
                    # Pastikan hanya simpan jika ada deskripsi defect
                    if report['desc']: 
                        # Pastikan nama kolom di SQL sesuai dengan database (defect_id)
                        curr.execute("""
                            INSERT INTO aml_pilot_report (aml_no, defect_id, defect_desc, rectification, lame, status)
                            VALUES (?, ?, ?, ?, ?, 'OPEN')
                        """, (aml_no, report['id'], report['desc'], report['rect'], report['lame']))

                        # 3. JIKA DEFERRED, SIMPAN KE TABEL DEFERRED_DEFECTS
                        if report['deferred']:
                            curr.execute("""
                                INSERT INTO deferred_defects (aml_no, ac_reg, defect_no, description, rectification, category, due_date)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (aml_no, selected_ac, report['dd_no'], report['desc'], report['rect'], report['cat'], str(report['due'])))

                        for comp in comp_replacements:
                            if comp['pos']:
                                curr.execute("INSERT INTO aml_component_replacement (aml_no, pos, part_desc, rem_pn, rem_sn, ins_pn, ins_sn, grn) VALUES (?,?,?,?,?,?,?,?)", 
                                            (aml_no, comp['pos'], comp['p_desc'], comp['rem_pn'], comp['rem_sn'], comp['ins_pn'], comp['ins_sn'], comp['grn']))
                
                conn.commit()
                st.success("✅ Success! Data & Deferred Defects Saved.")
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Error: {e}")
            finally:
                conn.close()

    # --- LIST RECORDS ---
    st.divider()
    st.subheader("📋 Registered AML Records")
    conn = create_connection()
    try:
        df_aml = pd.read_sql("SELECT aml_no, ac_reg, date, flight_hours, landings FROM aml_utilization ORDER BY date DESC", conn)
        if not df_aml.empty:
            for _, row in df_aml.iterrows():
                with st.expander(f"AML: {row['aml_no']} | {row['ac_reg']} | {row['date']}"):
                    c_inf, c_del = st.columns([4, 1])
                    c_inf.write(f"Hours: {row['flight_hours']} | Ldgs: {row['landings']}")
                    if c_del.button("🗑️ Delete", key=f"del_{row['aml_no']}"):
                        curr = conn.cursor()
                        curr.execute("DELETE FROM aml_utilization WHERE aml_no = ?", (row['aml_no'],))
                        conn.commit()
                        st.rerun()
    finally:
        conn.close()

def show_update_maintenance_tasks():
    st.header("🛠️ Update Maintenance Tasks")
    conn = create_connection()

    try:
        df_catalog = pd.read_sql("SELECT task_id, task_title, task_description FROM maintenance_catalog", conn)
        df_ac = pd.read_sql("SELECT ac_reg FROM catalog", conn)
        
        if df_catalog.empty:
            st.warning("Maintenance Catalog kosong!")
            return
    
        with st.form("form_update_task"):
            col1, col2 = st.columns(2)
            with col1:
                registration = st.selectbox("Select Aircraft", df_ac['ac_reg'])
                selected_task_id = st.selectbox("Task ID", df_catalog['task_id'].unique())
                
                mask = df_catalog['task_id'] == selected_task_id
                task_info = df_catalog[mask].iloc[0] if any(mask) else None
                task_desc = task_info['task_description'] if task_info is not None else ""
                
                st.text_input("Task Title", value=task_info['task_title'] if task_info is not None else "", disabled=True)

            with col2:
                ld_h = st.number_input("Last Done Hours", min_value=0.0)
                ld_d = st.date_input("Last Done Date", date.today())
                int_h = st.number_input("Interval Hours", min_value=0.0)
                int_cal = st.number_input("Interval Days", min_value=0)

                due_h = ld_h + int_h
                due_d = ld_d + timedelta(days=int_cal)

                st.write(f"**Calculated Due:** {due_h:.2f} Hours | {due_d.strftime('%Y-%m-%d')}")
                
                if st.form_submit_button("💾 Save to Schedule"):
                    # --- LOGIKA PENYIMPANAN KE DATABASE ---
                    try:
                        curr = conn.cursor()
                        # Gunakan INSERT OR REPLACE agar jika Task ID & AC Reg sama, dia mengupdate yang lama
                        query_save = """
                            INSERT OR REPLACE INTO maintenance_schedule 
                            (ac_reg, task_id, task_description, last_done_hours, last_done_date, next_due_hours, next_due_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """
                        curr.execute(query_save, (
                            registration, 
                            selected_task_id, 
                            task_desc, 
                            ld_h, 
                            str(ld_d), 
                            due_h, 
                            str(due_d)
                        ))
                        conn.commit()
                        st.success("✅ Jadwal Berhasil Diperbarui!")
                        st.rerun() # Supaya tabel di bawah langsung update
                    except Exception as e:
                        st.error(f"Gagal menyimpan ke database: {e}")

    finally:
        conn.close()

        # --- BAGIAN TABEL DATA (Di luar form) ---
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