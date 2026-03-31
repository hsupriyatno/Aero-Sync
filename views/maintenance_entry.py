import streamlit as st
from database import create_connection

def show(page_name):
    st.header("📝 Aircraft Maintenance Log (AML) Entry")
    
    # --- SECTION PARENT: UTILIZATION ---
    st.subheader("1. Utilization Record (Parent)")
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        aml_no = col1.text_input("AML No")
        ac_reg = col2.selectbox("A/C Reg", ["PK-OCA", "PK-OCB", "PK-OCC"]) # Ambil dari DB nantinya
        ac_type = col3.text_input("A/C Type", value="Bell 412")
        date = col4.date_input("Date")

        c1, c2, c3, c4 = st.columns(4)
        departure = c1.text_input("Departure")
        arrival = c2.text_input("Arrival")
        flight_hours = c3.number_input("Flight Hours", step=0.1)
        landings = c4.number_input("Landings", step=1)

        c11, c12, c13, c14, c15, c16 = st.columns(6)
        total_af_hours = c11.text_input("Total AF Hours")
        total_af_landings = c12.text_input("Total AF Landings")
        total_e1_hours = c13.text_input("Total E1 Hours")
        total_e1_cycles = c14.text_input("Total E1 Cycles")
        total_e2_hours = c15.text_input("Total E2 Hours")
        total_e2_cycles = c16.text_input("Total E2 Cycles")


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


# --- BUTTON SAVE (LANJUTAN) ---
    st.divider()
    if st.button("💾 Submit AML Entry", use_container_width=True, type="primary"):
        if aml_no: # Validasi sederhana, minimal nomor AML diisi
            conn = create_connection()
            curr = conn.cursor()
            try:
                # 1. Simpan Parent (Utilization)
                curr.execute("""
                    INSERT INTO aml_utilization (aml_no, ac_type, ac_reg, date, departure, arrival, flight_hours, landings)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (aml_no, ac_type, ac_reg, str(date), dep, arr, fh, ldg))

                # 2. Simpan Child: Pilot Reports (Hanya jika Deskripsi diisi)
                for pr in pilot_reports:
                    if pr['desc']: # Jika ada deskripsi, baru simpan
                        curr.execute("""
                            INSERT INTO aml_pilot_report (aml_no, defect_id, defect_desc, rectification, lame)
                            VALUES (?, ?, ?, ?, ?)
                        """, (aml_no, pr['id'], pr['desc'], pr['rect'], pr['lame']))

                # 3. Simpan Child: Component Replacements (Hanya jika P/N diisi)
                for cr in comp_replacements:
                    if cr['p_desc']: # Jika ada nama part, baru simpan
                        curr.execute("""
                            INSERT INTO aml_component_replacement (aml_no, pos, part_desc, rem_pn)
                            VALUES (?, ?, ?, ?)
                        """, (aml_no, cr['pos'], cr['p_desc'], cr['rem_pn']))

                conn.commit()
                st.success(f"✅ Sukses! AML No {aml_no} berhasil disimpan ke database.")
                st.balloons() # Efek perayaan kecil
                
            except Exception as e:
                st.error(f"❌ Gagal menyimpan: {e}")
            finally:
                conn.close()
        else:
            st.warning("⚠️ Mohon isi Nomor AML terlebih dahulu sebelum menyimpan.")        