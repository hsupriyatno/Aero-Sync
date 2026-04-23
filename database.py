import sqlite3
import os
import pandas as pd

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
        tbo_hours REAL, tbo_cycles INTEGER, tbo_calendar INTEGER,
        category TEXT, shelf_life INTEGER, date_registered TEXT)''')

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

    # 10. Tabel untuk Fleet Dashboard (Solusi error: no such table aircraft_status)
    curr.execute("""
        CREATE TABLE IF NOT EXISTS aircraft_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aircraft_type TEXT,
            registration TEXT,
            flight_hours REAL
        )
    """)

    # 11. Tabel untuk Deferred Defect (OPEN/CLOSED)
    curr.execute("""
        CREATE TABLE IF NOT EXISTS deferred_defects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aml_no TEXT,
            ac_reg TEXT,
            description TEXT,
            defect_no TEXT,
            defect_id TEXT,
            category TEXT,
            rectification TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'OPEN'
        )
    """)

    # 12. Tabel untuk Maintenance Schedule
    curr.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_schedule (
            rowid INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT,
            ac_reg TEXT,
            ac_type TEXT,
            task_description TEXT,
            duration_days INTEGER,
            last_done_hours REAL,
            last_done_cycles INTEGER,
            last_done_date TEXT,
            next_due_hours REAL,
            next_due_cycles INTEGER,
            next_due_date TEXT,
            remaining_hours REAL,
            remaining_cycles INTEGER,
            remaining_days INTEGER
        )
    """)

    # 13. Tabel untuk AML Utilization
    curr.execute("""
        CREATE TABLE IF NOT EXISTS aml_utilization (
            aml_no TEXT PRIMARY KEY,
            ac_type TEXT,
            ac_reg TEXT,
            date TEXT,
            departure TEXT,
            arrival TEXT,
            flight_hours REAL,
            landings INTEGER
        )
    """)
    # 14. Tabel untuk AML Pilot Report
    curr.execute("""
        CREATE TABLE IF NOT EXISTS aml_pilot_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aml_no TEXT,
            defect_id TEXT,
            defect_desc TEXT,
            rectification TEXT,
            lame TEXT,
            status TEXT DEFAULT 'OPEN'
        )
    """)
    # 15. Tabel untuk AML Component Replacement
    curr.execute("""
        CREATE TABLE IF NOT EXISTS aml_component_replacement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aml_no TEXT,
            pos TEXT,
            part_desc TEXT,
            rem_pn TEXT,
            rem_sn TEXT,
            ins_pn TEXT,
            ins_sn TEXT,
            grn TEXT,
            rectification TEXT,
            lame TEXT,
            status TEXT DEFAULT 'OPEN'
        )
    """)
    # 16. Tabel untuk Maintenance Catalog
    curr.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aircraft_type TEXT,
            task_id TEXT,
            task_title TEXT,
            task_description TEXT,
            interval_hours REAL,
            interval_cycles INTEGER,
            interval_calendar INTEGER,
            duration_days INTEGER DEFAULT 0  -- Pastikan tidak ada koma di baris terakhir sebelum tutup kurung
        )
    """)
 
    conn.commit()
    conn.close()

def update_aircraft(ac_reg, ac_type, msn, tsn, csn):
    """Update data pesawat berdasarkan Registrasi."""
    conn = create_connection()
    curr = conn.cursor()
    curr.execute("""
        UPDATE catalog 
        SET ac_type=?, msn=?, tsn=?, csn=?
        WHERE ac_reg=?
    """, (ac_type, msn, tsn, csn, ac_reg))
    conn.commit()
    conn.close()

def delete_aircraft(ac_reg):
    """Hapus data pesawat berdasarkan Registrasi."""
    conn = create_connection()
    curr = conn.cursor()
    curr.execute("DELETE FROM catalog WHERE ac_reg=?", (ac_reg,))
    conn.commit()
    conn.close()