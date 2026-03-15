import streamlit as st
import pandas as pd
import sqlite3

st.title("📂 Utilization History")

with st.form("filter_form"):
    col1, col2 = st.columns(2)
    with col1:
        t_type = st.selectbox("Type", ["DHC6-300", "B737-MAX", "B412"])
        t_tail = st.text_input("Tail Number")
    with col2:
        d_range = st.date_input("Periode", [])
    
    submit = st.form_submit_button("PROCESS")

if submit and len(d_range) == 2:
    conn = sqlite3.connect("db_storage/aerosynch_main.db")
    query = f"""SELECT techlog_no, date, flight_hours, landings, 
                total_af_hrs, total_af_ldg, total_e1_hrs, total_e2_cyc 
                FROM techlog_main 
                WHERE ac_type='{t_type}' AND tail_num='{t_tail}'
                AND date BETWEEN '{d_range[0]}' AND '{d_range[1]}'"""
    df = pd.read_sql(query, conn)
    
    # Penamaan Kolom sesuai permintaan Bapak
    df.columns = ['TechLog No.', 'Date', 'Flight Hours', 'Landings', 
                  'Total Flight Hours', 'Total Landings', 
                  'Total #1 Engine Hours', 'Total #2 Engine Cycles']
    
    st.dataframe(df)
    
    # Tombol Export Excel (Membutuhkan openpyxl)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("EXPORT TO EXCEL", csv, "Utilization_History.csv", "text/csv")