import streamlit as st
import pandas as pd
from database import create_connection

def show():
    st.header("🔄 Part Interchangeability Management")
    conn = create_connection()
    curr = conn.cursor()

    # --- FORM INPUT ---
    with st.expander("➕ Register New Interchange/Supersede"):
        with st.form("form_interchange"):
            col1, col2 = st.columns(2)
            
            # Ambil daftar P/N dari Master untuk mempermudah input
            df_pn = pd.read_sql("SELECT part_number FROM master_part_number", conn)
            pn_list = df_pn['part_number'].tolist()

            with col1:
                orig_pn = st.selectbox("Original P/N", options=pn_list)
                ic_type = st.selectbox("Interchange Type", 
                                     options=["ONE-WAY", "TWO-WAY"],
                                     help="ONE-WAY: A diganti B (Supersede). TWO-WAY: A & B sama (Interchange).")

            with col2:
                alt_pn = st.selectbox("Alternate/Replacement P/N", options=pn_list)
                remarks = st.text_input("Remarks (e.g., SB Number, AD Ref)")

            submitted = st.form_submit_button("Register Connection")

            if submitted:
                if orig_pn == alt_pn:
                    st.error("P/N asal dan pengganti tidak boleh sama.")
                else:
                    try:
                        curr.execute("""
                            INSERT INTO part_interchange (original_pn, alternate_pn, interchange_type, remarks)
                            VALUES (?, ?, ?, ?)
                        """, (orig_pn, alt_pn, ic_type, remarks))
                        conn.commit()
                        st.success(f"Berhasil mencatat hubungan {orig_pn} -> {alt_pn}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: Hubungan ini mungkin sudah terdaftar. ({e})")

    # --- VIEW & DELETE DATA ---
    st.subheader("📋 Registered Interchange List")
    df_list = pd.read_sql_query("SELECT * FROM part_interchange", conn)
    
    if not df_list.empty:
        # Percantik tampilan tabel
        st.dataframe(df_list, use_container_width=True)
        
        # Opsi Hapus
        with st.expander("🗑️ Delete Connection"):
            to_delete = st.selectbox("Select Connection to Remove", 
                                   options=df_list.apply(lambda x: f"{x['original_pn']} -> {x['alternate_pn']}", axis=1))
            if st.button("Confirm Delete"):
                pns = to_delete.split(" -> ")
                curr.execute("DELETE FROM part_interchange WHERE original_pn = ? AND alternate_pn = ?", (pns[0], pns[1]))
                conn.commit()
                st.success("Hubungan berhasil dihapus.")
                st.rerun()
    else:
        st.info("Belum ada data interchange yang terdaftar.")

    conn.close()