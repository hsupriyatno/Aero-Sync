import sqlite3
import os

# Memastikan folder db_storage ada
if not os.path.exists('db_storage'):
    os.makedirs('db_storage')

DB_PATH = 'db_storage/aerosynch_main.db'

def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Tabel Utama: Header & Cumulative Totals
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS techlog_main (
            techlog_no TEXT PRIMARY KEY, ac_type TEXT, tail_num TEXT, date DATE,
            sta_dep TEXT, sta_arr TEXT, flight_hours REAL, landings INTEGER,
            total_af_hrs REAL, total_af_ldg INTEGER,
            total_e1_hrs REAL, total_e1_cyc INTEGER,
            total_e2_hrs REAL, total_e2_cyc INTEGER,
            press_alt INTEGER, oat_c INTEGER, ias_kts INTEGER,
            tq REAL, np REAL, t5 REAL, ng REAL, ff REAL,
            oil_temp REAL, oil_press REAL
        )
    ''')
    # Tabel Defects
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS techlog_defects (
            id INTEGER PRIMARY KEY AUTOINCREMENT, techlog_no TEXT, defect_idx INTEGER,
            defect_desc TEXT, rectification TEXT, sta TEXT, lame TEXT,
            FOREIGN KEY (techlog_no) REFERENCES techlog_main (techlog_no)
        )
    ''')
    # Tabel Parts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS techlog_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, techlog_no TEXT, pos TEXT,
            part_desc TEXT, rem_pn TEXT, rem_sn TEXT, ins_pn TEXT, ins_sn TEXT, grn_no TEXT,
            FOREIGN KEY (techlog_no) REFERENCES techlog_main (techlog_no)
        )
    ''')
    conn.commit()
    conn.close()

def get_last_totals(tail_num):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT total_af_hrs, total_af_ldg, total_e1_hrs, total_e1_cyc, total_e2_hrs, total_e2_cyc 
        FROM techlog_main WHERE tail_num = ? ORDER BY date DESC, techlog_no DESC LIMIT 1
    ''', (tail_num,))
    res = cursor.fetchone()
    conn.close()
    return res if res else (0.0, 0, 0.0, 0, 0.0, 0)

def save_complete_techlog(main_data, defects_list, parts_list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO techlog_main VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', main_data)
        if defects_list:
            cursor.executemany('INSERT INTO techlog_defects (techlog_no, defect_idx, defect_desc, rectification, sta, lame) VALUES (?,?,?,?,?,?)', defects_list)
        if parts_list:
            cursor.executemany('INSERT INTO techlog_parts (techlog_no, pos, part_desc, rem_pn, rem_sn, ins_pn, ins_sn, grn_no) VALUES (?,?,?,?,?,?,?,?)', parts_list)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()

def get_full_report():
    conn = sqlite3.connect(DB_PATH)
    import pandas as pd
    df_m = pd.read_sql_query("SELECT * FROM techlog_main", conn)
    df_d = pd.read_sql_query("SELECT * FROM techlog_defects", conn)
    df_p = pd.read_sql_query("SELECT * FROM techlog_parts", conn)
    conn.close()
    return df_m, df_d, df_p

if __name__ == "__main__":
    create_tables()