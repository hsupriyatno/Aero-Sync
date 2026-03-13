import streamlit as st
import pandas as pd
from database_logic import save_complete_techlog, create_tables, get_full_report, get_last_totals
import datetime
import io

# 1. Inisialisasi
create_tables()
st.set_page_config(page_title="TechLog Entry - AERO-SYNCH", layout="wide")
st.title("📄 Technical Log Entry")

# --- SECTION 1: AIRCRAFT & GENERAL ---
with st.container():
    st.subheader("General Information")
    h1, h2, h3, h4 = st.columns(4)
    
    # Menggunakan HTML untuk mewarnai bintang menjadi merah
    ac_type = h1.text_input(label="Aircraft Type :red[*]", placeholder="e.g. DHC6-300")
    tail_num = h2.text_input(label="Tail Number :red[*]", placeholder="e.g. PK-OFI")
    tl_no = h3.text_input(label="TechLog No :red[*]")
    date = h4.date_input(label="Date :red[*]", value=datetime.date.today())

    prev = get_last_totals(tail_num)
    
    c1, c2, c3, c4 = st.columns(4)
    sta_dep = c1.text_input(label="Departure Station :red[*]")
    sta_arr = c2.text_input(label="Arrival Station :red[*]")
    f_hrs = c3.number_input(label="Flight Hours (Now) :red[*]", min_value=0.0, format="%.2f")
    ldg = c4.number_input(label="Landings (Now) :red[*]", min_value=0)

    # Kalkulasi Otomatis
    new_af_hrs, new_af_ldg = prev[0] + f_hrs, prev[1] + ldg
    new_e1_hrs, new_e1_cyc = prev[2] + f_hrs, prev[3] + ldg
    new_e2_hrs, new_e2_cyc = prev[4] + f_hrs, prev[5] + ldg

    res = st.columns(6)
    res[0].metric("Total A/F Hrs", f"{new_af_hrs:.2f}")
    res[1].metric("Total A/F Ldg", new_af_ldg)
    res[2].metric("E1 Total Hrs", f"{new_e1_hrs:.2f}")
    res[3].metric("E1 Total Cyc", new_e1_cyc)
    res[4].metric("E2 Total Hrs", f"{new_e2_hrs:.2f}")
    res[5].metric("E2 Total Cyc", new_e2_cyc)

# --- SECTION 2: ENGINE PARAMETERS ---
with st.expander("🚀 Engine Parameters (Flight Record)", expanded=False):
    e1, e2, e3, e4, e5, e6, e7 = st.columns(7)
    ias = e1.number_input("IAS (KTS)")
    tq = e2.number_input("TQ (%)")
    np = e3.number_input("Np (RPM)")
    t5 = e4.number_input("T5 (°C)")
    ng = e5.number_input("Ng (%)")
    ff = e6.number_input("F/F (PPH)")
    oil_t = e7.number_input("Oil Temp")
    oil_p = e1.number_input("Oil Press", key="op_key")

st.divider()

# --- SECTION 3: DEFECTS & RECTIFICATIONS ---
st.subheader("Defects & Rectifications")
defects_data = []
t1, t2, t3 = st.tabs(["Defect 1", "Defect 2", "Defect 3"])

with t1:
    d1 = st.text_area("Description of Defect 1", key="d1_in")
    r1 = st.text_area("Rectification 1", key="r1_in")
    ca, cb = st.columns(2)
    s1, l1 = ca.text_input("STA 1", key="s1_in"), cb.text_input("LAME 1", key="l1_in")
    if d1: defects_data.append((tl_no, 1, d1, r1, s1, l1))

with t2:
    d2 = st.text_area("Description of Defect 2", key="d2_in")
    r2 = st.text_area("Rectification 2", key="r2_in")
    cc, cd = st.columns(2)
    s2, l2 = cc.text_input("STA 2", key="s2_in"), cd.text_input("LAME 2", key="l2_in")
    if d2: defects_data.append((tl_no, 2, d2, r2, s2, l2))

with t3:
    d3 = st.text_area("Description of Defect 3", key="d3_in")
    r3 = st.text_area("Rectification 3", key="r3_in")
    ce, cf = st.columns(2)
    s3, l3 = ce.text_input("STA 3", key="s3_in"), cf.text_input("LAME 3", key="l3_in")
    if d3: defects_data.append((tl_no, 3, d3, r3, s3, l3))

st.divider()

# --- SECTION 4: PART REPLACEMENT ---
st.subheader("Part Replacement Record")
st.info("Isi tabel di bawah untuk penggantian komponen (Max 7).")

df_template = pd.DataFrame(
    [{"Position": "", "Description": "", "Removed P/N": "", "Removed S/N": "", "Installed P/N": "", "Installed S/N": "", "GRN No": ""} for _ in range(7)]
)

edited_df = st.data_editor(
    df_template, 
    num_rows="fixed", 
    use_container_width=True,
    key="parts_editor_v2"
)

# --- SAVE LOGIC ---
if st.button("SUBMIT TECHLOG", type="primary", use_container_width=True):
    # List pengecekan field wajib
    mandatory_fields = [ac_type, tail_num, tl_no, sta_dep, sta_arr]
    
    # Validasi: Jika ada text field yang kosong atau FH/Ldg masih nol
    if any(not field for field in mandatory_fields) or (f_hrs == 0 and ldg == 0):
        st.error("❌ Mohon lengkapi semua field yang bertanda bintang (*) sebelum Submit!")
    else:
        # Jika semua aman, baru jalankan proses simpan
        m_data = (
            tl_no, ac_type, tail_num, date.isoformat(), sta_dep, sta_arr, 
            f_hrs, ldg, new_af_hrs, new_af_ldg, new_e1_hrs, new_e1_cyc, 
            new_e2_hrs, new_e2_cyc, 0, 0, ias, tq, np, t5, ng, ff, oil_t, oil_p
        )
        
        # (Proses simpan selanjutnya tetap sama seperti sebelumnya...)
        if save_complete_techlog(m_data, defects_data, p_list):
            st.success(f"✅ TechLog {tl_no} berhasil disimpan!")
            st.balloons()
        else:
            st.error("⚠️ Gagal simpan. Pastikan nomor TechLog belum pernah terdaftar.")

# --- DOWNLOAD SECTION ---
st.divider()
if st.button("PREPARE EXCEL REPORT"):
    df_m, df_d, df_p = get_full_report()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_m.to_excel(writer, index=False, sheet_name='Main')
        df_d.to_excel(writer, index=False, sheet_name='Defects')
        df_p.to_excel(writer, index=False, sheet_name='Parts')
    st.download_button("DOWNLOAD EXCEL", output.getvalue(), f"AeroSynch_{date}.xlsx", use_container_width=True)