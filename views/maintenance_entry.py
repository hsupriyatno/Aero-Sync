import streamlit as st
from database import create_connection
import pandas as pd

def get_current_totals(ac_reg):
    conn = create_connection()
    try:
        query_init = f"SELECT tsn, csn, tsn_e1, csn_e1, tsn_e2, csn_e2 FROM catalog WHERE ac_reg = '{ac_reg}'"
        df_init = pd.read_sql(query_init, conn)
        
        query_accum = f"SELECT SUM(flight_hours) as total_fh, SUM(landings) as total_ld FROM aml_utilization WHERE ac_reg = '{ac_reg}'"
        df_accum = pd.read_sql(query_accum, conn)
        
        if not df_init.empty:
            # Pastikan jika NULL di database, dianggap 0.0 atau 0
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
    st.subheader("📝 Aircraft Maintenance Log (AML) Entry")
    
    # --- 1. AMBIL DAFTAR PESAWAT DARI DATABASE ---
    conn = create_connection()
    ac_list = pd.read_sql("SELECT ac_reg FROM catalog", conn)['ac_reg'].tolist()
    conn.close()
    
    # --- 2. INPUT FIELD (BARIS ATAS) ---
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        aml_no = st.text_input("AML No")
    with col_b:
        selected_ac = st.selectbox("A/C Reg", ac_list) # Variabel selected_ac dibuat di sini
    with col_c:
        ac_type = st.text_input("A/C Type") 
    with col_d:
        date_entry = st.date_input("Date")

    # --- 3. INPUT FIELD (BARIS KEDUA) ---
    col_e, col_f, col_g, col_h = st.columns(4)
    with col_e:
        departure = st.text_input("Departure")
    with col_f:
        arrival = st.text_input("Arrival")
    with col_g:
        input_fh = st.number_input("Flight Hours", min_value=0.0, step=0.1, format="%.2f")
    with col_h:
        input_ld = st.number_input("Landings", min_value=0, step=1)

    # --- 4. LOGIKA PENGHITUNGAN (WAJIB ADA DI SINI) ---
    # Kita panggil data terakhir dari database berdasarkan selected_ac
    base_fh, base_ld, base_e1h, base_e1c, base_e2h, base_e2c = get_current_totals(selected_ac)

    # Kita jumlahkan saldo awal + input baru untuk ditampilkan secara real-time
    current_total_af_h = base_fh + input_fh
    current_total_af_l = base_ld + input_ld
    current_total_e1_h = base_e1h + input_fh
    current_total_e1_c = base_e1c + input_ld
    current_total_e2_h = base_e2h + input_fh
    current_total_e2_c = base_e2c + input_ld

    # --- 5. TAMPILKAN HASILNYA DI FIELD BAWAH (READ-ONLY) ---
    st.write("---")
    st.info("💡 Auto-Calculated Totals (Current + New Entry)")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.text_input("Total AF Hours", value=f"{current_total_af_h:.2f}", disabled=True)
    with c2:
        st.text_input("Total AF Landings", value=str(int(current_total_af_l)), disabled=True)
    with c3:
        st.text_input("Total E1 Hours", value=f"{current_total_e1_h:.2f}", disabled=True)
    with c4:
        st.text_input("Total E1 Cycles", value=str(int(current_total_e1_c)), disabled=True)
    with c5:
        st.text_input("Total E2 Hours", value=f"{current_total_e2_h:.2f}", disabled=True)
    with c6:
        st.text_input("Total E2 Cycles", value=str(int(current_total_e2_c)), disabled=True)


    st.divider()

    # --- SECTION CHILD: TABS ---
    st.subheader("2. Detailed Reports (Child)")
    tab1, tab2, tab3 = st.tabs(["🔥 Engine Parameter", "👨‍✈️ Pilot Report", "⚙️ Component Replacement"])

    with tab1:
        st.caption("Engine Performance Data")

        colm1, colm2, colm3 = st.columns(3)
        press_alt = colm1.text_input("Pressure Altitude") 
        oat = colm2.text_input("OAT")
        ias = colm3.text_input("IAS")

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.markdown("**Engine 1**")
            tq1 = st.number_input("TQ 1", key="tq1")
            np1 = st.number_input("NP 1", key="np1")
            t51 = st.number_input("T5 1", key="t51")
            ng1 = st.number_input("NG 1", key="ng1")
            ff1 = st.number_input("FF 1", key="ff1")
            ot1 = st.number_input("OT 1", key="ot1")
            op1 = st.number_input("OP 1", key="op1")
            oa1 = st.number_input("OA 1", key="oa1")

        with col_e2:
            st.markdown("**Engine 2**")
            tq2 = st.number_input("TQ 2", key="tq2")
            np2 = st.number_input("NP 2", key="np2")
            t52 = st.number_input("T5 2", key="t52")
            ng2 = st.number_input("NG 2", key="ng2")
            ff2 = st.number_input("FF 2", key="ff2")
            ot2 = st.number_input("OT 2", key="ot2")
            op2 = st.number_input("OP 2", key="op2")
            oa2 = st.number_input("OA 2", key="oa2")

    with tab2:
            st.caption("Input maksimal 3 temuan pilot")
            pilot_reports = []
            for i in range(1, 4):
                with st.expander(f"Pilot Report #{i}"):
                    col_a, col_b = st.columns([1, 3])
                    def_id = col_a.text_input(f"Defect ID {i}", key=f"def_id_{i}")
                    def_desc = col_b.text_input(f"Description {i}", key=f"def_desc_{i}")
                    rect = st.text_area(f"Rectification {i}", key=f"rect_{i}", height=70)
                    lame = st.text_input(f"LAME {i}", key=f"lame_{i}")
                    pilot_reports.append({"id": def_id, "desc": def_desc, "rect": rect, "lame": lame})

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
                rem_pn = col_rem.text_input(f"Off P/N {j}", key=f"rem_pn_{j}")
                rem_sn = col_rem.text_input(f"Off S/N {j}", key=f"rem_sn_{j}")
                ins_pn = col_ins.text_input(f"On P/N {j}", key=f"ins_pn_{j}")
                ins_sn = col_ins.text_input(f"On S/N {j}", key=f"ins_sn_{j}")
                comp_replacements.append({"pos": pos, "p_desc": p_desc, "rem_pn": rem_pn})

