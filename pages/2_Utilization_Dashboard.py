import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Utilization Dashboard", layout="wide")
st.title("📊 Aircraft Utilization Dashboard")

try:
    conn = sqlite3.connect("db_storage/aerosynch_main.db")
    df = pd.read_sql_query("SELECT * FROM techlog_main", conn)
    conn.close()

    if not df.empty:
        # Menampilkan data summary
        st.subheader("Utilization Summary")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Contoh Grafik Sederhana (Jika kolom tersedia)
        if 'flight_hours' in df.columns:
            fig = go.Figure(data=[go.Bar(x=df['date'], y=df['flight_hours'])])
            fig.update_layout(title="Daily Flight Hours", xaxis_title="Date", yaxis_title="Hours")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Database terhubung, namun belum ada data.")
except Exception as e:
    st.warning(f"Menunggu data atau Database belum siap: {e}")