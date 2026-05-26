import streamlit as st
import pandas as pd
import sqlite3
from database import create_connection
import io
from datetime import datetime

# --- Fungsi Report Tetap Sama ---
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
        conn.close()
        return

    selected_reg = st.selectbox("Pilih Aircraft Registration", df_fleet['ac_reg'])
    selected_type = df_fleet[df_fleet['ac_reg'] == selected_reg]['ac_type'].values[0]
    st.info(f"Unit: {selected_reg} | Type: {selected_type}")

    # 2. Ambil Struktur Pesawat (Logic Grid)
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

                # Hitung Total Required Berdasarkan Jumlah Parent
                curr.execute("SELECT COUNT(*) FROM installed_components WHERE ac_reg = ? AND component_name = ?", 
                             (selected_reg, item['parent_component']))
                parent_count = curr.fetchone()[0]
                total_required = item['required_qty'] * max(1, parent_count) if not is_layer_1 else item['required_qty']

                # Cek Data Terpasang
                curr.execute("SELECT parent_sn FROM installed_components WHERE ac_reg = ? AND component_name = ?", (selected_reg, item['sub_component']))
                already_in = len(curr.fetchall())
                
                # Display Only untuk Box Info Parent
                curr.execute("SELECT parent_sn FROM installed_components WHERE ac_reg = ? AND component_name = ?", (selected_reg, item['sub_component']))
                p_data = curr.fetchone()
                parent_info = p_data[0] if p_data else "Airframe"

                # Logika Warna Box
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
        main_pn_list = df_master_pn['part_number'].tolist()
        final_pn_options = []

        for pn in main_pn_list:
            final_pn_options.append(pn)
            curr.execute("""
                SELECT alternate_pn, interchange_type FROM part_interchange 
                WHERE original_pn = ?
            """, (pn,))
            rows = curr.fetchall()
            for row in rows:
                alt_pn, ic_type = row
                if alt_pn not in final_pn_options:
                    final_pn_options.append(alt_pn)

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
                install_date = st.date_input("Date of Install", value=datetime.now().date())    
            
            with c2:
                st.success(f"**Component Name:**\n\n{comp_desc}")
                tsn_at_install = st.number_input("TSN at Install", step=0.1)
                csn_at_install = st.number_input("CSN at Install", step=1)
                tso_at_install = st.number_input("TSO at Install", step=0.1)
                cso_at_install = st.number_input("CSO at Install", step=1)
                dsn_at_install = st.number_input("DSN at Install", step=0.1)
                dso_at_install = st.number_input("DSO at Install", step=0.1)
                install_af_hours = st.number_input("Aircraft Hours at Install", step=0.1, help="Jam terbang pesawat saat komponen ini dipasang")
                install_af_cycles = st.number_input("Aircraft Cycles at Install", step=1)

            submitted = st.form_submit_button("Save Installation")

            if submitted:
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
                elif selected_sn == "-- Pilih S/N --":
                    st.error("Silahkan pilih Serial Number terlebih dahulu.")
                else:
                    if "|" in selected_parent_full:
                        final_p_sn = selected_parent_full.split("| S/N: ")[1].split(" |")[0]
                    else:
                        final_p_sn = "Airframe"

                    curr.execute("""
                        SELECT alternate_pn FROM part_interchange 
                        WHERE original_pn = ? AND interchange_type = 'ONE-WAY'
                    """, (selected_pn,))
                    is_outdated = curr.fetchone()

                    if is_outdated:
                        st.warning(f"⚠️ Perhatian: P/N {selected_pn} sebenarnya sudah digantikan oleh {is_outdated[0]}. Pastikan ini sudah sesuai dengan manual.")

                    try:
                        curr.execute("""
                            INSERT INTO installed_components (
                                ac_reg, parent_sn, component_name, position,
                                part_number, serial_number, install_date, 
                                install_af_hours, install_af_cycles,
                                tsn_at_install, csn_at_install, tso_at_install, 
                                cso_at_install, dsn_at_install, dso_at_install, status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'INSTALLED')
                        """, (selected_reg, final_p_sn, st.session_state.target_comp, pos,
                              selected_pn, selected_sn, install_date.strftime('%Y-%m-%d'), 
                              install_af_hours, install_af_cycles,
                              tsn_at_install, csn_at_install, tso_at_install, cso_at_install, dsn_at_install, dso_at_install))
                            
                        curr.execute("UPDATE master_serial_number SET current_location = 'Aircraft', location = ? WHERE serial_number = ?", 
                                     (selected_reg, selected_sn))
                            
                        conn.commit()
                        st.success(f"Berhasil Terpasang!")
                        st.session_state.show_form = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Kesalahan Database: {e}")

# 4. List & Report (DI-FIX LENGKAP DI SINI)
    st.subheader(f"📋 Installed Components List - {selected_reg}")
    
    # Perbaikan Query: Ambil field asli serial_number & install_af_hours, buang koma menggantung
    df_installed = pd.read_sql_query(f"""
        SELECT 
            id, 
            install_date,
            position AS POS, 
            component_name AS NAME, 
            part_number AS PN, 
            serial_number AS SN,
            parent_sn AS PARENT_SN,
            install_af_hours,
            tsn_at_install AS TSN_AT_INSTALL,
            csn_at_install AS CSN_AT_INSTALL,
            tso_at_install AS TSO_AT_INSTALL,
            cso_at_install AS CSO_AT_INSTALL,
            dsn_at_install AS DSN_AT_INSTALL,
            dso_at_install AS DSO_AT_INSTALL
        FROM installed_components 
        WHERE ac_reg = '{selected_reg}'
    """, conn)
    
    if not df_installed.empty:
        # Tambahkan container box scroll biar rapi dan tidak memanjang ke bawah
        with st.container(height=400, border=True):
            for i, row in df_installed.iterrows():
                with st.container():
                    r1, r2, r3, r4 = st.columns([1, 4, 2, 1])
                
                    r1.write(f"**{row['POS']}**")
                
                    # Tampilan Nama, PN, SN, dan Jam Pesawat saat instalasi
                    r2.write(f"**{row['NAME']}** (PN: `{row['PN']}` / SN: `{row['SN']}`)")
                    r2.caption(f"📅 Installed: {row['install_date']} | 🛫 At: {row['install_af_hours']} AF Hrs | ⏱️ Start TSN: {row['TSN_AT_INSTALL']}")
                
                    # Penamaan kolom parent sesuai alias query terbaru
                    r3.write(f"Parent SN: `{row['PARENT_SN']}`")
                
                    # Logika Tombol Delete Menggunakan S/N Asli Komponen Komponen
                    if r4.button("🗑️", key=f"del_{row['id']}"):
                        sn_val = row['SN'] # Langsung ambil dari row dataframe
                        try:
                            # 1. Balikkan status komponen ke gudang utama
                            curr.execute("UPDATE master_serial_number SET current_location = 'HO Store', location = 'None' WHERE serial_number = ?", (sn_val,))
                            # 2. Hapus records instalasi dari database
                            curr.execute("DELETE FROM installed_components WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.success(f"S/N {sn_val} telah dilepas.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal Menghapus: {e}")
                st.divider() 
    else:
        st.info("Belum ada komponen terpasang untuk pesawat ini.")
        
    conn.close()