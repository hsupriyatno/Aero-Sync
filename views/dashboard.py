import streamlit as st
import pandas as pd
import plotly.express as px
from database import create_connection

def show():
    st.subheader("📊 Fleet Dashboard")
    
    conn = create_connection()
    
    # --- LOAD DATA (JOIN CATALOG & AML) ---
    try:
        # Mengambil total FH & Cycles: Saldo Catalog + Sum AML_Utilization
        query_util = """
            SELECT 
                c.ac_reg as registration, 
                c.ac_type as aircraft_type,
                (c.tsn + IFNULL(SUM(a.flight_hours), 0)) as total_flight_hours,
                (c.csn + IFNULL(SUM(a.landings), 0)) as total_landings
            FROM catalog c
            LEFT JOIN aml_utilization a ON c.ac_reg = a.ac_reg
            GROUP BY c.ac_reg
        """
        df_util = pd.read_sql(query_util, conn)
        
        # Load data untuk Deferred Defects (HIL/ADD) - dari tabel pilot report yang statusnya OPEN
        # Pastikan tabel aml_pilot_report punya kolom 'status'
        try:
            df_hil = pd.read_sql("SELECT * FROM aml_pilot_report WHERE status = 'OPEN'", conn)
        except:
            # Fallback jika kolom status belum ada
            df_hil = pd.read_sql("SELECT * FROM aml_pilot_report", conn)
        
        # Load data untuk Maintenance Schedule
        df_maint = pd.read_sql("SELECT registration, task_description, due_date FROM maintenance_schedule", conn)
        
    except Exception as e:
        st.error(f"Gagal memuat data dashboard: {e}")
        st.info("Pastikan tabel 'catalog' dan 'aml_utilization' sudah terisi data.")
        return
    finally:
        conn.close()

    # --- LAYOUT KOLOM ATAS (UTILIZATION) ---
    col1, col2 = st.columns(2)

    with col1:
        st.write("#### 1. Aircraft Utilization by Type")
        if not df_util.empty:
            util_type = df_util.groupby('aircraft_type')['total_flight_hours'].sum().reset_index()
            fig1 = px.bar(util_type, x='aircraft_type', y='total_flight_hours', 
                          color='aircraft_type', title="Total FH per Aircraft Type",
                          labels={'total_flight_hours': 'Total Flight Hours'})
            
            # --- PERBAIKAN TOTAL UNTUK MENGHILANGKAN AREA NEGATIF ---
            fig1.update_yaxes(
                range=[0, None],          # Memaksa mulai dari 0
                rangemode='nonnegative',  # Mencegah adanya ruang di bawah 0
                zeroline=True, 
                zerolinewidth=3, 
                zerolinecolor='Black'
            )
            
            fig1.update_layout(showlegend=True)
            
            st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.write("#### 2. Aircraft Utilization by Registration")
        if not df_util.empty:
            fig2 = px.pie(df_util, values='total_flight_hours', names='registration', 
                          title="FH Distribution by Registration")
            st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # --- LAYOUT KOLOM BAWAH (DEFECTS & SCHEDULE) ---
    col3, col4 = st.columns(2)

    with col3:
        st.write("#### 3. Deferred Defects (Status: OPEN)")
        open_count = len(df_hil)
        st.metric(label="Total HIL/ADD Open", value=open_count)
        
        if open_count > 0:
            st.info(f"Terdapat {open_count} temuan (Pilot Report) yang masih OPEN.")
            # Menampilkan list defect singkat
            st.dataframe(df_hil[['aml_no', 'defect_desc']], hide_index=True, use_container_width=True)
        else:
            st.success("✅ Semua defect sudah CLOSED.")

    with col4:
        st.write("#### 4. Short Term Maintenance Scheduled")
        if not df_util.empty:
            registrations = df_util['registration'].unique()
            selected_ac = st.selectbox("Select Registration", registrations)
            
            # Filter maintenance
            maint_filtered = df_maint[df_maint['registration'] == selected_ac]
            
            if not maint_filtered.empty:
                st.dataframe(maint_filtered, hide_index=True, use_container_width=True)
            else:
                st.write(f"Tidak ada jadwal maintenance terdekat untuk **{selected_ac}**")
        else:
            st.write("Data pesawat tidak ditemukan.")