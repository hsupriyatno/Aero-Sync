import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="Utilization Dashboard", layout="wide")

def get_utilization_data():
    conn = sqlite3.connect("db_storage/aerosynch_main.db")
    query = "SELECT date, tail_num, ac_type, flight_hrs, flight_cyc FROM techlog_main"
    df = pd.read_sql_query(query, conn)
    conn.close()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.strftime('%b')
    return df

st.title("📊 Utilization Dashboard")

try:
    df = get_utilization_data()
    if not df.empty:
        # Menghitung jam terbang per tail per bulan
        monthly_data = df.groupby(['month', 'tail_num'])['flight_hrs'].sum().reset_index()
        
        fig = go.Figure()
        for tail in monthly_data['tail_num'].unique():
            subset = monthly_data[monthly_data['tail_num'] == tail]
            fig.add_trace(go.Scatter(
                x=subset['month'], 
                y=subset['flight_hrs'],
                mode='lines+markers+text',
                name=tail,
                text=subset['flight_hrs'].round(2),
                textposition="top center"
            ))

        fig.update_layout(
            title="Monthly Flight Hours per Tail",
            xaxis_title="Month",
            yaxis_title="Hours",
            dragmode=False, # Stabil untuk HP
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Belum ada data di database.")
except Exception as e:
    st.error(f"Error load data: {e}")
