import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Pirep/Marep History", layout="wide")
st.title("🛠️ Pirep/Marep History")

try:
    conn = sqlite3.connect("db_storage/aerosynch_main.db")
    # Mengambil kolom defect dan action
    df = pd.read_sql_query("SELECT date, tail_num, pirep_defect, marep_action FROM techlog_main", conn)
    conn.close()

    if not df.empty:
        search = st.text_input("Cari Defect atau Tail Number...")
        if search:
            df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Belum ada histori defect yang tercatat.")
except Exception as e:
    st.error(f"Gagal memuat data: {e}")