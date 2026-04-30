import streamlit as st
import pandas as pd
from database import get_current_stock
from database import get_current_stock, save_material_request # Tambahkan ini
import get_current_stock

def show(current_page):
    st.title(f"📦 {current_page}")
    
    # --- LOGIKA CABANG MULAI DI SINI ---
    
    if current_page == "Material Requisition":
        # Perhatikan: tab1, tab2, tab3 harus menjorok ke dalam (di bawah IF)
        tab1, tab2, tab3 = st.tabs(["📊 Stock Monitor", "📝 Create Request", "📑 History"])
    
        with tab1:
            st.subheader("Current Stock Balance")
            try:
                df_stock = get_current_stock()
                if not df_stock.empty:
                    st.dataframe(df_stock, use_container_width=True, hide_index=True)
                else:
                    st.info("Belum ada data transaksi inventory.")
            except Exception as e:
                st.error(f"Error load data: {e}")

        with tab2:
            st.subheader("Create Material Request (MR)")
            with st.form("form_mr"):
                col1, col2 = st.columns(2)
                
                # Kita tambahkan input Aircraft Reg karena di Airfast 
                # request biasanya spesifik untuk satu pesawat (AOG/Routine)
                ac_reg = col1.selectbox("Aircraft Registration", ["PK-OCH", "PK-OFM", "PK-OCA"]) 
                pn = col2.text_input("Part Number") 
                
                priority = col1.selectbox("Priority", ["ROUTINE", "URGENT", "AOG"])
                qty = col2.number_input("Quantity Required", min_value=0.1, step=1.0)
                
                uom = col1.text_input("UOM (EA, LT, KG)")
                remark = st.text_area("Remark / Purpose")
            
                if st.form_submit_button("Submit Material Request"):
                    if pn:
                        # Panggil fungsi simpan
                        success = save_material_request(ac_reg, pn, priority, qty, uom, remark)
                        if success:
                            st.success(f"Material Request untuk {pn} ({ac_reg}) berhasil disimpan!")
                        else:
                            st.error("Gagal menyimpan ke database. Cek koneksi/tabel.")
                    else:
                        st.warning("Part Number tidak boleh kosong.")

        with tab3:
            st.subheader("Recent Requests")
            st.info("History request akan ditampilkan di sini.")

    elif current_page == "Scheduled Removal":
        # Halaman ini tidak pakai tabs, jadi isinya akan beda total
        st.subheader("Forecast Penggantian Komponen (TBO)")
        st.write("Daftar komponen yang mendekati batas waktu penggantian.")
        st.table({"Part Number": ["PN-123", "PN-456"], "Remaining Hours": [50, 120]})

    elif current_page == "Unscheduled Removal Forcasting":
        st.subheader("Analisis Prediksi Kerusakan")
        st.info("Halaman ini menggunakan data MTBUR untuk memprediksi kebutuhan sparepart.")

    elif current_page == "Stock Control":
        st.subheader("Inventory Monitoring")
        st.write("Halaman khusus untuk mengatur Reorder Level (ROL).")

    elif current_page == "Ideal Floating Calculation":
        st.subheader("Perhitungan Safety Stock")
        st.latex(r"SS = Z \times \sigma_d \times \sqrt{L}") 
        st.info("Menghitung jumlah stok ideal.")

    else:
        st.info(f"Halaman {current_page} sedang dalam tahap pengembangan.")
