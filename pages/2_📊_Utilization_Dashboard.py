Siap, Pak Hery! Saya mengerti kendalanya. Kalau dibuka di HP, grafik Plotly bawaannya memang sering "melayang" atau bergeser-geser saat kita mencoba scrolling halaman, karena dia mengira sentuhan jari kita adalah perintah untuk zoom atau pan grafik.

Supaya dashboard AERO-SYNCH Enterprise tetap stabil dan nyaman diakses lewat HP, kita perlu mematikan fitur interaksi sentuh yang tidak perlu (seperti drag untuk zoom) dan mengunci konfigurasi grafiknya.

Berikut adalah kode lengkap dan utuh untuk pages/2_📊_Utilization_Dashboard.py yang sudah saya optimasi agar stabil di HP/Mobile:

Python
import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Utilization Dashboard", layout="wide")

# --- KONEKSI DATABASE ---
def get_data():
    conn = sqlite3.connect("db_storage/aerosynch_main.db")
    query = "SELECT ac_type, tail_num, date, flight_hours, landings FROM techlog_main"
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['date'] = pd.to_datetime(df['date'])
    return df

# --- FUNGSI GRAFIK STABIL (MOBILE FRIENDLY) ---
def create_comparison_chart(title, y_label, last_val, curr_val, year_last, year_now, months_labels):
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=months_labels, y=last_val, name=str(year_last), 
        marker_color='#A6ACAF', text=last_val, textposition='auto'
    ))
    
    fig.add_trace(go.Bar(
        x=months_labels, y=curr_val, name=str(year_now), 
        marker_color='#2E86C1', text=curr_val, textposition='auto'
    ))
    
    fig.update_layout(
        title=title, barmode='group',
        xaxis_title="Month", yaxis_title=y_label,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode="x unified",
        # MENGUNCI GRAFIK AGAR TIDAK GESER SAAT DI-TOUCH DI HP
        dragmode=False 
    )
    
    # KONFIGURASI STATIC (Menghilangkan tombol-tombol zoom yang mengganggu di HP)
    config = {'staticPlot': False, 'scrollZoom': False, 'displayModeBar': False}
    return fig, config

# --- MAIN APP ---
st.title("📊 Aircraft Utilization Dashboard")

try:
    df_raw = get_data()
    today = datetime.now()
    first_day_current_month = today.replace(day=1)
    last_month_end = first_day_current_month - timedelta(days=1)
    last_month_start = (last_month_end - timedelta(days=364)).replace(day=1)
    year_now, year_last = today.year, today.year - 1
    months_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # --- 1. TABLE ---
    st.subheader(f"Utilization Summary ({last_month_start.strftime('%b %Y')} - {last_month_end.strftime('%b %Y')})")
    mask_12m = (df_raw['date'] >= last_month_start) & (df_raw['date'] <= last_month_end)
    df_12m = df_raw.loc[mask_12m].copy()
    df_12m['Month'] = df_12m['date'].dt.strftime('%Y-%m')
    summary_table = df_12m.groupby(['ac_type', 'Month']).agg({'flight_hours': 'sum', 'landings': 'sum'}).reset_index()
    st.dataframe(summary_table, use_container_width=True)

    # --- 2. DROPDOWN ---
    selected_type = st.selectbox("Pilih Type Pesawat:", df_raw['ac_type'].unique())
    df_type = df_raw[df_raw['ac_type'] == selected_type].copy()
    df_type['Month_Num'], df_type['Year'] = df_type['date'].dt.month, df_type['date'].dt.year
    df_plot = df_type.groupby(['Year', 'Month_Num']).agg({'flight_hours':'sum', 'landings':'sum'}).reset_index()

    # Data Processing
    h_last = [round(df_plot[(df_plot['Year'] == year_last) & (df_plot['Month_Num'] == m)]['flight_hours'].sum(), 2) for m in range(1, 13)]
    h_curr = [round(df_plot[(df_plot['Year'] == year_now) & (df_plot['Month_Num'] == m)]['flight_hours'].sum(), 2) for m in range(1, 13)]
    c_last = [int(df_plot[(df_plot['Year'] == year_last) & (df_plot['Month_Num'] == m)]['landings'].sum()) for m in range(1, 13)]
    c_curr = [int(df_plot[(df_plot['Year'] == year_now) & (df_plot['Month_Num'] == m)]['landings'].sum()) for m in range(1, 13)]
    r_last = [round(h/c, 2) if c > 0 else 0 for h, c in zip(h_last, c_last)]
    r_curr = [round(h/c, 2) if c > 0 else 0 for h, c in zip(h_curr, c_curr)]

    # --- DISPLAY GRAFIK A, B, C ---
    tabA, tabB, tabC = st.tabs(["A. Hours", "B. Cycles", "C. Ratio"])
    with tabA:
        f, c = create_comparison_chart(f"Hours: {selected_type}", "Hours", h_last, h_curr, year_last, year_now, months_labels)
        st.plotly_chart(f, config=c, use_container_width=True)
    with tabB:
        f, c = create_comparison_chart(f"Cycles: {selected_type}", "Cycles", c_last, c_curr, year_last, year_now, months_labels)
        st.plotly_chart(f, config=c, use_container_width=True)
    with tabC:
        f, c = create_comparison_chart(f"Ratio: {selected_type}", "Ratio", r_last, r_curr, year_last, year_now, months_labels)
        st.plotly_chart(f, config=c, use_container_width=True)

    # --- 3. GRAFIK D & E (SCATTER STABIL) ---
    st.subheader(f"Tail Performance - {year_now}")
    df_indiv = df_type[df_type['Year'] == year_now].groupby(['tail_num', 'Month_Num']).agg({'flight_hours':'sum', 'landings':'sum'}).reset_index()
    
    col_d, col_e = st.columns(2)
    cfg_mobile = {'displayModeBar': False, 'scrollZoom': False}
    
    with col_d:
        fig_d = go.Figure()
        for tail in df_indiv['tail_num'].unique():
            d_tail = df_indiv[df_indiv['tail_num'] == tail]
            fig_d.add_trace(go.Scatter(x=[months_labels[m-1] for m in d_tail['Month_Num']], y=d_tail['flight_hours'], 
                                       name=tail, mode='lines+markers+text', text=d_tail['flight_hours'].round(1), textposition="top center"))
        fig_d.update_layout(title="D. Hours/Tail", dragmode=False, hovermode="x unified", legend=dict(orientation="h"))
        st.plotly_chart(fig_d, config=cfg_mobile, use_container_width=True)

    with col_e:
        fig_e = go.Figure()
        for tail in df_indiv['tail_num'].unique():
            d_tail = df_indiv[df_indiv['tail_num'] == tail]
            fig_e.add_trace(go.Scatter(x=[months_labels[m-1] for m in d_tail['Month_Num']], y=d_tail['landings'], 
                                       name=tail, mode='lines+markers+text', text=d_tail['landings'], textposition="top center"))
        fig_e.update_layout(title="E. Cycles/Tail", dragmode=False, hovermode="x unified", legend=dict(orientation="h"))
        st.plotly_chart(fig_e, config=cfg_mobile, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")