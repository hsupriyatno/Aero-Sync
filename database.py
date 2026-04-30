import sqlite3
import os
import pandas as pd

conn = sqlite3.connect('inventory_system.db') # Sesuaikan nama file DB Bapak
curr = conn.cursor()

# Menambah kolom yang kurang agar tidak error saat INSERT
try:
    curr.execute("ALTER TABLE installed_components ADD COLUMN install_af_hours REAL DEFAULT 0")
    curr.execute("ALTER TABLE installed_components ADD COLUMN install_af_cycles INTEGER DEFAULT 0")
    curr.execute("ALTER TABLE installed_components ADD COLUMN tsn_at_install REAL DEFAULT 0")
    curr.execute("ALTER TABLE installed_components ADD COLUMN csn_at_install INTEGER DEFAULT 0")
    conn.commit()
    print("Kolom database berhasil diperbarui!")
except Exception as e:
    print(f"Catatan: {e}") # Jika kolom sudah ada, abaikan saja

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

    # 8. TRANSACTION (Movement Control / Stock History) - Ditambah Qty & UOM
    curr.execute('''CREATE TABLE IF NOT EXISTS inventory_transaction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT, 
        doc_number TEXT, 
        part_number TEXT, 
        serial_number TEXT,
        quantity REAL DEFAULT 1.0, -- Tambahan Baru
        uom TEXT,                  -- Tambahan Baru (EA, LT, KG, dll)
        store_location TEXT, 
        issued_to TEXT, 
        received_from TEXT, 
        status TEXT, 
        remark TEXT)''')

    # 9. INSTALLED COMPONENTS (Disinkronkan dengan History)
    curr.execute('''CREATE TABLE IF NOT EXISTS installed_components (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ac_reg TEXT, 
        component_name TEXT,
        position TEXT, 
        part_number TEXT, 
        parent_sn TEXT,
    
        -- Simpan data kondisi SAAT PASANG di sini
        install_date TEXT,
        install_af_hours REAL,
        install_af_cycles INTEGER,
        tsn_at_install REAL,      -- TSN komponen saat baru ditempel
        csn_at_install INTEGER,   -- CSN komponen saat baru ditempel
    
        status TEXT DEFAULT 'INSTALLED',
        FOREIGN KEY (ac_reg) REFERENCES catalog (ac_reg))''')

    # 10. COMPONENT REMOVAL HISTORY (Untuk Analisis Reliability)
    curr.execute('''CREATE TABLE IF NOT EXISTS component_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ac_reg TEXT,
        part_number TEXT,
        serial_number TEXT,
        component_name TEXT,
        position TEXT,
    
        -- Data Saat Pasang
        install_date TEXT,
        install_af_hours REAL,
        install_af_cycles INTEGER,
        tsn_at_install REAL,
        csn_at_install INTEGER,
    
        -- Data Saat Copot
        remove_date TEXT,
        remove_af_hours REAL,
        remove_af_cycles INTEGER,
        tsn_at_remove REAL,      -- Kalkulasi otomatis: (rem_af_hrs - ins_af_hrs) + tsn_at_ins
        csn_at_remove INTEGER,
    
        reason_removal TEXT,     -- Scheduled / Unscheduled
        status_at_removal TEXT,  -- Serviceable / Unserviceable
        remark TEXT
    )''')

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
            landings INTEGER,
            ac_tsn REAL,
            ac_csn INTEGER
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
 
    # 17. Tabel Header Paket
    curr.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_packages (
            package_id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_name TEXT NOT NULL,         -- Contoh: 'A1 Inspection'
            ac_type TEXT NOT NULL,              -- Contoh: 'DHC6-400'
            description TEXT
        )
    """)

    # 18. Tabel Detail Isi Paket
    curr.execute("""
        CREATE TABLE IF NOT EXISTS package_task_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_id INTEGER,
            task_id TEXT,                       -- Diambil dari Maintenance Catalog
            FOREIGN KEY (package_id) REFERENCES maintenance_packages(package_id),
            FOREIGN KEY (task_id) REFERENCES maintenance_catalog(task_id)
        )
    """)

# 19. Material Request - Ditambah UOM
    curr.execute("""
        CREATE TABLE IF NOT EXISTS material_request (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_date TEXT,
            priority TEXT,          
            ac_reg TEXT,
            package_id INTEGER,     
            part_number TEXT,
            qty_req REAL,           -- Menggunakan REAL agar bisa input desimal (misal 1.5 Liter)
            uom TEXT,               -- Tambahan Baru
            status TEXT DEFAULT 'PENDING', 
            remark TEXT,
            FOREIGN KEY (part_number) REFERENCES master_part_number (part_number)
        )
    """)

    conn.commit()
    conn.close()

def get_tasks_by_ac_type(ac_type):
    # Gunakan create_connection() agar path database konsisten (Laptop vs Cloud)
    conn = create_connection()
    try:
        # Perhatikan: di tabel maintenance_catalog kolomnya bernama 'aircraft_type'
        query = "SELECT task_id, task_title FROM maintenance_catalog WHERE aircraft_type = ?"
        df = pd.read_sql(query, conn, params=(ac_type,))
        return df
    finally:
        conn.close()

def save_package(package_name, ac_type, selected_tasks):
    """Menyimpan Header Paket dan Detail Task-nya"""
    conn = create_connection()
    try:
        curr = conn.cursor()
        # 1. Simpan Header Paket
        curr.execute("""
            INSERT INTO maintenance_packages (package_name, ac_type) 
            VALUES (?, ?)
        """, (package_name, ac_type))
        
        # Ambil ID paket yang baru saja dibuat
        package_id = curr.lastrowid
        
        # 2. Simpan semua Task yang dipilih ke dalam paket tersebut
        for task_id in selected_tasks:
            curr.execute("""
                INSERT INTO package_task_items (package_id, task_id) 
                VALUES (?, ?)
            """, (package_id, task_id))
            
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving package: {e}")
        return False
    finally:
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

def save_package(package_name, ac_type, selected_tasks):
    conn = create_connection()
    try:
        curr = conn.cursor()
        # 1. Simpan Header
        curr.execute("INSERT INTO maintenance_packages (package_name, ac_type) VALUES (?, ?)", 
                     (package_name, ac_type))
        pkg_id = curr.lastrowid
        
        # 2. Simpan Detail Tasks
        for task_id in selected_tasks:
            curr.execute("INSERT INTO package_task_items (package_id, task_id) VALUES (?, ?)", 
                         (pkg_id, task_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()

def get_all_maintenance_packages():
    conn = create_connection()
    query = """
    SELECT p.package_id, p.package_name, p.ac_type, GROUP_CONCAT(i.task_id, ', ') as tasks
    FROM maintenance_packages p
    LEFT JOIN package_task_items i ON p.package_id = i.package_id
    GROUP BY p.package_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def save_maintenance_package(package_name, ac_type, selected_tasks):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO maintenance_packages (package_name, ac_type) VALUES (?, ?)", 
                       (package_name, ac_type))
        package_id = cursor.lastrowid
        for task_id in selected_tasks:
            cursor.execute("INSERT INTO package_task_items (package_id, task_id) VALUES (?, ?)", 
                           (package_id, task_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()

def delete_maintenance_package(package_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM package_task_items WHERE package_id = ?", (package_id,))
        cursor.execute("DELETE FROM maintenance_packages WHERE package_id = ?", (package_id,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_current_stock():
    conn = create_connection()
    # Hapus 'uom,' dari bagian SELECT dan GROUP BY
    query = """
    SELECT 
        part_number, 
        SUM(CASE WHEN status IN ('RECEIVED', 'IN', 'RETURN') THEN quantity ELSE 0 END) - 
        SUM(CASE WHEN status IN ('ISSUED', 'OUT', 'SCRAP') THEN quantity ELSE 0 END) as balance 
    FROM inventory_transaction 
    GROUP BY part_number
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def save_material_request(ac_reg, pn, priority, qty, uom, remark):
    """Menyimpan permintaan material dari Engineering/Planning ke Database"""
    conn = create_connection()
    try:
        curr = conn.cursor()
        query = """
            INSERT INTO material_request 
            (request_date, ac_reg, part_number, priority, qty_req, uom, remark, status) 
            VALUES (DATE('now'), ?, ?, ?, ?, ?, ?, 'PENDING')
        """
        curr.execute(query, (ac_reg, pn, priority, qty, uom, remark))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving MR: {e}")
        return False
    finally:
        conn.close()

def get_fleet_current_status():
    """Mengambil status TSN/CSN terbaru untuk semua fleet"""
    conn = create_connection()
# Di dalam database.py (fungsi yang mengambil history)
    query = """
        SELECT 
            aml_no, 
            ac_reg, 
            date, 
            flight_hours, 
            landings, 
            OALESCE(ac_tsn, 0) as ac_tsn, 
            COALESCE(ac_csn, 0) as ac_csn 
        FROM aml_utilization 
        ORDER BY date DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df