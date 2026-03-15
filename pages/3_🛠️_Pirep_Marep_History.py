import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Pirep/Marep History", layout="wide")

def get_defect_data():
    conn = sqlite3.connect("db_storage/aerosynch_main.db")
    query = """
    SELECT date, techlog_no, tail_num, ac_type, ata_chapter, 
           defect_description, action_taken, lame_name 
    FROM techlog_main 
    WHERE defect_description IS NOT NULL AND defect_description != ''
    ORDER BY date DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

st.title("🛠️ Pirep / Marep History")
st.info("Riwayat temuan pilot/teknisi dan tindakan perbaikannya.")

try:
    df_raw = get_defect_data()

    # Filter Sederhana
    tail_list = df_raw['tail_num'].unique()
    selected_tail = st.multiselect("Filter Pesawat:", tail_list)

    df_filtered = df_raw.copy()
    if selected_tail:
        df_filtered = df_filtered[df_filtered['tail_num'].isin(selected_tail)]

    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

except Exception as e:
    st.warning("Belum ada data defect terdeteksi di database.")