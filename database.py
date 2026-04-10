import sqlite3
import os

import sqlite3
import os

def create_connection():
    # 1. Cek apakah sedang di laptop Bapak (Windows)
    local_path = r"C:\DATA\01. RELIABILITY PROJECT\DATABASE PROJECT\AERO-SYNCH\aircraft.db"
    
    if os.path.exists(os.path.dirname(local_path)):
        # Jika folder C:\DATA... ada, gunakan path tersebut
        db_path = local_path
    else:
        # 2. Jika di Cloud, gunakan folder project saat ini
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "aircraft.db")
    
    # Buat folder jika belum ada (hanya untuk path relatif)
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
    return sqlite3.connect(db_path, check_same_thread=False)

def init_db():
    conn = create_connection()
    curr = conn.cursor()
    
    # --- SEMUA TABEL HARUS DI DALAM SINI ---

    # 1. AIRCRAFT CATALOG (Master Fleet)
    curr.execute('''CREATE TABLE IF NOT EXISTS catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ac_reg TEXT UNIQUE, ac_type TEXT, msn TEXT, 
        tsn REAL, csn INTEGER, 
        tsn_e1 REAL, csn_e1 INTEGER, 
        tsn_e2 REAL, csn_e2 INTEGER, 
        entry_date TEXT)''')

    # 2. AIRCRAFT STRUCTURE
    curr.execute('''CREATE TABLE IF NOT EXISTS aircraft_structure (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ac_type TEXT, parent_component TEXT, sub_component TEXT,
        ata_chapter TEXT, required_qty INTEGER)''')

    # 3. MASTER PART NUMBER
    curr.execute('''CREATE TABLE IF NOT EXISTS master_part_number (
        part_number TEXT PRIMARY KEY, description TEXT, ata_chapter TEXT,
        tbo REAL, cbo INTEGER, dbo INTEGER, 
        category TEXT, shelf INTEGER, date_registered TEXT)''')

    # 4. MASTER SERIAL NUMBER
    curr.execute('''CREATE TABLE IF NOT EXISTS master_serial_number (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        part_number TEXT, serial_number TEXT,
        tsn REAL, csn INTEGER, dsn INTEGER,
        tso REAL, cso INTEGER, dso INTEGER,
        status TEXT, current_location TEXT, location TEXT, date_registered TEXT,
        UNIQUE(part_number, serial_number),
        FOREIGN KEY (part_number) REFERENCES master_part_number (part_number))''')

    # 5. TRANSACTION LOG
    curr.execute('''CREATE TABLE IF NOT EXISTS inventory_transaction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT, doc_number TEXT, part_number TEXT, serial_number TEXT,
        store_location TEXT, issued_to TEXT, received_from TEXT, status TEXT, remark TEXT)''')

    # 6. CHILD: Engine Parameter (Kesehatan Engine)
    curr.execute('''CREATE TABLE IF NOT EXISTS aml_engine_param (
        aml_no TEXT PRIMARY KEY,
        press_alt REAL, oat REAL, ias REAL,
        tq1 REAL, np1 REAL, t51 REAL, ng1 REAL, ff1 REAL, ot1 REAL, op1 REAL, oa1 REAL,
        tq2 REAL, np2 REAL, t52 REAL, ng2 REAL, ff2 REAL, ot2 REAL, op2 REAL, oa2 REAL)''')

    # 7. GRN LOG (Tambahan untuk tracking dokumen masuk)
    curr.execute('''CREATE TABLE IF NOT EXISTS grn_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grn_number TEXT, date_created TEXT, part_number TEXT, serial_number TEXT)''')

    # 8. TRANSACTION (Movement Control / Stock History)
    curr.execute('''CREATE TABLE IF NOT EXISTS inventory_transaction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT, doc_number TEXT, part_number TEXT, serial_number TEXT,
        store_location TEXT, issued_to TEXT, received_from TEXT, status TEXT, remark TEXT)''')

    # 9. INSTALLED COMPONENTS (Apa yang nempel di pesawat saat ini)
    curr.execute('''CREATE TABLE IF NOT EXISTS installed_components (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ac_reg TEXT, parent_sn TEXT, component_name TEXT,
        position TEXT, part_number TEXT, serial_number TEXT,
        tsn REAL, csn INTEGER, tso REAL, cso INTEGER, dsn INTEGER, dso INTEGER,
        status TEXT DEFAULT 'INSTALLED',
        FOREIGN KEY (ac_reg) REFERENCES catalog (ac_reg))''')

    #10. PART INTERCHANGE (Alternatif Part Number dan Interchangeability)

    curr.execute('''CREATE TABLE IF NOT EXISTS part_interchange (
        original_pn TEXT,
        alternate_pn TEXT,
        interchange_type TEXT, -- 'ONE-WAY' atau 'TWO-WAY'
        remarks TEXT,
        PRIMARY KEY (original_pn, alternate_pn)
    )''')

    conn.commit()
    conn.close()
    print("Database AERO-SYNCH (10 Tables) initialized successfully.")