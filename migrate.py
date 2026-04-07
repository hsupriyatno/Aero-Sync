from database import create_connection

def add_ata_column():
    conn = create_connection()
    curr = conn.cursor()
    try:
        # Perintah untuk menyisipkan kolom ata_chapter ke tabel yang sudah ada
        curr.execute("ALTER TABLE aircraft_structure ADD COLUMN ata_chapter TEXT")
        conn.commit()
        print("Migrasi Berhasil: Kolom 'ata_chapter' telah ditambahkan!")
    except Exception as e:
        print(f"Pesan: {e} (Mungkin kolom sudah ada)")
    finally:
        conn.close()

if __name__ == "__main__":
    add_ata_column()