import streamlit as st
import pandas as pd
import graphviz
from database import create_connection

def show(page_name):
    # Inject CSS untuk estetika UI
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
            df_list = pd.read_sql_query("SELECT ac_reg, ac_type, msn, tsn, csn FROM catalog", conn)
            if not df_list.empty:
                st.subheader("Registered Fleet")
                st.dataframe(df_list, use_container_width=True)    
            else:
                st.info("No aircraft registered yet.")

        # === HALAMAN 2: STRUCTURE MANAGEMENT ===
        if page_name == "Structure Management":
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

    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        conn.close()