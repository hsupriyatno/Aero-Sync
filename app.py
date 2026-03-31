import streamlit as st
from database import init_db
import views.dashboard as dashboard
import views.catalog as catalog
import views.maintenance_entry as maintenance_entry
import views.maintenance_status as maintenance_status
import views.engineering as engineering
import views.inventory as inventory
import views.rcpm as rcpm
import views.procurement as procurement

st.set_page_config(page_title="AERO-SYNCH ERP", layout="wide")

# 1. Inisialisasi Database
init_db()

# 2. CSS untuk menyembunyikan elemen bawaan Streamlit
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; }
        header { visibility: hidden; }
        [data-testid="stSidebarNav"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

st.title("✈️ Aircraft Engineering Reliability & Planning System (ERP)")

# 3. LOGIKA NAVIGASI
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

def update_page(key):
    # Jika user memilih opsi yang bukan kosong
    if st.session_state[key] != "":
        st.session_state.page = st.session_state[key]
        # Reset selectbox lain ke index 0 agar tidak bentrok
        keys_to_reset = ["cat", "maint", "status", "eng", "inv", "rcp", "proc"]
        for k in keys_to_reset:
            if k != key:
                st.session_state[k] = ""

def get_index(options, current_page):
    try:
        return options.index(current_page)
    except ValueError:
        return 0

# 4. SIDEBAR CUSTOM
st.sidebar.header("MAIN MENU")

# Tombol Dashboard Utama (Dikeluarkan dari dropdown)
if st.sidebar.button("🏠 GLOBAL DASHBOARD", use_container_width=True):
    st.session_state.page = "Dashboard"
    # Reset semua dropdown saat kembali ke Dashboard
    for k in ["cat", "maint", "status", "eng", "inv", "rcp", "proc"]:
        st.session_state[k] = ""

st.sidebar.divider()
st.sidebar.header("NAVIGATION")

# List pilihan menu (Dashboard sudah dihapus dari cat_opts)
cat_opts = ["", "Aircraft Catalog", "Structure Management"]
maint_opts = ["", "AML Entry", "Maintenance Package"]
status_opts = ["", "Aircraft Utilization Record", "Airworthiness Directive Status", "Service Bulletin Status"]
eng_opts = ["", "Engineering Order", "Engineering Evaluation", "Deferred Defect"]
inv_opts = ["", "Parts Catalog", "Parts In Stock", "Parts Usage History", "Incoming/Outgoing", "Allotment"]
rcp_opts = ["", "RCPM Dashboard", "Defect Analysis", "Component Analysis", "ECTM", "Oil Consumption Analysis", "ETOPS Requirement"]
proc_opts = ["", "Requisition", "Purchase Order", "Repair Order", "Vendor Management"]

# Render semua dropdown
st.sidebar.selectbox("CATALOG", cat_opts, index=get_index(cat_opts, st.session_state.page), key="cat", on_change=update_page, args=("cat",))
st.sidebar.selectbox("MAINTENANCE ENTRY", maint_opts, index=get_index(maint_opts, st.session_state.page), key="maint", on_change=update_page, args=("maint",))
st.sidebar.selectbox("MAINTENANCE STATUS", status_opts, index=get_index(status_opts, st.session_state.page), key="status", on_change=update_page, args=("status",))
st.sidebar.selectbox("ENGINEERING", eng_opts, index=get_index(eng_opts, st.session_state.page), key="eng", on_change=update_page, args=("eng",))
st.sidebar.selectbox("INVENTORY", inv_opts, index=get_index(inv_opts, st.session_state.page), key="inv_select", on_change=update_page, args=("inv_select",))
st.sidebar.selectbox("RCPM", rcp_opts, index=get_index(rcp_opts, st.session_state.page), key="rcp", on_change=update_page, args=("rcp",))
st.sidebar.selectbox("PROCUREMENT", proc_opts, index=get_index(proc_opts, st.session_state.page), key="proc", on_change=update_page, args=("proc",))

# 5. ROUTING (Memanggil Modul Berdasarkan Pilihan Spesifik)
page = st.session_state.page

if page == "Dashboard":
    dashboard.show()

elif page in cat_opts:
    catalog.show(page) # Parameter 'page' dikirim agar catalog.py tahu menu mana yang aktif

elif page in maint_opts:
    maintenance_entry.show(page)

elif page in status_opts:
    maintenance_status.show(page)

elif page in eng_opts:
    engineering.show(page)

elif page in inv_opts:
    inventory.show(page)

elif page in rcp_opts:
    rcpm.show(page)

elif page in proc_opts:
    procurement.show(page)

else:
    st.info(f"Halaman '{page}' sedang dalam pengembangan.")
