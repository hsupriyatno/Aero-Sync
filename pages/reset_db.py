import os
import sqlite3

db_path = "db_storage/aerosynch_main.db"

# 1. Hapus database lama agar struktur berubah
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 2. Buat tabel baru TANPA PRIMARY KEY pada techlog_no
# Kita tambahkan 'id' yang otomatis bertambah (AUTOINCREMENT)
cursor.execute('''
    CREATE TABLE techlog_main (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        techlog_no TEXT, 
        ac_type TEXT, tail_num TEXT, date TEXT, 
        departure TEXT, arrival TEXT, 
        flight_hours REAL, landings INTEGER,
        total_af_hrs REAL, total_af_ldg INTEGER,
        total_e1_hrs REAL, total_e1_cyc INTEGER,
        total_e2_hrs REAL, total_e2_cyc INTEGER,
        press_alt INTEGER, oat INTEGER, ias INTEGER,
        tq1 REAL, np1 REAL, t51 REAL, ng1 REAL, ff1 REAL, ot1 REAL, op1 REAL, oa1 REAL,
        tq2 REAL, np2 REAL, t52 REAL, ng2 REAL, ff2 REAL, ot2 REAL, op2 REAL, oa2 REAL
    )
''')
conn.commit()
conn.close()
print("✅ Database sudah di-reset! Sekarang nomor TechLog boleh kembar.")