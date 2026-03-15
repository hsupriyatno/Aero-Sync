import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Tech Log Entry", layout="wide")

# Fungsi mengambil data terakhir untuk kalkulasi otomatis
def get_last_totals(tail_num):
    conn = sqlite3.connect("db_storage/aerosynch_main.db")
    curr = conn.cursor()
    query = """SELECT total_af_hrs, total_af_ldg, total_e1_hrs, total_e1_cyc, total_e2_hrs, total_e2_cyc 
               FROM techlog_main WHERE tail_num = ? ORDER BY id DESC LIMIT 1"""
    curr.execute(query, (tail_num,))
    result = curr.fetchone()
    conn.close()
    return result if result else (0, 0, 0, 0, 0, 0)

def save_to_db(data_tuple, defects, components):
    conn = sqlite3.connect("db_storage/aerosynch_main.db")
    curr = conn.cursor()
    try:
        # 1. Simpan Data Utama
        query_main = '''INSERT INTO techlog_main (
                    techlog_no, ac_type, tail_num, date, departure, arrival, 
                    flight_hours, landings, total_af_hrs, total_af_ldg, 
                    total_e1_hrs, total_e1_cyc, total_e2_hrs, total_e2_cyc,
                    press_alt, oat, ias, 
                    tq1, np1, t51, ng1, ff1, ot1, op1, oa1,
                    tq2, np2, t52, ng2, ff2, ot2, op2, oa2
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
        curr.execute(query_main, data_tuple)
        
        # 2. Simpan Child Defect Record
        for d in defects:
            if d['defect']:
                curr.execute('''INSERT INTO defect_records (techlog_no, defect, corrective_action, sta, lame) 
                               VALUES (?,?,?,?,?)''', (data_tuple[0], d['defect'], d['action'], d['sta'], d['lame']))
        
        # 3. Simpan Child Component Replacement (Multi Record)
        for c in components:
            if c['p_desc']: # Hanya simpan jika Part Description diisi
                curr.execute('''INSERT INTO component_replacement (techlog_no, pos, p_desc, p_off, s_off, p_on, s_on, grn) 
                               VALUES (?,?,?,?,?,?,?,?)''', 
                               (data_tuple[0], c['pos'], c['p_desc'], c['p_off'], c['s_off'], c['p_on'], c['s_on'], c['grn']))
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error Database: {e}")
        return False
    finally:
        conn.close()

st.title("📝 Tech Log Entry System")
st.markdown("---")

# --- BAGIAN 1: IDENTITAS & FLIGHT DATA ---
col1, col2, col3, col4 = st.columns(4)
with col1: t_no = st.text_input("TechLog No.")
with col2: ac_type = st.selectbox("AC Type", ["DHC6-300", "DHC6-400", "B737-MAX", "B412"])
with col3: t_tail = st.text_input("Tail Number").upper()
with col4: date = st.date_input("Date")

col5, col6, col7, col8 = st.columns(4)
with col5: dep = st.text_input("Station Departure")
with col6: arr = st.text_input("Station Arrival")
with col7: fh = st.number_input("Flight Hours (FH)", min_value=0.0, step=0.1)
with col8: ldg = st.number_input("Landings (LDG)", min_value=1, step=1)

# --- BAGIAN 2: AUTO TOTALIZER ---
last_totals = get_last_totals(t_tail)
new_af_hrs, new_af_ldg = last_totals[0] + fh, last_totals[1] + ldg
new_e1_hrs, new_e1_cyc = last_totals[2] + fh, last_totals[3] + ldg
new_e2_hrs, new_e2_cyc = last_totals[4] + fh, last_totals[5] + ldg

st.info(f"Summary for {t_tail if t_tail else 'New Aircraft'}")
t_col1, t_col2, t_col3 = st.columns(3)
with t_col1:
    st.metric("Total Aircraft Hours", f"{new_af_hrs:.2f}", f"+{fh}")
    st.metric("Total Aircraft Landings", f"{new_af_ldg}", f"+{ldg}")
with t_col2:
    st.metric("Total Engine #1 Hours", f"{new_e1_hrs:.2f}")
    st.metric("Total Engine #1 Cycles", f"{new_e1_cyc}")
with t_col3:
    st.metric("Total Engine #2 Hours", f"{new_e2_hrs:.2f}")
    st.metric("Total Engine #2 Cycles", f"{new_e2_cyc}")

st.markdown("---")
with st.form("main_form"):
    # --- CHILD DEFECT RECORD (3 Baris) ---
    st.subheader("⚠️ Defect Record")
    defects_input = []
    for i in range(3):
        dcol1, dcol2, dcol3, dcol4 = st.columns([3, 3, 1, 1])
        with dcol1: d_val = st.text_input(f"Defect {i+1}", key=f"def_{i}")
        with dcol2: a_val = st.text_input(f"Corrective Action {i+1}", key=f"act_{i}")
        with dcol3: s_val = st.text_input(f"STA", key=f"sta_{i}")
        with dcol4: l_val = st.text_input(f"LAME", key=f"lame_{i}")
        defects_input.append({'defect': d_val, 'action': a_val, 'sta': s_val, 'lame': l_val})

    st.markdown("---")
    
    # --- CHILD COMPONENT REPLACEMENT (7 Baris) ---
    st.subheader("🔧 Component Replacement")
    components_input = []
    for j in range(7):
        st.write(f"Component #{j+1}")
        cc1, cc2, cc3, cc4, cc5, cc6, cc7, cc8 = st.columns([0.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1, 1])
        with cc1: c_pos = st.text_input("Pos", key=f"pos_{j}")
        with cc2: c_desc = st.text_input("Part Description", key=f"desc_{j}")
        with cc3: c_poff = st.text_input("P/N OFF", key=f"poff_{j}")
        with cc4: c_soff = st.text_input("S/N OFF", key=f"soff_{j}")
        with cc5: c_pon = st.text_input("P/N ON", key=f"pon_{j}")
        with cc6: c_son = st.text_input("S/N ON", key=f"son_{j}")
        with cc7: c_grn = st.text_input("GRN", key=f"grn_{j}")
        components_input.append({'pos': c_pos, 'p_desc': c_desc, 'p_off': c_poff, 's_off': c_soff, 'p_on': c_pon, 's_on': c_son, 'grn': c_grn})

    st.markdown("---")
    
    # --- ENGINE CRUISE PARAMETERS (ECTM) ---
    st.subheader("🌡️ Engine Cruise Parameters")
    c1, c2, c3 = st.columns(3)
    with c1: p_alt = st.number_input("Pressure Alt (ft)", step=100)
    with c2: oat = st.number_input("OAT (°C)", step=1)
    with c3: ias = st.number_input("IAS (Kts)", step=1)

    st.write("---")
    e1_col, e2_col = st.columns(2)
    with e1_col:
        st.write("**Engine 1 (LH)**")
        tq1, np1, t51, ng1, ff1, ot1, op1, oa1 = [st.number_input(f"{n} 1", step=0.1) for n in ["TQ", "Np", "T5", "Ng", "FF", "OT", "OP", "OA"]]
    with e2_col:
        st.write("**Engine 2 (RH)**")
        tq2, np2, t52, ng2, ff2, ot2, op2, oa2 = [st.number_input(f"{n} 2", step=0.1) for n in ["TQ", "Np", "T5", "Ng", "FF", "OT", "OP", "OA"]]

    submit = st.form_submit_button("SUBMIT ALL DATA TO DATABASE")

if submit:
    data_to_save = (t_no, ac_type, t_tail, str(date), dep, arr, fh, ldg, 
                    new_af_hrs, new_af_ldg, new_e1_hrs, new_e1_cyc, new_e2_hrs, new_e2_cyc,
                    p_alt, oat, ias, tq1, np1, t51, ng1, ff1, ot1, op1, oa1, tq2, np2, t52, ng2, ff2, ot2, op2, oa2)
    
    if save_to_db(data_to_save, defects_input, components_input):
        st.success(f"✅ TechLog {t_no} & All Child Records Berhasil Disimpan!")
        st.balloons()