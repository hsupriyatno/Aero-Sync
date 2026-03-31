import streamlit as st
from database import create_connection
import datetime
import pandas as pd
import io 

def show(page_name):
    # ==========================================
    # HALAMAN: PARTS CATALOG
    # ==========================================
    if page_name == "Parts Catalog":
        st.subheader("📦 Inventory Management: Parts Catalog")
        
        tab_pn, tab_sn = st.tabs(["📑 Master Part Number (Engineering)", "🆔 Master Serial Number (Store)"])

        with tab_pn:
            st.info("Input Part Number baru di sini sebelum mendaftarkan Serial Number.")
            with st.form("form_master_pn"):
                col1, col2 = st.columns(2)
                pn = col1.text_input("Part Number")
                desc = col1.text_input("Description")
                ata = col2.text_input("ATA Chapter")
                cat = col2.selectbox("Category", ["HT", "OC"])
                tbo_h = col1.number_input("TBO Hours", step=0.1)
                tbo_c = col2.number_input("TBO Cycles", step=1.0)
                tbo_cal = col2.number_input("TBO Calendar (Days)", step=1)
                shelf = col1.number_input("Shelf Life (months)", step=1)
                date_reg = col2.date_input("Date Registered", value=datetime.date.today())
                
                if st.form_submit_button("Register New Part Number"):
                    if pn:
                        conn = create_connection()
                        curr = conn.cursor()
                        query = """INSERT INTO master_part_number 
                                   (part_number, description, ata_chapter, category, tbo_hours, tbo_cycles, tbo_calendar, shelf, date_registered) 
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                        curr.execute(query, (pn, desc, ata, cat, tbo_h, tbo_c, tbo_cal, shelf, date_reg))
                        conn.commit()
                        conn.close()
                        st.success(f"P/N {pn} berhasil diregistrasi!")
                        st.rerun()
                    else:
                        st.error("P/N tidak boleh kosong.")

            st.markdown("---")
            st.subheader("📋 Registered Parts List")
            conn = create_connection()
            df_pn = pd.read_sql("SELECT * FROM master_part_number ORDER BY date_registered DESC", conn)
            conn.close()

            if not df_pn.empty:
                st.dataframe(df_pn, use_container_width=True, hide_index=True)
            else:
                st.write("No Part Numbers registered yet.")

        with tab_sn:
            st.info("Serial Number hanya bisa didaftarkan untuk Part Number yang sudah ada.")
            conn = create_connection()
            curr = conn.cursor()
            curr.execute("SELECT part_number FROM master_part_number")
            existing_pn = [row[0] for row in curr.fetchall()]
            conn.close()

            if not existing_pn:
                st.warning("Belum ada Part Number terdaftar. Silakan isi di tab sebelah dulu.")
            else:
                with st.form("form_master_sn"):
                    col_a, col_b = st.columns(2)
                    selected_pn_input = col_a.selectbox("Select Part Number", existing_pn)
                    sn = col_b.text_input("Serial Number")
            
                    c1, c2, c3 = st.columns(3)
                    tsn = c1.number_input("TSN", step=0.1)
                    csn = c2.number_input("CSN", step=0.1)
                    dsn = c3.number_input("DSN", step=0.1)
                    tso = c1.number_input("TSO", step=0.1)
                    cso = c2.number_input("CSO", step=0.1)
                    dso = c3.number_input("DSO", step=0.1)
                    date_registered = c1.date_input("Date Registered", value=datetime.date.today())
                    status = c2.selectbox("Status", ["S", "U"])
                    location = st.text_input("Current Location (Store/Shelf/Bin)", placeholder="Contoh: CGK Store Shelf B2")

                    if st.form_submit_button("Register New Serial Number"):
                        if sn:
                            conn = create_connection()
                            curr = conn.cursor()
                            try:
                                query = """INSERT INTO master_serial_number 
                                           (part_number, serial_number, tsn, csn, dsn, tso, cso, dso, status, location, date_registered) 
                                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                                curr.execute(query, (selected_pn_input, sn, tsn, csn, dsn, tso, cso, dso, status, location, date_registered))
                                conn.commit()
                                st.success(f"S/N {sn} berhasil diregistrasi!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Gagal simpan: {e}")
                            finally:
                                conn.close()
                        else:
                            st.error("S/N harus diisi.")

            st.markdown("---")
            st.subheader("📋 Registered Serial Numbers")
            conn = create_connection()
            df_sn = pd.read_sql("SELECT * FROM master_serial_number", conn)
            conn.close()
            if not df_sn.empty:
                st.dataframe(df_sn, use_container_width=True, hide_index=True)

    # ==========================================
    # HALAMAN: PARTS IN STOCK
    # ==========================================
    elif page_name == "Parts In Stock":
        st.subheader("📦 Store Inventory: Serviceable Parts")
        
        conn = create_connection()
        query = """
            SELECT 
                sn.part_number, 
                pn.description, 
                sn.serial_number, 
                pn.ata_chapter,
                sn.location,
                sn.tsn, 
                sn.csn, 
                sn.status,
                sn.date_registered
            FROM master_serial_number sn
            LEFT JOIN master_part_number pn ON sn.part_number = pn.part_number
            WHERE sn.status = 'S'
            ORDER BY sn.date_registered DESC
        """
        df_stock = pd.read_sql(query, conn)
        conn.close()

        if not df_stock.empty:
            # --- 1. INPUT FILTER (Multiselect) ---
            st.write("🔍 **Filter Data**")
            f1, f2, f3 = st.columns(3)
            selected_pn = f1.multiselect("Part Number", options=df_stock["part_number"].unique())
            selected_desc = f2.multiselect("Description", options=df_stock["description"].unique())
            selected_sn = f3.multiselect("Serial Number", options=df_stock["serial_number"].unique())

            # --- 2. LOGIKA FILTERING ---
            df_filtered = df_stock.copy()
            if selected_pn:
                df_filtered = df_filtered[df_filtered["part_number"].isin(selected_pn)]
            if selected_desc:
                df_filtered = df_filtered[df_filtered["description"].isin(selected_desc)]
            if selected_sn:
                df_filtered = df_filtered[df_filtered["serial_number"].isin(selected_sn)]

            # --- 3. MENAMPILKAN TABEL ---
            st.dataframe(df_filtered, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(df_filtered)} of {len(df_stock)} Serviceable Items")

            # --- 4. TOMBOL DOWNLOAD EXCEL ---
            if not df_filtered.empty:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_filtered.to_excel(writer, index=False, sheet_name='Serviceable_Stock')
                
                st.download_button(
                    label="📥 Download Filtered List to Excel",
                    data=buffer.getvalue(),
                    file_name=f"Serviceable_Stock_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("Belum ada data Serviceable.")

    elif page_name == "Incoming/Outgoing":
        st.subheader("🔁 Stock Mutation: Incoming & Outgoing")
        
        tab_in, tab_out, tab_history = st.tabs(["📥 Incoming (Received)", "📤 Outgoing (Issued)", "📜 Transaction History"])

        # Ambil data Master S/N untuk pilihan
        conn = create_connection()
        df_master_sn = pd.read_sql("SELECT part_number, serial_number, status FROM master_serial_number", conn)
        conn.close()

        # --- TAB 1: INCOMING (Barang Masuk ke Store) ---
        with tab_in:
            with st.form("form_incoming"):
                st.info("Gunakan ini untuk mencatat barang masuk dari Supplier, Vendor Repair, atau Aircraft.")
                c1, c2 = st.columns(2)
                
                # Filter P/N yang ada
                all_pn = df_master_sn["part_number"].unique()
                in_pn = c1.selectbox("Part Number", all_pn, key="in_pn")
                
                # Filter S/N sesuai P/N
                all_sn = df_master_sn[df_master_sn["part_number"] == in_pn]["serial_number"].unique()
                in_sn = c1.selectbox("Serial Number", all_sn, key="in_sn")
                
                in_from = c1.text_input("Received From", placeholder="Contoh: Vendor A, PK-OCK, HLP Store")
                in_loc = c1.selectbox("Store Location (Destination)", ["HO", "CGK", "HLP", "SRG"])
                
                in_doc = c2.text_input("Document Number (GRN/PO/Release)")
                in_date = c2.date_input("Date Received", value=datetime.date.today())
                in_remark = st.text_area("Remark")

                if st.form_submit_button("Submit Incoming"):
                    conn = create_connection()
                    curr = conn.cursor()
                    try:
                        # 1. Insert ke inventory_transaction
                        query_trans = """INSERT INTO inventory_transaction 
                                        (date, doc_number, part_number, serial_number, store_location, received_from, issued_to, status, remark) 
                                        VALUES (?, ?, ?, ?, ?, ?, 'Store', 'S', ?)"""
                        curr.execute(query_trans, (in_date, in_doc, in_pn, in_sn, in_loc, in_from, in_remark))
                        
                        # 2. Update status di master_serial_number menjadi 'S' (Serviceable)
                        curr.execute("UPDATE master_serial_number SET status = 'S' WHERE part_number = ? AND serial_number = ?", (in_pn, in_sn))
                        
                        conn.commit()
                        st.success(f"Success! S/N {in_sn} telah diterima di {in_loc} Store.")
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        conn.close()

        # --- TAB 2: OUTGOING (Barang Keluar dari Store) ---
        with tab_out:
            # Hanya barang Serviceable yang bisa dikeluarkan
            df_serviceable = df_master_sn[df_master_sn["status"] == 'S']
            
            if df_serviceable.empty:
                st.warning("Tidak ada barang dengan status Serviceable (S) di gudang saat ini.")
            else:
                with st.form("form_outgoing"):
                    st.error("Gunakan ini untuk mencatat barang keluar untuk Pemasangan Pesawat atau Kirim Repair.")
                    o1, o2 = st.columns(2)
                    
                    out_sn = o1.selectbox("Select S/N to Issue", df_serviceable["serial_number"].unique())
                    # Auto-get P/N
                    out_pn = df_serviceable[df_serviceable["serial_number"] == out_sn]["part_number"].values[0]
                    o1.text_input("Part Number", value=out_pn, disabled=True)
                    
                    out_to = o2.text_input("Issued To", placeholder="Contoh: PK-OCA, Vendor B, SRG Store")
                    out_loc = o2.selectbox("From Store Location", ["HO", "CGK", "HLP", "SRG"])
                    
                    out_doc = o2.text_input("Document Number (WO/Request/Shipping)")
                    out_date = o2.date_input("Date Issued", value=datetime.date.today())
                    out_remark = st.text_area("Remark Outgoing")

                    if st.form_submit_button("Submit Outgoing"):
                        conn = create_connection()
                        curr = conn.cursor()
                        try:
                            # 1. Insert ke inventory_transaction
                            query_trans = """INSERT INTO inventory_transaction 
                                            (date, doc_number, part_number, serial_number, store_location, received_from, issued_to, status, remark) 
                                            VALUES (?, ?, ?, ?, ?, 'Store', ?, 'U', ?)"""
                            curr.execute(query_trans, (out_date, out_doc, out_pn, out_sn, out_loc, out_to, out_remark))
                            
                            # 2. Update status di master_serial_number menjadi 'U' (Unserviceable/Used)
                            curr.execute("UPDATE master_serial_number SET status = 'U' WHERE part_number = ? AND serial_number = ?", (out_pn, out_sn))
                            
                            conn.commit()
                            st.success(f"Success! S/N {out_sn} telah dikeluarkan untuk {out_to}.")
                        except Exception as e:
                            st.error(f"Error: {e}")
                        finally:
                            conn.close()

        # --- TAB 3: HISTORY ---
        with tab_history:
            st.subheader("Transaction Log")
            conn = create_connection()
            df_history = pd.read_sql("SELECT * FROM inventory_transaction ORDER BY date DESC", conn)
            conn.close()
            
            if not df_history.empty:
                st.dataframe(df_history, use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada riwayat transaksi.")       