# --- BUTTON SAVE ---
    if st.button("💾 Submit AML Entry", use_container_width=True, type="primary"):
        if aml_no:
            conn = create_connection()
            curr = conn.cursor()
            try:
                # 1. SIMPAN DATA UTAMA (Parent)
                curr.execute("""
                    INSERT INTO aml_utilization (aml_no, ac_type, ac_reg, date, departure, arrival, flight_hours, landings)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (aml_no, ac_type, selected_ac, str(date_entry), departure, arrival, input_fh, input_ld))
            
                # 2. SIMPAN ENGINE PARAMETER (Child 1)
                # Pastikan tabel 'engine_parameters' sudah dibuat di database.py
                curr.execute("""
                    INSERT INTO engine_parameters (aml_no, press_alt, oat, ias, tq1, np1, t51, ng1, ff1, ot1, op1, oa1, tq2, np2, t52, ng2, ff2, ot2, op2, oa2)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (aml_no, press_alt, oat, ias, tq1, np1, t51, ng1, ff1, ot1, op1, oa1, tq2, np2, t52, ng2, ff2, ot2, op2, oa2))

                # 3. SIMPAN PILOT REPORTS (Child 2 - Looping)
                for report in pilot_reports:
                    if report['id']: # Hanya simpan jika Defect ID diisi
                        curr.execute("""
                            INSERT INTO aml_pilot_report (aml_no, defect_id, description, rectification, lame)
                            VALUES (?, ?, ?, ?, ?)
                        """, (aml_no, report['id'], report['desc'], report['rect'], report['lame']))

                # 4. SIMPAN COMPONENT REPLACEMENT (Child 3 - Looping)
                for comp in comp_replacements:
                    if comp['pos']: # Hanya simpan jika Position dipilih (E1/E2/AF)
                        curr.execute("""
                            INSERT INTO aml_component_replacement (aml_no, pos, part_desc, rem_pn, rem_sn, ins_pn, ins_sn, grn)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (aml_no, comp['pos'], comp['p_desc'], comp['rem_pn'], comp['rem_sn'], comp['ins_pn'], comp['ins_sn'], comp['grn']))
            
                conn.commit()
                st.success(f"✅ AML No {aml_no} and all details saved successfully!")
                st.rerun()
            
            except Exception as e:
                conn.rollback() # Batalkan semua jika salah satu gagal
                st.error(f"❌ Gagal menyimpan: {e}")
            finally:
                conn.close()

    # --- TABEL DATA & FITUR DELETE (Di bawah tombol Submit) ---
    st.divider()
    st.subheader("📋 Registered AML Records")
    
    conn = create_connection()
    try:
        # Mengambil data untuk tabel
        df_aml = pd.read_sql("SELECT aml_no, ac_reg, date, flight_hours, landings FROM aml_utilization ORDER BY date DESC", conn)
        
        if not df_aml.empty:
            for _, row in df_aml.iterrows():
                with st.expander(f"AML: {row['aml_no']} | {row['ac_reg']} | {row['date']}"):
                    col_info, col_act = st.columns([3, 1])
                    col_info.write(f"Hours: {row['flight_hours']} | Landings: {row['landings']}")
                    
                    if col_act.button("🗑️ Delete", key=f"del_{row['aml_no']}"):
                        curr = conn.cursor()
                        curr.execute("DELETE FROM aml_utilization WHERE aml_no = ?", (row['aml_no'],))
                        conn.commit()
                        st.rerun()
        else:
            st.info("Belum ada data AML yang tersimpan.")
    except:
        pass
    finally:
        conn.close()        