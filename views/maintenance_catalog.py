import streamlit as st
import sqlite3

def show():
    st.header("📋 Maintenance Catalog Entry")
    st.write("Gunakan form ini untuk menambahkan master data task maintenance baru ke dalam katalog.")

    # Inisialisasi Database
    db_path = 'aircraft.db' # Pastikan path database sesuai dengan proyek Anda

    with st.form("form_maintenance_catalog", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Aircraft Type bisa diisi manual atau menggunakan selectbox jika datanya sudah ada
            aircraft_type = st.selectbox("Aircraft Type", ["Bell 412", "DHC-6", "B737-8 MAX"])
            task_id = st.text_input("Task ID (Contoh: EMMA-01)")
            task_title = st.text_input("Task Title")
        
        with col2:
            interval_hours = st.number_input("Interval Hours", min_value=0.0, step=0.1)
            interval_cycles = st.number_input("Interval Cycles", min_value=0, step=1)
            interval_calendar = st.number_input("Interval Calendar (Days)", min_value=0, step=1)
            
        task_description = st.text_area("Task Description")

        # Tombol Submit (Mechanical necessity agar data terkirim)
        submit_button = st.form_submit_button("Save to Catalog")

        if submit_button:
            if task_id and task_title:
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Query Insert
                    query = """
                    INSERT INTO maintenance_catalog (
                        aircraft_type, task_id, task_title, task_description, 
                        interval_hours, interval_cycles, interval_calendar
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    cursor.execute(query, (
                        aircraft_type, task_id, task_title, task_description,
                        interval_hours, interval_cycles, interval_calendar
                    ))
                    
                    conn.commit()
                    st.success(f"Task {task_id} berhasil disimpan ke dalam katalog!")
                except sqlite3.Error as e:
                    st.error(f"Gagal menyimpan data: {e}")
                finally:
                    conn.close()
            else:
                st.warning("Mohon isi Task ID dan Task Title sebelum menyimpan.")

    # Bagian bawah: Menampilkan tabel katalog yang sudah ada (Opsional tapi berguna)
    st.divider()
    st.subheader("Existing Catalog Entries")
    try:
        import pandas as pd
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM maintenance_catalog", conn)
        st.dataframe(df, use_container_width=True)
        conn.close()
    except:
        st.info("Katalog masih kosong.")