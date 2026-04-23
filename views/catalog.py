import streamlit as st
import pandas as pd
import graphviz
import sqlite3
from datetime import datetime
from database import create_connection

def show(page_name):
    # --- CSS Injection ---
    st.markdown("""
        <style>
        .section-font { font-size:20px !important; font-weight: bold; margin-top: 10px; color: #1E3A8A; }
        </style>
    """, unsafe_allow_html=True)

    # Gunakan satu database yang sama untuk semua fitur (misal: aero_synch.db)
    db_name = 'aero_synch.db' 
    conn = create_connection() # Menggunakan fungsi dari database.py

    try:
        # === HALAMAN 1: AIRCRAFT CATALOG ===
        if page_name == "Aircraft Catalog":
            st.header("✈️ Aircraft Catalog")
            
            with st.form("form_catalog"):
                col1, col2 = st.columns(2)
                with col1:
                    ac_reg = st.text_input("Aircraft Registration", placeholder="PK-ABC")
                    ac_type = st.selectbox("Aircraft Type", ["DHC6-300", "DHC6-400", "B737-800", "B737-MAX", "BELL 412"])
                    msn = st.text_input("MSN (Manufacturer Serial Number)")
                with col2:
                    tsn = st.number_input("Total Airframe Hours (TSN)", min_value=0.0)
                    csn = st.number_input("Total Airframe Cycles (CSN)", min_value=0)
                    entry_date = st.date_input("Entry into Service Date")

                if st.form_submit_button("Register Aircraft"):
                    curr = conn.cursor()
                    curr.execute('''INSERT INTO catalog (ac_reg, ac_type, msn, tsn, csn, entry_date)
                                 VALUES (?, ?, ?, ?, ?, ?)''', 
                                 (ac_reg, ac_type, msn, tsn, csn, str(entry_date)))
                    conn.commit()
                    st.success(f"Aircraft {ac_reg} registered successfully!")
                    st.rerun()

            st.divider()
            # Ambil data dari database
            df_list = pd.read_sql_query("SELECT ac_reg, ac_type, msn, tsn, csn FROM catalog", conn)
            
            if not df_list.empty:
                st.subheader("Registered Fleet")
                st.dataframe(df_list, use_container_width=True) 
                
                st.divider()
                st.subheader("🛠️ Edit or Remove Aircraft")

                # Pilih pesawat yang mau di-edit/hapus (MENGGUNAKAN df_list)
                list_ac = df_list['ac_reg'].tolist()
                selected_ac = st.selectbox("Select Registration to Edit/Delete", list_ac)

                if selected_ac:
                    # Ambil data lama untuk ditampilkan di input
                    row = df_list[df_list['ac_reg'] == selected_ac].iloc[0]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        # Pastikan pilihan type sesuai dengan yang ada di database atau list
                        current_types = ["DHC6-300", "DHC6-400", "B737-800", "B737-MAX", "BELL 412"]
                        # Jika type lama tidak ada di list, tambahkan sementara agar tidak error
                        if row['ac_type'] not in current_types:
                            current_types.append(row['ac_type'])
                            
                        new_type = st.selectbox("Aircraft Type", current_types, 
                                               index=current_types.index(row['ac_type']))
                        new_msn = st.text_input("MSN", value=row['msn'])
                    with col2:
                        new_tsn = st.number_input("Total Hours (TSN)", value=float(row['tsn']))
                        new_csn = st.number_input("Total Cycles (CSN)", value=int(row['csn']))

                    btn_edit, btn_delete = st.columns(2)
                    
                    with btn_edit:
                        if st.button("💾 Save Changes", use_container_width=True):
                            # Memanggil fungsi dari database.py
                            from database import update_aircraft
                            update_aircraft(selected_ac, new_type, new_msn, new_tsn, new_csn)
                            st.success(f"Data {selected_ac} berhasil diperbarui!")
                            st.rerun()

                    with btn_delete:
                        if st.button("🗑️ Delete Aircraft", type="primary", use_container_width=True):
                            # Memanggil fungsi dari database.py
                            from database import delete_aircraft
                            delete_aircraft(selected_ac)
                            st.warning(f"Data {selected_ac} telah dihapus.")
                            st.rerun()
            else:
                st.info("No aircraft registered yet.")

        # === HALAMAN 2: STRUCTURE MANAGEMENT ===
        elif page_name == "Structure Management":
            st.header("🏗️ Aircraft Structure Management")
            
            # 1. Pilih Tipe Pesawat
            df_ac = pd.read_sql_query("SELECT DISTINCT ac_type FROM catalog", conn)
            if df_ac.empty:
                st.warning("Daftarkan pesawat di Aircraft Catalog terlebih dahulu.")
                return

            selected_type = st.selectbox("Pilih Aircraft Type", df_ac['ac_type'])

            # 2. Ambil List Description Unik dari Master Part Number
            # Ini kuncinya: Kita hanya ambil Description agar tidak terkunci ke satu P/N
            df_master = pd.read_sql_query("SELECT DISTINCT description, ata_chapter FROM master_part_number", conn)
            
            if df_master.empty:
                st.error("Master Part Number kosong! Isi data di menu Inventory dulu.")
                return

            description_options = sorted(df_master['description'].tolist())
            ata_mapping = dict(zip(df_master['description'], df_master['ata_chapter']))

            # --- 3. Form Input Struktur (Berdasarkan Description) ---
            with st.form("form_structure"):
                st.markdown(f'<p class="section-font">Add Component for {selected_type}</p>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                
                with col1:
                    # Parent bisa berupa Airframe atau komponen lain yang sudah terdaftar
                    parent_list = ["Airframe"] + description_options
                    p_name = st.selectbox("Installed to (Parent)", parent_list)
                    
                    # Child (Komponen yang mau didaftarkan strukturnya)
                    c_name = st.selectbox("Component Name (Description Only)", description_options)
                
                with col2:
                    # Auto-fill ATA berdasarkan Description yang dipilih
                    default_ata = ata_mapping.get(c_name, "")
                    ata = st.text_input("ATA Chapter", value=default_ata)
                    qty = st.number_input("Required Qty", min_value=1, value=1)

                if st.form_submit_button("Submit Structure"):
                    curr = conn.cursor()
                    curr.execute('''INSERT INTO aircraft_structure 
                                   (ac_type, parent_component, sub_component, ata_chapter, required_qty)
                                   VALUES (?, ?, ?, ?, ?)''', 
                                   (selected_type, p_name, c_name, ata, qty))
                    conn.commit()
                    st.success(f"Struktur '{c_name}' untuk {selected_type} berhasil disimpan!")
                    st.rerun()

            # --- 4. Visual Hierarchy ---
            st.divider()
            st.subheader(f"Visual Hierarchy: {selected_type}")
            
            df_view = pd.read_sql_query(f"SELECT * FROM aircraft_structure WHERE ac_type = '{selected_type}'", conn)

            if not df_view.empty:
                dot = graphviz.Digraph()
                dot.attr(rankdir='LR')
                dot.attr('node', shape='record', style='filled', fontname='Arial', fontsize='10')

                for _, row in df_view.iterrows():
                    p, c, a, q = str(row['parent_component']), str(row['sub_component']), str(row['ata_chapter']), str(row['required_qty'])
                    
                    if p.lower() == 'airframe':
                        dot.node(p, fillcolor='#FFD700', label=f"{{ {p} }}")
                    
                    node_label = f"{{ {c} | {{ ATA: {a} | Qty: {q} }} }}"
                    color = '#ADD8E6' if p.lower() == 'airframe' else '#E0FFE0'
                    dot.node(c, fillcolor=color, label=node_label)
                    dot.edge(p, c)

                st.graphviz_chart(dot)

            # --- 5. Manage Existing Structure ---
            st.divider()
            st.subheader("📋 Manage Existing Structure")
            
            if not df_view.empty:
                for _, row in df_view.iterrows():
                    with st.expander(f"⚙️ {row['sub_component']} (Parent: {row['parent_component']})"):
                        edit_col1, edit_col2 = st.columns(2)
                        with edit_col1:
                            new_ata = st.text_input("Edit ATA", value=row['ata_chapter'], key=f"ata_{row['id']}")
                            new_qty = st.number_input("Edit Qty", min_value=1, value=int(row['required_qty']), key=f"qty_{row['id']}")
                        
                        with edit_col2:
                            if st.button("Update", key=f"upd_{row['id']}", use_container_width=True):
                                curr = conn.cursor()
                                curr.execute("UPDATE aircraft_structure SET ata_chapter=?, required_qty=? WHERE id=?", (new_ata, new_qty, row['id']))
                                conn.commit()
                                st.rerun()
                            
                            if st.button("Delete", key=f"del_{row['id']}", type="secondary", use_container_width=True):
                                curr = conn.cursor()
                                curr.execute("DELETE FROM aircraft_structure WHERE id = ?", (row['id'],))
                                conn.commit()
                                st.rerun()

# === HALAMAN 3: MAINTENANCE CATALOG (Perbaikan di Sini) ===
        elif page_name == "Maintenance Catalog":
            st.header("🛠️ Maintenance Catalog")
            st.info("Master data untuk Task Maintenance individual.")

            with st.form("form_maintenance_catalog", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    aircraft_type = st.selectbox("Aircraft Type", ["Bell-412", "DHC6-300", "DHC6-400", "B737-8 MAX", "MIL171", "AS350B3"])
                    task_id = st.text_input("Task ID (e.g., EMMA-01)")
                    task_title = st.text_input("Task Title")
                with col2:
                    interval_hours = st.number_input("Interval Hours", min_value=0.0)
                    interval_cycles = st.number_input("Interval Cycles", min_value=0)
                    interval_calendar = st.number_input("Interval Calendar (Days)", min_value=0)
                
                task_description = st.text_area("Task Description")
                submit_button = st.form_submit_button("Save to Catalog")

                if submit_button:
                    if task_id and task_title:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO maintenance_catalog 
                            (aircraft_type, task_id, task_title, task_description, interval_hours, interval_cycles, interval_calendar)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (aircraft_type, task_id, task_title, task_description, interval_hours, interval_cycles, interval_calendar))
                        conn.commit()
                        st.success(f"Task {task_id} disimpan!")
                        st.rerun()
                    else:
                        st.warning("Isi Task ID dan Title!")

            # Tampilkan Tabel
            st.divider()
            df_cat = pd.read_sql_query("SELECT * FROM maintenance_catalog", conn)
            st.dataframe(df_cat, use_container_width=True)

    except Exception as e:
        st.error(f"Error pada halaman {page_name}: {e}")
    finally:
        conn.close()