from database import create_connection

conn = create_connection()
# Baris di bawah ini yang tadi terlewat:
cursor = conn.cursor()

try:
    print("Sedang membuat tabel grn_log...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grn_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grn_number TEXT,
            date_created TEXT,
            part_number TEXT,
            serial_number TEXT
        )
    """)
    conn.commit()
    print("✅ Tabel grn_log berhasil dibuat!")
except Exception as e:
    print(f"❌ Terjadi kesalahan: {e}")
finally:
    conn.close()