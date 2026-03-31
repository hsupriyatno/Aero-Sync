import sqlite3

def create_connection():
    return sqlite3.connect('airfast_erp.db', check_same_thread=False)

def init_db():
    conn = create_connection()
    curr = conn.cursor()
    
    # 1. PARENT: Utilization Record
    curr.execute('''CREATE TABLE IF NOT EXISTS aml_utilization (
        aml_no TEXT PRIMARY KEY,
        ac_type TEXT,
        ac_reg TEXT,
        date TEXT,
        departure TEXT,
        arrival TEXT,
        flight_hours REAL,
        landings INTEGER,
        total_af_hours REAL,
        total_af_landings INTEGER,
        total_e1_hours REAL,
        total_e1_cycles INTEGER,
        total_e2_hours REAL,
        total_e2_cycles INTEGER
    )''')

    # 2. CHILD: Pilot Report
    curr.execute('''CREATE TABLE IF NOT EXISTS aml_pilot_report (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aml_no TEXT,
        defect_id TEXT,
        defect_desc TEXT,
        rectification TEXT,
        station TEXT,
        lame TEXT,
        FOREIGN KEY (aml_no) REFERENCES aml_utilization (aml_no)
    )''')

    # 3. CHILD: Component Replacement
    curr.execute('''CREATE TABLE IF NOT EXISTS aml_component_replacement (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aml_no TEXT,
        pos TEXT,
        part_desc TEXT,
        rem_pn TEXT,
        rem_sn TEXT,
        ins_pn TEXT,
        ins_sn TEXT,
        grn_no TEXT,
        FOREIGN KEY (aml_no) REFERENCES aml_utilization (aml_no)
    )''')

    # 4. CHILD: Engine Parameter
    curr.execute('''CREATE TABLE IF NOT EXISTS aml_engine_param (
        aml_no TEXT PRIMARY KEY,
        press_alt REAL, oat REAL, ias REAL,
        tq1 REAL, np1 REAL, t51 REAL, ng1 REAL, ff1 REAL, ot1 REAL, op1 REAL, oa1 REAL,
        tq2 REAL, np2 REAL, t52 REAL, ng2 REAL, ff2 REAL, ot2 REAL, op2 REAL, oa2 REAL,
        FOREIGN KEY (aml_no) REFERENCES aml_utilization (aml_no)
    )''')

    # 5. MASTER PART NUMBER (Engineering Control)
    curr.execute('''CREATE TABLE IF NOT EXISTS master_part_number (
        part_number TEXT PRIMARY KEY,
        description TEXT,
        ata_chapter TEXT,
        tbo_hours REAL,
        tbo_cycles INTEGER,
        tbo_calendar INTEGER,
        category TEXT, -- HT (Hard Time) or OC (On Condition)
        shelf INTEGER,
        date_registered TEXT
    )''')

    # 6. MASTER SERIAL NUMBER (Store Control)
    curr.execute('''CREATE TABLE IF NOT EXISTS master_serial_number (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        part_number TEXT,
        serial_number TEXT,
        tsn REAL, csn INTEGER, dsn INTEGER,
        tso REAL, cso INTEGER, dso INTEGER,
        status TEXT, -- S (Serviceable) or U (Unserviceable)
        date_registered TEXT,
        UNIQUE(part_number, serial_number),
        FOREIGN KEY (part_number) REFERENCES master_part_number (part_number)
    )''')

    # 7. TRANSACTION (Movement Control)
    curr.execute('''CREATE TABLE IF NOT EXISTS inventory_transaction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        doc_number TEXT,
        part_number TEXT,
        serial_number TEXT,
        store_location TEXT, -- HO, CGK, HLP, etc.
        issued_to TEXT, -- Third Party, Aircraft, or Store
        received_from TEXT, -- Third Party, Aircraft, or Store
        status TEXT,
        remark TEXT,
        FOREIGN KEY (part_number, serial_number) REFERENCES master_serial_number (part_number, serial_number)
    )''')

    conn.commit()
    conn.close()