import streamlit as st
import pandas as pd
from database import create_connection

def show(page_name):
    if page_name == "Structure Management": # Sesuaikan dengan nama di app.py Bapak
        st.header("🏗️ Aircraft Configuration Management")
        st.write("Definisikan komponen wajib (Master Blueprint) untuk setiap tipe pesawat.")

        conn = create_connection()
        curr = conn.cursor()

        # --- 1. DATA PREPARATION ---
        # Ambil list Tipe Pesawat dari Catalog
        df_types = pd.read_sql_query("SELECT DISTINCT ac_type FROM catalog", conn)
        type_list = df_types['ac_type'].tolist() if not df_types.empty else ["DHC6-300", "Bell 412", "B737-8"]

        # Ambil data dari Master Part Number untuk Dropdown Component
        df_master = pd.read_sql_query("SELECT DISTINCT component_name, ata_chapter FROM master_part_number", conn)
        master_dict = dict(zip(df_master['component_name'], df_master['ata_chapter']))
        component_options = sorted(list(master_dict.keys()))

        # --- 2. FORM INPUT STRUCTURE ---
        with st.expander("➕ Tambah Struktur Komponen Baru", expanded=True):
            with st.form("form_structure"):
                col1, col2 = st.columns(2)
                
                with col1:
                    ac_type = st.selectbox("Tipe Pesawat", type_list)
                    
                    # Dropdown Parent: Ambil dari komponen yang sudah terdaftar di tipe pesawat ini
                    curr.execute("SELECT DISTINCT sub_component FROM aircraft_structure WHERE ac_type = ?", (ac_type,))
                    existing_comps = [r[0] for r in curr.fetchall()]
                    parent_options = ["Airframe"] + existing_comps
                    parent = st.selectbox("Installed to (Parent)", parent_options)

                with col2:
                    # Dropdown Component: Ambil dari Master Part Number
                    comp_name = st.selectbox("Component Name", ["-- Pilih dari Master --"] + component_options)
                    
                    # Auto-fill ATA Chapter (Disabled agar tidak diubah manual)
                    auto_ata = master_dict.get(comp_name, "") if comp_name != "-- Pilih dari Master --" else ""
                    st.text_input("ATA Chapter", value=auto_ata, disabled=True)
                    
                    req_qty = st.number_input("Required Qty", min_value=1, value=1)

                if st.form_submit_button("Simpan ke Blueprint"):
                    if comp_name != "-- Pilih dari Master --":
                        try:
                            curr.execute("""
                                INSERT INTO aircraft_structure (ac_type, parent_component, sub_component, ata_chapter, required_qty)
                                VALUES (?, ?, ?, ?, ?)
                            """, (ac_type, parent, comp_name, auto_ata, req_qty))
                            conn.commit()
                            st.success(f"✅ {comp_name} ditambahkan ke struktur {ac_type}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Silakan pilih Component Name dari Master.")

        # --- 3. TAMPILAN BLUEPRINT ---
        st.subheader("📋 Master Structure List")
        df_view = pd.read_sql_query("SELECT * FROM aircraft_structure", conn)

        if not df_view.empty:
            tipe_pilihan = st.selectbox("Filter Tipe Pesawat", df_view['ac_type'].unique())
            filtered_df = df_view[df_view['ac_type'] == tipe_pilihan]
            
            # Tampilkan tabel yang lebih lengkap
            st.dataframe(
                filtered_df[['parent_component', 'sub_component', 'ata_chapter', 'required_qty']],
                use_container_width=True,
                hide_index=True
            )
            
            # Fitur Hapus
            st.write("---")
            comp_to_delete = st.selectbox("Pilih komponen untuk dihapus", filtered_df['sub_component'].unique())
            if st.button("🗑️ Hapus Komponen dari Struktur"):
                curr.execute("DELETE FROM aircraft_structure WHERE ac_type = ? AND sub_component = ?", (tipe_pilihan, comp_to_delete))
                conn.commit()
                st.rerun()
        else:
            st.info("Belum ada struktur yang didefinisikan.")

        conn.close()