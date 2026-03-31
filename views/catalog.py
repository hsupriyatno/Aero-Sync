import streamlit as st
import pandas as pd
from database import create_connection

def show(Catalog):
    # GUNAKAN 'if' UNTUK KONDISI PERTAMA
    if page_name == "Catalog":
        st.subheader("Add New Aircraft")

# 1. AIRCRAFT CATALOG
    elif current_page == "Catalog":
        st.subheader("Add New Aircraft")
    
        with st.form("form_aircraft"):
            col1, col2 = st.columns(2)
            with col1:
                reg = st.text_input("Registration (e.g. PK-OFI)")
                ac_type = st.selectbox("Type", ["B737-8", "DHC6-300", "DHC6-400", "Bell 412", "AS350B3", "MIL171"])
                msn = st.text_input("Manufacturer Serial Number (MSN)")
                tsn = st.number_input("Total Time Since New (Aircraft)", min_value=0.0)
                csn = st.number_input("Total Cycles Since New (Aircraft)", min_value=0)
            with col2:
                tsn_e1 = st.number_input("Total Time Since New (Engine 1)", min_value=0.0)
                csn_e1 = st.number_input("Total Cycles Since New (Engine 1)", min_value=0)
                tsn_e2 = st.number_input("Total Time Since New (Engine 2)", min_value=0.0)
                csn_e2 = st.number_input("Total Cycles Since New (Engine 2)", min_value=0)
                entry_date = st.date_input("Date Enter to Airfast")
            
            submit = st.form_submit_button("Simpan Pesawat")
        
            if submit:
                conn = create_connection()
                curr = conn.cursor()
                try:
                    curr.execute('''INSERT INTO catalog (ac_reg, ac_type, msn, tsn, csn, tsn_e1, csn_e1, tsn_e2, csn_e2, entry_date) 
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (reg, ac_type, msn, tsn, csn, tsn_e1, csn_e1, tsn_e2, csn_e2, entry_date))
                    conn.commit()
                    st.success(f"Pesawat {reg} berhasil didaftarkan!")
                except Exception as e:
                    st.error(f"Gagal simpan: {e}")
                conn.close()

        st.divider()
        st.subheader("Current Fleet List")
        conn = create_connection()
        df = pd.read_sql_query("SELECT * FROM aircraft_catalog", conn)
        st.dataframe(df, use_container_width=True)
        conn.close()

# 2. STRUCTURE MANAGEMENT
    elif current_page == "Structure Management":
        st.subheader("Manage Aircraft Structure & Components")

        conn = create_connection()
        df_ac = pd.read_sql_query("SELECT id, ac_reg FROM aircraft_catalog", conn)
    
        if df_ac.empty:
            st.warning("Mohon daftarkan pesawat di menu 'Catalog' terlebih dahulu.")
        else:
            ac_options = {row['ac_reg']: row['id'] for index, row in df_ac.iterrows()}
            selected_ac_reg = st.selectbox("Pilih Pesawat", list(ac_options.keys()))
            selected_ac_id = ac_options[selected_ac_reg]

            with st.expander("➕ Tambah Komponen Baru"):
                with st.form("form_component"):
                    col1, col2 = st.columns(2)
                    with col1:
                        p_n = st.text_input("Part Number (P/N)")
                        s_n = st.text_input("Serial Number (S/N)")
                        desc = st.text_input("Description")
                    with col2:
                        tsn_c = st.number_input("Component TSN", min_value=0.0)
                        csn_c = st.number_input("Component CSN", min_value=0)
                    
                        df_p = pd.read_sql_query(f"SELECT id, description FROM aircraft_structure WHERE ac_id = {selected_ac_id}", conn)
                        parent_options = {"None (Top Level)": None}
                        for _, r in df_p.iterrows():
                            parent_options[r['description']] = r['id']
                    
                        selected_parent = st.selectbox("Parent Component", list(parent_options.keys()))

                    submit_comp = st.form_submit_button("Install Component")
                
                    if submit_comp:
                        curr = conn.cursor()
                        parent_id = parent_options[selected_parent]
                        curr.execute('''INSERT INTO aircraft_structure 
                                 (ac_id, parent_id, part_number, serial_number, description, tsn, csn) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                                 (selected_ac_id, parent_id, p_n, s_n, desc, tsn_c, csn_c))
                        conn.commit()
                        st.success(f"Komponen {desc} berhasil dipasang!")

            st.divider()
            st.subheader(f"Component List for {selected_ac_reg}")
            df_struct = pd.read_sql_query(f"SELECT id, parent_id, description, part_number, serial_number, tsn FROM aircraft_structure WHERE ac_id = {selected_ac_id}", conn)
            st.dataframe(df_struct, use_container_width=True)
        conn.close()