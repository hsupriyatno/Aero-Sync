import sqlite3
import os

def fix_aircraft_database():
    db_path = 'aircraft.db'
    if not os.path.exists(db_path):
        print(f"❌ Error: File {db_path} tidak ditemukan!")
        return

    conn = sqlite3.connect(db_path)
    curr = conn.cursor()
    
    # 1. Pastikan kolom TBO dkk ada di master_part_number
    columns_pn = [("tbo", "REAL"), ("cbo", "INTEGER"), ("dbo", "INTEGER")]
    for col, dtype in columns_pn:
        try:
            curr.execute(f"ALTER TABLE master_part_number ADD COLUMN {col} {dtype}")
            print(f"✅ Kolom {col} ditambahkan ke master_part_number")
        except sqlite3.OperationalError:
            print(f"ℹ️ Kolom {col} sudah ada.")

    # 2. Pastikan kolom lokasi ada di master_serial_number
    columns_sn = [("current_location", "TEXT"), ("location", "TEXT")]
    for col, dtype in columns_sn:
        try:
            curr.execute(f"ALTER TABLE master_serial_number ADD COLUMN {col} {dtype}")
            print(f"✅ Kolom {col} ditambahkan ke master_serial_number")
        except sqlite3.OperationalError:
            print(f"ℹ️ Kolom {col} sudah ada.")

    # 3. Buat tabel grn_log jika belum ada
    curr.execute("""
        CREATE TABLE IF NOT EXISTS grn_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grn_number TEXT,
            date_created TEXT,
            part_number TEXT,
            serial_number TEXT
        )
    """)
    print("✅ Tabel grn_log siap.")

    conn.commit()
    conn.close()
    print("🚀 aircraft.db berhasil diperbarui!")

if __name__ == "__main__":
    fix_aircraft_database()