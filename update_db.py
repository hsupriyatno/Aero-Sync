import sqlite3
import os

def update_database():
    # Mengarahkan langsung ke file database di root folder
    db_path = 'aircraft.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Error: File {db_path} tidak ditemukan di folder ini!")
        return

    conn = sqlite3.connect(db_path)
    curr = conn.cursor()
    
    # List kolom baru yang harus ditambahkan
    updates = [
        ("master_part_number", "tbo", "REAL"),
        ("master_part_number", "cbo", "INTEGER"),
        ("master_part_number", "dbo", "INTEGER"),
        ("master_serial_number", "current_location", "TEXT"),
        ("master_serial_number", "location", "TEXT")
    ]
    
    for table, column, dtype in updates:
        try:
            curr.execute(f"ALTER TABLE {table} ADD COLUMN {column} {dtype}")
            print(f"✅ Kolom '{column}' berhasil ditambahkan ke tabel '{table}'")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"ℹ️ Kolom '{column}' sudah ada di '{table}'.")
            else:
                print(f"❌ Gagal di {table}.{column}: {e}")

    conn.commit()
    conn.close()
    print("🚀 Database Update Selesai!")

if __name__ == "__main__":
    update_database()