import sqlite3

def fix_db():
    conn = sqlite3.connect('aircraft.db')
    curr = conn.cursor()
    
    # 1. Pastikan kolom-kolom baru ada di master_part_number
    columns_pn = [("tbo", "REAL"), ("cbo", "INTEGER"), ("dbo", "INTEGER")]
    for col, dtype in columns_pn:
        try:
            curr.execute(f"ALTER TABLE master_part_number ADD COLUMN {col} {dtype}")
            print(f"✅ Kolom {col} ditambahkan ke master_part_number")
        except: pass

    # 2. Pastikan kolom-kolom baru ada di master_serial_number
    columns_sn = [("current_location", "TEXT"), ("location", "TEXT")]
    for col, dtype in columns_sn:
        try:
            curr.execute(f"ALTER TABLE master_serial_number ADD COLUMN {col} {dtype}")
            print(f"✅ Kolom {col} ditambahkan ke master_serial_number")
        except: pass

    # 3. Pastikan tabel grn_log sudah ada
    curr.execute("""
        CREATE TABLE IF NOT EXISTS grn_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grn_number TEXT,
            date_created TEXT,
            part_number TEXT,
            serial_number TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    print("🚀 aircraft.db siap digunakan!")

if __name__ == "__main__":
    fix_db()