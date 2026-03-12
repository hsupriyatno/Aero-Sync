import sqlite3
import pandas as pd
import os

# Buat folder penyimpanan data otomatis
if not os.path.exists('db_storage'):
    os.makedirs('db_storage')

DB_PATH = 'db_storage/aerosynch_main.db'

# --- DATA ARMADA AIRFAST (Update Terbaru) ---
FLEET_DATA = {
    "BOEING B737-8": ["PK-OFI", "PK-OFM"],
    "DHC6-300": ["PK-OCJ", "PK-OCK", "PK-OCL"],
    "DHC6-400": ["PK-OCF", "PK-OCG", "PK-OCH", "PK-OCI", "PK-OAM"],
    "Mil171": ["PK-OMI", "PK-OMS"],
    "Bell412": ["PK-OCA", "PK-OCD"],
    "AS350B3": ["PK-ODC"]
}

def get_aircraft_types():
    return list(FLEET_DATA.keys())

def get_tail_numbers(ac_type):
    return FLEET_DATA.get(ac_type, [])

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS utilization 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     date TEXT, ac_type TEXT, tail_number TEXT,
                     flight_hours REAL, flight_cycles INTEGER, remarks TEXT)''')
    conn.commit()
    conn.close()

def save_utilization(date, ac_type, tail_no, fh, fc, remarks):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO utilization (date, ac_type, tail_number, flight_hours, flight_cycles, remarks)
                      VALUES (?, ?, ?, ?, ?, ?)''', (date, ac_type, tail_no, fh, fc, remarks))
    conn.commit()
    conn.close()

def get_utilization_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM utilization ORDER BY date DESC", conn)
    conn.close()
    return df

init_db()