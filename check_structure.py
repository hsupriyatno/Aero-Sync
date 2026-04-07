import sqlite3
import pandas as pd

conn = sqlite3.connect('airfast_erp.db')
# Cek semua isi tabel struktur
df = pd.read_sql_query("SELECT * FROM aircraft_structure", conn)
print(df)
conn.close()