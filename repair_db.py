conn = create_connection()
curr = conn.cursor()
try:
    curr.execute("ALTER TABLE aml_pilot_report ADD COLUMN defect_id TEXT")
    conn.commit()
    st.success("Kolom defect_id berhasil ditambahkan!")
except Exception as e:
    st.info(f"Kolom mungkin sudah ada: {e}")
finally:
    conn.close()