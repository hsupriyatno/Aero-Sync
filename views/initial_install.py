import streamlit as st
import pandas as pd
import sqlite3
from database import create_connection
import io
from datetime import datetime

def generate_component_report(df, ac_reg, ac_type):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Initial_Status', index=False, startrow=4)
        workbook  = writer.book
        worksheet = writer.sheets['Initial_Status']
        header_format = workbook.add_format({'bold': True, 'font_size': 14})
        info_format = workbook.add_format({'font_size': 11})
        worksheet.write('A1', f"INITIAL COMPONENT STATUS REPORT - {ac_reg}", header_format)
        worksheet.write('A2', f"Aircraft Type: {ac_type}", info_format)
        worksheet.write('A3', f"Print Date: {datetime.now().strftime('%d-%b-%Y %H:%M')}", info_format)
        worksheet.set_column('A:B', 20)
        worksheet.set_column('C:D', 25)
        worksheet.set_column('E:K', 12)
    return output.getvalue()

def show():
    st.header("⚙️ Initial Component Installed")
    conn = create_connection()
    curr = conn.cursor()

    # 1. Dropdown Pilih Pesawat
    df_fleet = pd.read_sql_query("SELECT ac_reg, ac_type FROM catalog", conn)
    if df_fleet.empty:
        st.warning("Data Catalog kosong. Mohon isi Aircraft Catalog dulu.")
        return

    selected_reg = st.selectbox("Pilih Aircraft Registration", df_fleet['ac_reg'])
    selected_type = df_fleet[df_fleet['ac_reg'] == selected_reg]['ac_type'].values[0]
    st.info(f"Unit: {selected_reg} | Type: {selected_type}")

    # 2. Ambil Struktur Pesawat (Logic Grid Tetap Sama)
    query_struct = """
        SELECT sub_component, parent_component, required_qty, ata_chapter 
        FROM aircraft_structure 
        WHERE ac_type = ?
    """
    df_struct = pd.read_sql_query(query_struct, conn, params=(selected_type,))
    
    if not df_struct.empty:
        st.subheader("Configuration Grid Status")
        cols = st.columns(4) 
        
        for idx, item in df_struct.iterrows():
            with cols[idx % 4]:
                is_layer_1 = item['parent_component'].lower() == "airframe"

                # Hitung Total Required Berdasarkan Jumlah Parent (Maintain Logic)
                curr.execute("SELECT COUNT(*) FROM installed_components WHERE ac_reg = ? AND component_name = ?", 
                             (selected_reg, item['parent_component']))
                parent_count = curr.fetchone()[0]
                total_required = item['required_qty'] * max(1, parent_count) if not is_layer_1 else item['required_qty']

                # Cek Data Terpasang
                curr.execute("SELECT serial_number FROM installed_components WHERE ac_reg = ? AND component_name = ?", 
                             (selected_reg, item['sub_component']))
                already_in = len(curr.fetchall())
                
                # Display Only untuk Box
                curr.execute("SELECT serial_number FROM installed_components WHERE ac_reg = ? AND component_name = ? LIMIT 1", 
                             (selected_reg, item['parent_component']))
                p_data = curr.fetchone()
                parent_info = p_data[0] if p_data else "Airframe"

                # Logika Warna
                is_complete = already_in >= total_required
                if is_complete:
                    base_color, border_color = "#ffffff", "#2e7d32"
                else:
                    base_color = "#e3f2fd" if is_layer_1 else "#fffde7"
                    border_color = "#1976d2" if is_layer_1 else "#fbc02d"

                html_box = f"""
                <div style="border: 2px solid {border_color}; padding: 12px; border-radius: 10px; background-color: {base_color}; min-height: 150px; text-align: center; margin-bottom: 10px;">
                    <div style="font-size: 9px; color: #666; font-weight: bold;">{item['ata_chapter']}</div>
                    <div style="font-size: 10px; color: #444;">PARENT: {parent_info}</div>
                    <hr style="margin: 5px 0; border: 0.5px solid {border_color}; opacity: 0.3;">
                    <div style="font-size: 12px; font-weight: bold; height: 35px;">{item['sub_component'].upper()}</div>
                    <div style="font-size: 24px; font-weight: 800; color: {border_color};">{already_in} / {total_required}</div>
                    <div style="font-size: 11px; margin-top: 5px; font-weight: bold; color: {"#2e7d32" if is_complete else "#d32f2f"};">
                    {"✅ COMPLETE" if is_complete else "⏳ INCOMPLETE"}
                    </div>
                </div>"""
                st.markdown(html_box, unsafe_allow_html=True)
        
                if st.button(f"Update", key=f"btn_{selected_reg}_{idx}"):
                    st.session_state.show_form = True
                    st.session_state.target_comp = item['sub_component']
                    st.session_state.target_parent = item['parent_component']
                    st.rerun()

    st.divider()

    # 3. Form Entry
    if st.session_state.get('show_form'):
        st.subheader(f"📝 Install: {st.session_state.target_comp}")
        
        query_pn = "SELECT part_number, description FROM master_part_number WHERE description = ?"
        df_master_pn = pd.read_sql(query_pn, conn, params=(st.session_state.target_comp,))
        
        if df_master_pn.empty:
            df_master_pn = pd.read_sql("SELECT part_number, description FROM master_part_number", conn)
            
        # --- LOGIKA PARTS INTERCHANGE ---
        # Ambil P/N utama dari master
        main_pn_list = df_master_pn['part_number'].tolist()
        final_pn_options = []

        for pn in main_pn_list:
            final_pn_options.append(pn)
            # Cari apakah ada P/N pengganti (Interchange) untuk P/N ini
            curr.execute("""
                SELECT alternate_pn, interchange_type FROM part_interchange 
                WHERE original_pn = ?
            """, (pn,))
            rows = curr.fetchall()
            for row in rows:
                alt_pn, ic_type = row
                label = f"{alt_pn} (Alt for {pn})" if ic_type == 'TWO-WAY' else f"{alt_pn} (Supersedes {pn})"
                if alt_pn not in final_pn_options:
                    final_pn_options.append(alt_pn)

        # Masukkan ke Selectbox Bapak
        options_pn = ["-- Pilih P/N --"] + final_pn_options
        selected_pn = st.selectbox("Pilih Part Number (Interchangeable)", options=options_pn)

        comp_desc = st.session_state.target_comp
        sn_options = []
        if selected_pn != "-- Pilih P/N --":
            res_desc = df_master_pn[df_master_pn['part_number'] == selected_pn]['description']
            comp_desc = res_desc.values[0] if not res_desc.empty else ""
            curr.execute("""
                SELECT serial_number FROM master_serial_number 
                WHERE part_number = ? 
                AND (current_location NOT LIKE '%Aircraft%')
                AND (current_location LIKE '%Store%' OR location = ?)
            """, (selected_pn, selected_reg))
            sn_options = [r[0] for r in curr.fetchall()]

        parent_sn_list = ["Airframe"]
        if st.session_state.target_parent.lower() != "airframe":
            curr.execute("""
                SELECT serial_number, position FROM installed_components 
                WHERE ac_reg = ? AND component_name = ?
                ORDER BY position ASC
            """, (selected_reg, st.session_state.target_parent))
    
            rows = curr.fetchall()
            if rows:
                parent_sn_list = [f"{st.session_state.target_parent} | S/N: {r[0]} | Pos: {r[1]}" for r in rows]
            else:
                st.warning(f"Perhatian: {st.session_state.target_parent} belum terpasang di unit ini.")
                parent_sn_list = [f"{st.session_state.target_parent} (NOT INSTALLED)"]

        with st.form("form_final_install"):
            c1, c2 = st.columns(2)
            with c1:
                selected_parent_full = st.selectbox("Install to (Parent S/N)", options=parent_sn_list)
                selected_sn = st.selectbox("Serial Number", options=["-- Pilih S/N --"] + sn_options)
                pos = st.selectbox("Position", ["LH", "RH", "CTR", "NO.1", "NO.2", "ONLY"])
            
            with c2:
                st.success(f"**Component Name:**\n\n{comp_desc}")
                tsn = st.number_input("TSN", step=0.1)
                csn = st.number_input("CSN", step=1)
                tso = st.number_input("TSO", step=0.1)
                cso = st.number_input("CSO", step=1)
                dsn = st.number_input("DSN", step=0.1)
                dso = st.number_input("DSO", step=0.1)

            submitted = st.form_submit_button("Save Installation")

            if submitted:
                # --- LOGIKA VALIDASI KUOTA DINAMIS ---
                curr.execute("SELECT required_qty, parent_component FROM aircraft_structure WHERE ac_type = ? AND sub_component = ?", 
                             (selected_type, st.session_state.target_comp))
                res_struct = curr.fetchone()
                base_qty = res_struct[0] if res_struct else 1
                parent_name = res_struct[1] if res_struct else "Airframe"

                curr.execute("SELECT COUNT(*) FROM installed_components WHERE ac_reg = ? AND component_name = ?", 
                             (selected_reg, parent_name))
                parent_installed_count = curr.fetchone()[0]

                if parent_name.lower() == "airframe":
                    total_required_qty = base_qty
                else:
                    total_required_qty = base_qty * max(1, parent_installed_count)

                curr.execute("SELECT COUNT(*) FROM installed_components WHERE component_name = ? AND ac_reg = ?", 
                             (st.session_state.target_comp, selected_reg))
                already_installed = curr.fetchone()[0]

                if already_installed >= total_required_qty:
                    st.error(f"Gagal! {st.session_state.target_comp} sudah mencapai kuota total ({already_installed}/{total_required_qty}).")
                    st.info(f"Struktur membutuhkan {base_qty} unit per {parent_name}.")
                elif selected_sn == "-- Pilih S/N --":
                    st.error("Silahkan pilih Serial Number terlebih dahulu.")
                else:
                    # --- EKSTRAK FINAL PARENT S/N ---
                    if "|" in selected_parent_full:
                        final_p_sn = selected_parent_full.split("| S/N: ")[1].split(" |")[0]
                    else:
                        final_p_sn = "Airframe"

                    # Cek apakah P/N yang dipilih adalah barang yang sudah ditarik (Superseded)
                curr.execute("""
                    SELECT alternate_pn FROM part_interchange 
                    WHERE original_pn = ? AND interchange_type = 'ONE-WAY'
                """, (selected_pn,))
                is_outdated = curr.fetchone()

                if is_outdated:
                    st.warning(f"⚠️ Perhatian: P/N {selected_pn} sebenarnya sudah digantikan oleh {is_outdated[0]}. Pastikan ini sudah sesuai dengan manual.")

                    # --- JALANKAN INSERT ---
                    try:
                        curr.execute("""
                            INSERT INTO installed_components (
                                ac_reg, parent_sn, component_name, position,
                                part_number, serial_number, tsn, csn, tso, cso, dsn, dso, status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'INSTALLED')
                        """, (selected_reg, final_p_sn, st.session_state.target_comp, pos,
                              selected_pn, selected_sn, tsn, csn, tso, cso, dsn, dso))
                        
                        curr.execute("UPDATE master_serial_number SET current_location = 'Aircraft', location = ? WHERE serial_number = ?", 
                                     (selected_reg, selected_sn))
                        
                        conn.commit()
                        st.success(f"Berhasil Terpasang!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Kesalahan Database: {e}")

    # 4. List & Report (Tetap Sama)
    st.subheader(f"📋 Installed Components List - {selected_reg}")
    df_installed = pd.read_sql_query("""
        SELECT position as POS, component_name as NAME, part_number as PN, serial_number as SN, parent_sn as PARENT_SN, tsn as TSN, csn as CSN, id
        FROM installed_components WHERE ac_reg = ?
    """, conn, params=(selected_reg,))
    
    if not df_installed.empty:
        for i, row in df_installed.iterrows():
            r1, r2, r3, r4 = st.columns([1, 4, 2, 1])
            r1.write(f"**{row['POS']}**")
            r2.write(f"{row['NAME']} (PN: {row['PN']} / SN: {row['SN']})")
            r3.write(f"Parent: {row['PARENT_SN']}")
            if r4.button("🗑️", key=f"del_{row['id']}"):
                # 1. Ambil dulu Serial Number yang mau dihapus sebelum datanya hilang
                curr.execute("SELECT serial_number FROM installed_components WHERE id = ?", (row['id'],))
                sn_to_release = curr.fetchone()
    
                if sn_to_release:
                    sn_val = sn_to_release[0]
        
                    # 2. Kembalikan lokasi di Master Serial Number ke HO Store
                    curr.execute("""
                        UPDATE master_serial_number 
                        SET current_location = 'HO Store', location = 'None' 
                        WHERE serial_number = ?
                    """, (sn_val,))
        
                    # 3. Baru hapus data instalasinya
                    curr.execute("DELETE FROM installed_components WHERE id = ?", (row['id'],))
        
                    conn.commit()
                    st.success(f"S/N {sn_val} telah dilepas dan kembali ke HO Store.")
                    st.rerun()
        
    conn.close()
