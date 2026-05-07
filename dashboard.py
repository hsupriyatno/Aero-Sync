import streamlit as st
import pandas as pd
import plotly.express as px
from database import create_connection
import plotly.figure_factory as ff
import datetime

def show():
    current_year = datetime.date.today().year
    st.subheader(f"📊 Fleet Dashboard (Year To Date {current_year})")
    st.caption(f"Year To Date {current_year}")
    
    conn = create_connection()
    
    # --- LOAD DATA UTILIZATION ---
    # Mendapatkan tahun saat ini secara dinamis
    current_year = datetime.date.today().year
    start_of_year = f"{current_year}-01-01"

    # --- LOAD DATA UTILIZATION (YEAR TO DATE) ---
    try:
        # Kita hanya mengambil SUM dari aml_utilization yang tanggalnya >= 1 Jan tahun ini
        query_util = f"""
            SELECT 
                c.ac_reg, 
                c.ac_type as aircraft_type,
                IFNULL(SUM(a.flight_hours), 0) as total_flight_hours,
                IFNULL(SUM(a.landings), 0) as total_landings
            FROM catalog c
            LEFT JOIN aml_utilization a ON c.ac_reg = a.ac_reg 
                AND a.date >= '{start_of_year}'
            GROUP BY c.ac_reg
        """
        df_util = pd.read_sql(query_util, conn)
    except:
        st.write("test")
    finally:
        conn.close()

    # --- LAYOUT KOLOM ATAS (UTILIZATION) ---
    col1, col2 = st.columns(2)

    with col1:
        st.write("#### 1. Aircraft Utilization by Type")
        if not df_util.empty:
            util_type = df_util.groupby('aircraft_type')['total_flight_hours'].sum().reset_index()
            fig1 = px.bar(util_type, x='aircraft_type', y='total_flight_hours', 
                          color='aircraft_type', title="Total FH per Aircraft Type")
            fig1.update_yaxes(range=[0, None], rangemode='nonnegative')
            st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.write("#### 2. Aircraft Utilization by ac_reg")
        if not df_util.empty:
            # Pastikan names='ac_reg' sesuai dengan kolom hasil query SQL di atas
            fig2 = px.pie(df_util, values='total_flight_hours', names='ac_reg', 
                          title="FH Distribution by ac_reg")
            st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # --- SECTION 3: DEFERRED DEFECTS ---
    st.subheader("3. Deferred Defects (Status: OPEN)")
    conn = create_connection()
    try:
        query_dd = "SELECT ac_reg, defect_no, description, rectification, due_date FROM deferred_defects WHERE status = 'OPEN' ORDER BY due_date ASC"
        df_dd = pd.read_sql(query_dd, conn)

        if not df_dd.empty:
            st.dataframe(df_dd, hide_index=True, use_container_width=True)
        else:
            st.success("✅ No Open Deferred Defects. All clear!")
    except:
        st.info("Tabel deferred_defects belum tersedia atau kosong.")
    finally:
        conn.close()

    st.divider()
    show_maintenance_planning()

def show_maintenance_planning():
    st.subheader("4. Short Term Maintenance Scheduled (Gantt Chart)")

    conn = create_connection()
    # 1. UPDATE QUERY: Ambil duration_days dari database
    query = """
    
        SELECT 
            ac_reg as Task, 
            next_due_date as Start, 
            task_id as Resource,
            duration_days as duration_days 
        FROM maintenance_schedule
    """

    df_plan = pd.read_sql(query, conn)
    conn.close()

    if not df_plan.empty:
        # 2. KONVERSI DATA
        df_plan['Start'] = pd.to_datetime(df_plan['Start'])
        
        # 3. LOGIKA DURASI: Jika duration_days 0, set minimal 1 agar tetap muncul bar-nya
        df_plan['duration_days'] = df_plan['duration_days'].apply(lambda x: 1 if x == 0 or x is None else x)
        
        # 4. HITUNG FINISH: Start + Duration
        df_plan['Finish'] = df_plan.apply(lambda row: row['Start'] + pd.Timedelta(days=row['duration_days']), axis=1)
    
        today_dt = pd.to_datetime(datetime.date.today())
        # Filter agar hanya menampilkan jadwal yang belum lewat atau akan datang
        df_filtered = df_plan[df_plan['Finish'] >= today_dt].copy()

        if not df_filtered.empty:
            # Menggunakan ff.create_gantt (Pastikan dataframe punya kolom 'Task', 'Start', 'Finish')
            fig = ff.create_gantt(
                df_filtered, 
                index_col='Resource', 
                show_colorbar=True,
                group_tasks=True,
                showgrid_x=True, 
                showgrid_y=True
            )
            
            today = datetime.date.today()
            # Tampilkan timeline untuk 6 bulan ke depan (180 hari)
            default_end = today + datetime.timedelta(days=180)
            
            fig.update_layout(
                xaxis=dict(type="date", range=[today, default_end], autorange=False),
                xaxis_title="Timeline Perawatan (Based on Duration Days)"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Tidak ada jadwal maintenance aktif di masa depan.")
    else:
        st.info("Belum ada jadwal maintenance yang terdaftar.")