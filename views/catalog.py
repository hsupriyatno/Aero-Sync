import streamlit as st
import pandas as pd
import graphviz
from database import create_connection

def show(page_name):
    # Inject CSS untuk mengecilkan semua judul utama secara global
    st.markdown("""
        <style>
        .small-font { font-size:24px !important; font-weight: bold; color: #1E3A8A; }
        .section-font { font-size:20px !important; font-weight: bold; margin-top: 10px; }
        </style>
    """, unsafe_allow_html=True)

    conn = create_connection()
    
    try:
        # === HALAMAN 1: AIRCRAFT CATALOG ===
        if page_name == "Aircraft Catalog":
            st.header("✈️ Aircraft Catalog")
            
            # Form Input Pesawat Baru
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

            # Tampilkan Daftar Pesawat yang Ada
            st.divider()
            df_list = pd.read_sql_query("SELECT ac_reg, ac_type, msn, tsn, csn FROM catalog", conn)
            if not df_list.empty:
                st.subheader("Registered Fleet")
                st.dataframe(df_list, use_container_width=True)    
            else:
                st.info("No aircraft registered yet.")

        if page_name == "Structure Management":
            st.header("🏗️ Aircraft Structure Management")
            
            # 1. Ambil data tipe pesawat untuk filter
            df_ac = pd.read_sql_query("SELECT DISTINCT ac_type FROM catalog", conn)
            
            if df_ac.empty:
                st.warning("Daftarkan pesawat di Aircraft Catalog terlebih dahulu.")
                return

            selected_type = st.selectbox("Pilih Aircraft Type", df_ac['ac_type'])

            # 2. Ambil data Master Part Number untuk Dropdown Parent & Component
            df_parts = pd.read_sql_query("SELECT part_number, description FROM master_part_number", conn)
            
            if df_parts.empty:
                st.error("Master Part Number masih kosong! Isi data di menu Inventory dulu.")
                part_options = []
            else:
                part_options = (df_parts['part_number'] + " - " + df_parts['description']).tolist()

            # --- 3. Form Input Struktur ---
            with st.form("form_structure"):
                st.markdown(f'<p class="section-font">Add Component for {selected_type}</p>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                
                # Ambil data Master Part Number lengkap (termasuk ATA Chapter)
                df_parts = pd.read_sql_query("SELECT part_number, description, ata_chapter FROM master_part_number", conn)
                
                if not df_parts.empty:
                    # Buat mapping Dictionary untuk lookup ATA Chapter otomatis
                    ata_mapping = dict(zip(df_parts['part_number'], df_parts['ata_chapter']))
                    part_options = (df_parts['part_number'] + " - " + df_parts['description']).tolist()
                else:
                    ata_mapping = {}
                    part_options = []

                with col1:
                    parent_list = ["Airframe"] + part_options
                    p_raw = st.selectbox("Installed to (Parent)", parent_list)
                    
                    # Kita gunakan index untuk mendeteksi perubahan pilihan komponen
                    c_raw = st.selectbox("Component (Child)", part_options)
                
                with col2:
                    # LOGIKA OTOMATIS: Ambil ATA dari mapping berdasarkan PN yang dipilih
                    selected_pn = c_raw.split(" - ")[0] if c_raw else ""
                    auto_ata = ata_mapping.get(selected_pn, "") # Ambil dari DB, default kosong jika tidak ada
                    
                    ata = st.text_input("ATA Chapter", value=auto_ata, placeholder="e.g. 21-10-00")
                    qty = st.number_input("Required Qty", min_value=1, value=1)

                if st.form_submit_button("Submit Structure"):
                    # ... (logika submit tetap sama)
                    p_pn = p_raw.split(" - ")[0] if " - " in p_raw else p_raw
                    c_pn = c_raw.split(" - ")[0]
                    curr = conn.cursor()
                    curr.execute('''INSERT INTO aircraft_structure 
                                 (ac_type, parent_component, sub_component, ata_chapter, required_qty)
                                 VALUES (?, ?, ?, ?, ?)''', (selected_type, p_pn, c_pn, ata, qty))
                    conn.commit()
                    st.success("Structure updated!")
                    st.rerun()

            # 4. Ambil data untuk Visualisasi (Keluar dari blok form)
            st.divider()
            st.subheader(f"Visual Hierarchy: {selected_type}")
            
            query_view = f"""
                SELECT parent_component as Parent, sub_component as Component, 
                       ata_chapter as ATA, required_qty as Qty 
                FROM aircraft_structure 
                WHERE ac_type = '{selected_type}'
            """
            df_view = pd.read_sql_query(query_view, conn)

            if not df_view.empty:
                dot = graphviz.Digraph()
                dot.attr(rankdir='LR')
                dot.attr('node', shape='record', style='filled', fontname='Arial', fontsize='10')

                for _, row in df_view.iterrows():
                    p, c, a, q = str(row['Parent']), str(row['Component']), str(row['ATA']), str(row['Qty'])
                    
                    # Gambar Node Parent jika Airframe
                    if p.lower() == 'airframe':
                        dot.node(p, fillcolor='#FFD700', label=f"{{ {p} }}")
                    
                    # Node Component
                    node_label = f"{{ {c} | {{ ATA: {a} | Qty: {q} }} }}"
                    color = '#ADD8E6' if p.lower() == 'airframe' else '#E0FFE0'
                    dot.node(c, fillcolor=color, label=node_label)
                    
                    dot.edge(p, c)

                st.graphviz_chart(dot)
            else:
                st.info(f"Belum ada data struktur untuk {selected_type}.")

            # --- 5. EDIT & DELETE SECTION ---
            st.divider()
            st.subheader("📋 Manage Existing Structure")
            
            if not df_view.empty:
                # Kita ambil ID asli dari database agar bisa di-delete/update
                df_manage = pd.read_sql_query(f"""
                    SELECT id, parent_component, sub_component, ata_chapter, required_qty 
                    FROM aircraft_structure WHERE ac_type = '{selected_type}'
                """, conn)

                for _, row in df_manage.iterrows():
                    with st.expander(f"⚙️ {row['sub_component']} (Parent: {row['parent_component']})"):
                        edit_col1, edit_col2 = st.columns(2)
                        
                        # Form Edit Mini
                        with edit_col1:
                            new_ata = st.text_input("Edit ATA", value=row['ata_chapter'], key=f"ata_{row['id']}")
                            new_qty = st.number_input("Edit Qty", min_value=1, value=int(row['required_qty']), key=f"qty_{row['id']}")
                        
                        with edit_col2:
                            st.write("Action:")
                            # Tombol Update
                            if st.button("Update Data", key=f"upd_{row['id']}", use_container_width=True):
                                curr = conn.cursor()
                                curr.execute("""
                                    UPDATE aircraft_structure 
                                    SET ata_chapter = ?, required_qty = ? 
                                    WHERE id = ?
                                """, (new_ata, new_qty, row['id']))
                                conn.commit()
                                st.success("Updated!")
                                st.rerun()
                            
                            # Tombol Delete dengan warna merah
                            if st.button("🗑️ Delete Component", key=f"del_{row['id']}", type="secondary", use_container_width=True):
                                curr = conn.cursor()
                                curr.execute("DELETE FROM aircraft_structure WHERE id = ?", (row['id'],))
                                conn.commit()
                                st.warning("Component Deleted!")
                                st.rerun()
            else:
                st.info("No data available to manage.")

    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        conn.close()