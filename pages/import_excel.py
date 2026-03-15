import pandas as pd
import sqlite3
import os

def import_to_db(excel_file):
    db_path = "db_storage/aerosynch_main.db"
    
    # 1. Baca Excel
    try:
        df = pd.read_excel(excel_file)
        print(f"✅ Berhasil membaca {len(df)} baris dari Excel.")
    except Exception as e:
        print(f"❌ Gagal membaca Excel: {e}")
        return

    # 2. Koneksi ke Database
    conn = sqlite3.connect(db_path)
    
    try:
        # 3. Masukkan data ke tabel techlog_main
        # if_exists='append' artinya data ditambah ke yang sudah ada
        df.to_sql('techlog_main', conn, if_exists='append', index=False)
        print("🚀 Data berhasil di-import ke Database AERO-SYNCH!")
    except Exception as e:
        print(f"❌ Gagal simpan ke DB: {e}")
        print("Saran: Pastikan nomor TechLog di Excel tidak ada yang duplikat dengan di DB.")
    finally:
        conn.close()

# Jalankan fungsi (Ganti nama file sesuai file Excel Bapak)
if __name__ == "__main__":
    file_target = "import_template.xlsx" 
    if os.path.exists(file_target):
        import_to_db(file_target)
    else:
        print(f"⚠️ File {file_target} tidak ditemukan di folder!")