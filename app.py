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
import datetime

# 1. Konfigurasi Halaman
st.set_page_config(
    page_title="AERO-SYNCH ERP",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inisialisasi Database
init_db()

# 3. CSS Custom
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; }
        header[data-testid="stHeader"] { background-color: rgba(0,0,0,0); z-index: 1; }
        [data-testid="stSidebarNav"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

st.title("✈️ Aircraft Engineering Reliability & Planning System (ERP)")

# 4. LOGIKA NAVIGASI
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

def update_page(key):
    if st.session_state[key] != "":
        st.session_state.page = st.session_state[key]
        # Reset dropdown lain agar tidak sinkron ke pilihan lama
        keys_to_reset = ["cat", "maint", "status", "eng", "inv_select", "rcp", "proc", "nav_menu"]
        for k in keys_to_reset:
            if k != key and k in st.session_state:
                st.session_state[k] = ""

def get_index(options, current_page):
    try:
        return options.index(current_page)
    except ValueError:
        return 0

# 5. DEFINISI MENU (Sangat Penting: Harus di atas sebelum dipanggil selectbox)
cat_opts = ["", "Aircraft Catalog", "Structure Management"]
maint_opts = ["", "AML Entry", "Maintenance Package"]
status_opts = ["", "Aircraft Utilization Record", "Airworthiness Directive Status", "Service Bulletin Status"]
eng_opts = ["", "Engineering Order", "Engineering Evaluation", "Deferred Defect"]
inv_opts = ["", "Parts Catalog", "Parts In Stock", "Parts Usage History", "Incoming/Outgoing", "Allotment"]
rcp_opts = ["", "RCPM Dashboard", "Defect Analysis", "Component Analysis", "ECTM", "Oil Consumption Analysis", "ETOPS Requirement"]
proc_opts = ["", "Requisition", "Purchase Order", "Repair Order", "Vendor Management"]

# Membuat list gabungan untuk fitur "Quick Jump" agar tidak NameError
opsi_menu = ["Dashboard"] + cat_opts + maint_opts + status_opts + eng_opts + inv_opts + rcp_opts + proc_opts
opsi_menu = [opt for opt in opsi_menu if opt != ""] # Buang string kosong

# 6. SIDEBAR CUSTOM
st.sidebar.header("MAIN MENU")

if st.sidebar.button("🏠 GLOBAL DASHBOARD", use_container_width=True):
    st.session_state.page = "Dashboard"

st.sidebar.divider()
st.sidebar.header("NAVIGATION")

# Dropdown Kategori
st.sidebar.selectbox("CATALOG", cat_opts, index=get_index(cat_opts, st.session_state.page), key="cat", on_change=update_page, args=("cat",))
st.sidebar.selectbox("MAINTENANCE ENTRY", maint_opts, index=get_index(maint_opts, st.session_state.page), key="maint", on_change=update_page, args=("maint",))
st.sidebar.selectbox("MAINTENANCE STATUS", status_opts, index=get_index(status_opts, st.session_state.page), key="status", on_change=update_page, args=("status",))
st.sidebar.selectbox("ENGINEERING", eng_opts, index=get_index(eng_opts, st.session_state.page), key="eng", on_change=update_page, args=("eng",))
st.sidebar.selectbox("INVENTORY", inv_opts, index=get_index(inv_opts, st.session_state.page), key="inv_select", on_change=update_page, args=("inv_select",))
st.sidebar.selectbox("RCPM", rcp_opts, index=get_index(rcp_opts, st.session_state.page), key="rcp", on_change=update_page, args=("rcp",))
st.sidebar.selectbox("PROCUREMENT", proc_opts, index=get_index(proc_opts, st.session_state.page), key="proc", on_change=update_page, args=("proc",))

st.sidebar.divider()
# Navigasi Cepat (Sudah tidak akan error opsi_menu lagi)
st.sidebar.selectbox("QUICK JUMP", options=opsi_menu, index=get_index(opsi_menu, st.session_state.page), key="nav_menu", on_change=update_page, args=("nav_menu",))

# 7. ROUTING
page = st.session_state.page

if page == "Dashboard":
    dashboard.show()
elif page in cat_opts:
    catalog.show(page)
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
