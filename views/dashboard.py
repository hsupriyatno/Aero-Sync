import streamlit as st

def show():
    st.subheader("📊 Fleet Dashboard")
    st.info("Selamat datang di panel utama. Silakan pilih menu di sidebar.")

def create_connection():
    return sqlite3.connect('airfast_erp.db', check_same_thread=False)

def init_db():
    conn = create_connection()
    curr = conn.cursor() # Baris ini yang sebelumnya terlewat
    
    # Tabel Catalog
    curr.execute('''CREATE TABLE IF NOT EXISTS aircraft_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ac_reg TEXT UNIQUE,
        ac_type TEXT,
        msn TEXT,
        tsn REAL,
        csn INTEGER,
        entry_date TEXT
    )''')

    conn.commit()
    conn.close()