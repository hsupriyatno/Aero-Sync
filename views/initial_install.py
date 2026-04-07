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

    # 2. Ambil Struktur Pesawat (Include ATA Chapter)
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
                curr.execute("SELECT serial_number FROM installed_components WHERE ac_reg = ? AND component_name = ?", 
                             (selected_reg, item['sub_component']))
                already_in = len(curr.fetchall())
                
                # Ambil Parent S/N Terakhir (Display Only)
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

                # Render Box dengan ATA Chapter
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
        with st.form("form_install"):
            st.subheader(f"📝 Install: {st.session_state.target_comp}")
            
            # --- LOGIKA PENENTUAN PARENT ---
            if st.session_state.target_parent.lower() == "airframe":
                parent_options = ["Airframe"]
            else:
                curr.execute("SELECT serial_number, position FROM installed_components WHERE ac_reg = ? AND component_name = ?", 
                             (selected_reg, st.session_state.target_parent))
                p_rows = curr.fetchall()
                parent_options = [f"{r[0]} ({r[1]})" for r in p_rows] if p_rows else ["No Parent Found"]

            sel_parent = st.selectbox("Select Parent S/N", parent_options)
            final_p_sn = sel_parent.split(" (")[0]

            st.divider()
            
            # --- PENGUNCIAN KE MASTER DATA ---
            c1, c2 = st.columns(2)
            
            # Ambil List P/N dari Master
            df_master_pn = pd.read_sql("SELECT part_number, description FROM master_part_number", conn)
            pn_list = df_master_pn['part_number'].tolist()
            
            with c1:
                # User dipaksa pilih P/N yang sudah ada di Master
                selected_pn = st.selectbox("Part Number", options=["-- Pilih P/N --"] + pn_list)
                
                # S/N difilter berdasarkan P/N yang dipilih
                sn_options = []
                if selected_pn != "-- Pilih P/N --":
                    # Hanya S/N yang ada di gudang (Store) yang bisa diinstall
                    query_sn = "SELECT serial_number FROM master_serial_number WHERE part_number = ? AND current_location = 'Store'"
                    df_master_sn = pd.read_sql(query_sn, conn, params=(selected_pn,))
                    sn_options = df_master_sn['serial_number'].tolist()
                
                selected_sn = st.selectbox("Serial Number", options=["-- Pilih S/N --"] + sn_options)
                pos = st.selectbox("Position", ["LH", "RH", "CTR", "NO.1", "NO.2", "ONLY"])

            with c2:
                # Tampilkan Deskripsi Otomatis (Akan masuk ke component_name di database)
                comp_desc = ""
                if selected_pn != "-- Pilih P/N --":
                    comp_desc = df_master_pn[df_master_pn['part_number'] == selected_pn]['description'].values[0]
                
                # Kita tampilkan saja, tidak perlu diinput lagi
                st.info(f"**Component Name:** {comp_desc if comp_desc else 'Pilih P/N dulu'}")
                
                tsn = st.number_input("TSN", step=0.1)
                csn = st.number_input("CSN", step=1)

            # Baris Detail Lainnya
            c3, c4, c5 = st.columns(3)
            with c3:
                tso = st.number_input("TSO", step=0.1)
            with c4:
                cso = st.number_input("CSO", step=1)
            with c5:
                dsn = st.number_input("DSN", step=0.1)

            if st.form_submit_button("Save Installation"):
                if selected_pn != "-- Pilih P/N --" and selected_sn != "-- Pilih S/N --" and final_p_sn != "No Parent Found":
                    # GUNAKAN comp_desc UNTUK MENGISI component_name
                    curr.execute("""
                        INSERT INTO installed_components (
                            ac_reg, parent_sn, component_name, position, 
                            part_number, serial_number, tsn, csn, tso, cso, dsn, dso, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'INSTALLED')
                    """, (selected_reg, final_p_sn, comp_desc, pos, 
                          selected_pn, selected_sn, tsn, csn, tso, cso, dsn, 0.0))
                    
                    # UPDATE MASTER SERIAL NUMBER: Status pindah dari Store ke Aircraft
                    curr.execute("""
                        UPDATE master_serial_number 
                        SET current_location = 'Aircraft', location = ? 
                        WHERE part_number = ? AND serial_number = ?
                    """, (selected_reg, selected_pn, selected_sn))
                    
                    conn.commit()
                    st.success(f"Berhasil: {comp_desc} terpasang di {selected_reg}")
                    st.session_state.show_form = False
                    st.rerun()
                else:
                    st.error("P/N dan S/N wajib dipilih dari Master Data!")

    # 4. List & Report
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
                curr.execute("DELETE FROM installed_components WHERE id = ?", (row['id'],))
                conn.commit()
                st.rerun()
            st.divider()

        # Report Export
        df_report = pd.read_sql_query("""
            SELECT component_name, part_number, serial_number, position, parent_sn, tsn, csn, tso, cso, dsn, dso 
            FROM installed_components WHERE ac_reg = ?
        """, conn, params=(selected_reg,))
        
        report_data = generate_component_report(df_report, selected_reg, selected_type)
        st.download_button(
            label="📄 Export to Excel/PDF Report",
            data=report_data,
            file_name=f"Initial_Status_{selected_reg}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Belum ada komponen yang terdaftar.")

    conn.close()