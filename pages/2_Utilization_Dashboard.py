import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go

st.title("📊 Aircraft Utilization Dashboard")

try:
    # Mengambil data dari database
    conn = sqlite3.connect("db_storage/aerosynch_main.db")
    df = pd.read_sql_query("SELECT ac_type, date as Month, flight_hrs as flight_hours, landings FROM techlog_main", conn)
    conn.close()

    if not df.empty:
        st.subheader("Utilization Summary")
        st.dataframe(df, use_container_width=True)
        
        # Contoh visualisasi sederhana
        fig = go.Figure(data=[go.Bar(x=df['Month'], y=df['flight_hours'])])
        fig.update_layout(title="Total Flight Hours per Month", xaxis_title="Month", yaxis_title="Hours")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Database terdeteksi, namun data masih kosong.")
except Exception as e:
    st.warning("Database belum tersedia atau belum ada record data.")
3. pages/3_Pirep_Marep_History.py
Skrip untuk menampilkan histori laporan defect (Pirep) dan tindakan perbaikan (Marep).

Python
import streamlit as st
import sqlite3
import pandas as pd

st.title("🛠️ Pirep/Marep History")

try:
    conn = sqlite3.connect("db_storage/aerosynch_main.db")
    df = pd.read_sql_query("SELECT date, tail_num, pirep_defect, marep_action FROM techlog_main", conn)
    conn.close()

    if not df.empty:
        # Fitur filter sederhana
        tail_filter = st.selectbox("Filter Tail Number", ["All"] + list(df['tail_num'].unique()))
        
        display_df = df if tail_filter == "All" else df[df['tail_num'] == tail_filter]
        st.table(display_df)
    else:
        st.info("Belum ada data Pirep/Marep yang tercatat.")
except Exception as e:
    st.error(f"Gagal memuat histori: {e}")
