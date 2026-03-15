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

# --- FUNGSI GENERATE GRAFIK DENGAN DATA LABELS ---
def create_comparison_chart(title, y_label, last_val, curr_val, year_last, year_now, months_labels):
    fig = go.Figure()
    
    # Bar Tahun Lalu
    fig.add_trace(go.Bar(
        x=months_labels, 
        y=last_val, 
        name=str(year_last), 
        marker_color='#A6ACAF',
        text=last_val, 
        textposition='auto',
    ))
    
    # Bar Tahun Berjalan
    fig.add_trace(go.Bar(
        x=months_labels, 
        y=curr_val, 
        name=str(year_now), 
        marker_color='#2E86C1',
        text=curr_val, 
        textposition='auto',
    ))
    
    fig.update_layout(
        title=title, barmode='group', 
        xaxis_title="Month", yaxis_title=y_label,
        legend_title="Year", uniformtext_minsize=8, uniformtext_mode='hide'
    )
    return fig

# --- MAIN APP ---
st.title("📊 Aircraft Utilization Dashboard")

try:
    df_raw = get_data()

    today = datetime.now()
    first_day_current_month = today.replace(day=1)
    last_month_end = first_day_current_month - timedelta(days=1)
    last_month_start = (last_month_end - timedelta(days=364)).replace(day=1)
    
    year_now = today.year
    year_last = year_now - 1
    months_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # --- 1. UTILIZATION SUMMARY TABLE ---
    st.subheader(f"Utilization Summary ({last_month_start.strftime('%b %Y')} - {last_month_end.strftime('%b %Y')})")
    mask_12m = (df_raw['date'] >= last_month_start) & (df_raw['date'] <= last_month_end)
    df_12m = df_raw.loc[mask_12m].copy()
    df_12m['Month'] = df_12m['date'].dt.strftime('%Y-%m')

    summary_table = df_12m.groupby(['ac_type', 'Month']).agg({
        'flight_hours': 'sum',
        'landings': 'sum'
    }).rename(columns={'landings': 'flight_cycles'}).reset_index()

    st.dataframe(summary_table, use_container_width=True)
    st.markdown("---")

    # --- 2. DROPDOWN SELECTION ---
    all_types = df_raw['ac_type'].unique()
    selected_type = st.selectbox("Pilih Type Pesawat untuk Visualisasi Grafik:", all_types)

    df_type = df_raw[df_raw['ac_type'] == selected_type].copy()
    df_type['Month_Num'] = df_type['date'].dt.month
    df_type['Year'] = df_type['date'].dt.year

    df_plot = df_type.groupby(['Year', 'Month_Num']).agg({'flight_hours':'sum', 'landings':'sum'}).reset_index()

    # Data per bulan dengan pembulatan 2 desimal
    hours_last = [round(df_plot[(df_plot['Year'] == year_last) & (df_plot['Month_Num'] == m)]['flight_hours'].sum(), 2) for m in range(1, 13)]
    hours_curr = [round(df_plot[(df_plot['Year'] == year_now) & (df_plot['Month_Num'] == m)]['flight_hours'].sum(), 2) for m in range(1, 13)]
    cyc_last = [int(df_plot[(df_plot['Year'] == year_last) & (df_plot['Month_Num'] == m)]['landings'].sum()) for m in range(1, 13)]
    cyc_curr = [int(df_plot[(df_plot['Year'] == year_now) & (df_plot['Month_Num'] == m)]['landings'].sum()) for m in range(1, 13)]
    
    ratio_last = [round(h/c, 2) if c > 0 else 0 for h, c in zip(hours_last, cyc_last)]
    ratio_curr = [round(h/c, 2) if c > 0 else 0 for h, c in zip(hours_curr, cyc_curr)]

    # --- DISPLAY GRAFIK A, B, C ---
    tabA, tabB, tabC = st.tabs(["A. Monthly Flight Hours", "B. Monthly Flight Cycles", "C. Ratio Hours/Cycles"])
    
    with tabA:
        st.plotly_chart(create_comparison_chart(f"Flight Hours: {selected_type}", "Hours", hours_last, hours_curr, year_last, year_now, months_labels), use_container_width=True)
    with tabB:
        st.plotly_chart(create_comparison_chart(f"Flight Cycles: {selected_type}", "Cycles", cyc_last, cyc_curr, year_last, year_now, months_labels), use_container_width=True)
    with tabC:
        st.plotly_chart(create_comparison_chart(f"H/C Ratio: {selected_type}", "Ratio", ratio_last, ratio_curr, year_last, year_now, months_labels), use_container_width=True)

    st.markdown("---")

    # --- 3. GRAFIK D & E (FIXED ROUNDING LABELS) ---
    st.subheader(f"Individual Aircraft Performance ({selected_type}) - Year {year_now}")
    df_indiv = df_type[df_type['Year'] == year_now].groupby(['tail_num', 'Month_Num']).agg({'flight_hours':'sum', 'landings':'sum'}).reset_index()

    col_d, col_e = st.columns(2)
    
    with col_d:
        fig_d = go.Figure()
        for tail in df_indiv['tail_num'].unique():
            d_tail = df_indiv[df_indiv['tail_num'] == tail]
            # Pembulatan data jam terbang agar label bersih
            rounded_hours = d_tail['flight_hours'].round(2)
            fig_d.add_trace(go.Scatter(
                x=[months_labels[m-1] for m in d_tail['Month_Num']], 
                y=d_tail['flight_hours'], 
                name=tail, 
                mode='lines+markers+text',
                text=rounded_hours, # Label yang sudah dibulatkan
                textposition="top center"
            ))
        fig_d.update_layout(title="D. Monthly Flight Hours per Tail", yaxis_title="Hours")
        st.plotly_chart(fig_d, use_container_width=True)

    with col_e:
        fig_e = go.Figure()
        for tail in df_indiv['tail_num'].unique():
            d_tail = df_indiv[df_indiv['tail_num'] == tail]
            fig_e.add_trace(go.Scatter(
                x=[months_labels[m-1] for m in d_tail['Month_Num']], 
                y=d_tail['landings'], 
                name=tail, 
                mode='lines+markers+text',
                text=d_tail['landings'],
                textposition="top center"
            ))
        fig_e.update_layout(title="E. Monthly Flight Cycles per Tail", yaxis_title="Cycles")
        st.plotly_chart(fig_e, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")