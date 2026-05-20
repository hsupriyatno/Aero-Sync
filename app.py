import streamlit as st
import sqlite3
import pandas as pd
import io
from database import init_db
import views.dashboard as dashboard
import views.catalog as catalog
import views.maintenance_entry as maintenance_entry
import views.maintenance_status as maintenance_status
import views.material_planning as material_planning
import views.engineering as engineering
import views.inventory as inventory
import views.rcpm as rcpm
import views.procurement as procurement
import datetime
import part_interchange_mgmt  # Import file baru
from views import catalog, initial_install
from views import catalog, structure  # Import file baru

def create_connection():
    db_file = "aircraft.db"  # Sesuaikan dengan nama file DB AERO-SYNCH Bapak
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        st.error(f"Gagal koneksi ke database: {e}")
    return conn

# 1. Konfigurasi Halaman
st.set_page_config(
    page_title="AIRFAST MAINTENANCE APPLICATION",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inisialisasi Database
init_db()

# Inject CSS untuk memperbaiki posisi judul agar tidak hilang
st.markdown("""
    <style>
    /* Menghilangkan padding default Streamlit di bagian atas */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }

    /* Mengatur judul utama agar proporsional */
    .main-title { 
        font-size: 40px !important; 
        font-weight: bold; 
        color: #1E3A8A; 
        margin-top: 0px;
        margin-bottom: 5px;
        padding-top: 0px;
    }
    
    .small-font { font-size:20px !important; font-weight: bold; color: #1E3A8A; }
    .section-font { font-size:16px !important; font-weight: bold; margin-top: 5px; }
    
    /* Tambahan untuk menghilangkan spasi extra dari header default st */
    header[data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
        color: white;
    }
    footer {visibility: hidden;}

    /* ======================================================== */
    /* ---- TRICK BARU: PAKSA GESER GAMBAR PERTAMA DI APP ---- */
    /* ======================================================== */
    [data-testid="stMainBlockContainer"] img {
        margin-left: 25px !important; /* Geser sejauh 25 pixel ke kanan */
    }
    </style>
""", unsafe_allow_html=True)

st.image("LOGO.png", width=250)

# 4. LOGIKA NAVIGASI
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

def update_page(key):
    if st.session_state[key] != "":
        st.session_state.page = st.session_state[key]
        # Tambahkan 'interchange' dan 'mat_plan' ke dalam list reset
        keys_to_reset = ["cat", "maint", "status", "eng", "inv_select", "rcp", "proc", "nav_menu", "interchange", "mat_plan", "database_utility"]
        for k in keys_to_reset:
            if k != key and k in st.session_state:
                st.session_state[k] = ""

def get_index(options, current_page):
    try:
        return options.index(current_page)
    except ValueError:
        return 0

# 5. DEFINISI MENU (Sangat Penting: Harus di atas sebelum dipanggil selectbox)
cat_opts = ["", "Aircraft Catalog", "Aircraft Configuration", "Initial Component Installed", "Maintenance Catalog", "Airworthiness Directives Catalog", "Service Bulletins Catalog"]
maint_opts = ["", "AML Entry", "Maintenance Package / Work Pack", "Update Maintenance Tasks", "AD Compliance Entry", "SB Compliance Entry"]  # Tambahkan opsi untuk AD dan SB compliance
status_opts = ["", "Aircraft Utilization Record", "Component Status", "Airworthiness Directive Status", "Service Bulletin Status"]
eng_opts = ["", "Engineering Order", "Engineering Evaluation", "Deferred Defect"]
inv_opts = ["", "Parts Catalog", "Parts In Stock", "Parts Usage History", "Incoming/Outgoing", "Allotment"]
rcp_opts = ["", "RCPM Dashboard", "Defect Analysis", "Component Analysis", "ECTM", "Oil Consumption Analysis", "ETOPS Requirement"]
proc_opts = ["", "Requisition", "Purchase Order", "Repair Order", "Vendor Management"]
part_interchange_opts = ["", "Part Interchangeability Management"]  # Opsi untuk part interchange
mat_plan_opts = ["", "Scheduled Component Removal", "Unscheduled Removal Forcasting", "Material Requisition", "Stock Control", "Ideal Floating Calculation"]  # Opsi untuk material planning

# Membuat list gabungan untuk fitur "Quick Jump" agar tidak NameError
opsi_menu = ["Dashboard"] + cat_opts + maint_opts + status_opts + eng_opts + inv_opts + rcp_opts + proc_opts + part_interchange_opts + mat_plan_opts
opsi_menu = [opt for opt in opsi_menu if opt != ""] # Buang string kosong

# 2. FUNGSI UTILITY EXCEL (EXPORT/IMPORT)
def show_database_utility_page():
    st.subheader("🛠️ Database Utility: Excel Export & Import")
    st.write("Gunakan fitur ini untuk backup data ke Excel atau memperbarui data secara massal.")
    
    conn = create_connection()
    if not conn:
        return

    try:
        tables_df = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';", conn)
        table_options = tables_df['name'].tolist()
    except:
        table_options = ["master_part_number", "master_serial_number", "inventory_transaction"]

    selected_table = st.selectbox("Pilih Tabel yang Akan Diproses:", options=table_options)
    st.divider()
    
    # --- PROSES DOWNLOAD ---
    st.write(f"### 📥 Download Tabel '{selected_table}' ke Excel")
    try:
        df_current = pd.read_sql(f"SELECT * FROM {selected_table}", conn)
        if not df_current.empty:
            st.dataframe(df_current.head(5), use_container_width=True)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_current.to_excel(writer, index=False, sheet_name=selected_table)
            
            st.download_button(
                label=f"🟢 Download {selected_table}.xlsx",
                data=buffer.getvalue(),
                file_name=f"AEROSYNCH_{selected_table}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning(f"Tabel '{selected_table}' saat ini masih kosong.")
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")

    st.divider()

    # --- PROSES UPLOAD & REPLACE ---
    st.write(f"### 📤 Upload & Replace Tabel '{selected_table}'")
    st.warning("⚠️ PERINGATAN: Mengunggah file ini akan MENGHAPUS seluruh data lama di tabel tersebut dan menggantinya dengan data Excel baru!")

    uploaded_file = st.file_uploader(f"Pilih file Excel untuk menggantikan tabel '{selected_table}'", type=["xlsx"])

    if uploaded_file is not None:
        try:
            df_uploaded = pd.read_excel(uploaded_file)
            st.write("📊 **Pratinjau Data Baru:**")
            st.dataframe(df_uploaded.head(5), use_container_width=True)
            
            if st.button(f"🔴 KONFIRMASI: Timpa Tabel {selected_table} Sekarang", type="primary"):
                # 1. Masukkan data dari Excel ke Database seperti biasa
                df_uploaded.to_sql(selected_table, conn, if_exists='replace', index=False)
                
                # 2. PROSES AMAN: Kita paksa SQLite membuat ulang kolom 'id' yang hilang atau rusak
                cursor = conn.cursor()
                try:
                    # Ambil daftar nama kolom yang baru saja dibuat di database
                    cursor.execute(f"PRAGMA table_info({selected_table})")
                    kolom_db = [row[1] for row in cursor.fetchall()]
                    
                    # Jika kolom 'id' atau 'ID' (huruf kecil/besar) tidak ditemukan di database murni:
                    if 'id' not in kolom_db and 'ID' not in kolom_db:
                        # Buat ulang tabel dengan kolom id AUTOINCREMENT agar halaman lain tidak crash
                        st.info("Menyelaraskan struktur kolom 'id' otomatis untuk system...")
                        
                        # Ambil backup data sementara yang baru diupload
                        df_temp = pd.read_sql(f"SELECT * FROM {selected_table}", conn)
                        
                        # Hapus tabel tiruan tadi
                        cursor.execute(f"DROP TABLE {selected_table}")
                        
                        # Buat tabel murni dengan struktur ID resmi SQLite
                        kolom_lain = ", ".join([f"`{k}` TEXT" for k in df_temp.columns])
                        query_buat_tabel = f"CREATE TABLE {selected_table} (id INTEGER PRIMARY KEY AUTOINCREMENT, {kolom_lain})"
                        cursor.execute(query_buat_tabel)
                        
                        # Masukkan kembali datanya tanpa mengusik kolom id bawaan database
                        df_temp.to_sql(selected_table, conn, if_exists='append', index=False)
                except Exception as ex:
                    st.warning(f"Catatan sistem database: {ex}")
                
                conn.commit()
                st.success(f"✅ Sukses! Data pada tabel '{selected_table}' berhasil diperbarui total.")
                st.balloons()
        except Exception as e:
            st.error(f"Gagal memproses file Excel: {e}")
            
    conn.close()

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
st.sidebar.selectbox("RELIABILITY CONTROL PROGRAM", rcp_opts, index=get_index(rcp_opts, st.session_state.page), key="rcp", on_change=update_page, args=("rcp",))
st.sidebar.selectbox("PROCUREMENT", proc_opts, index=get_index(proc_opts, st.session_state.page), key="proc", on_change=update_page, args=("proc",))
st.sidebar.selectbox("PART INTERCHANGE MGMT", ["", "Part Interchangeability Management"], index=get_index(["", "Part Interchangeability Management"], st.session_state.page), key="interchange", on_change=update_page, args=("interchange",))
st.sidebar.selectbox("MATERIAL PLANNING", mat_plan_opts, index=get_index(mat_plan_opts, st.session_state.page), key="mat_plan", on_change=update_page, args=("mat_plan",))
st.sidebar.selectbox("DATABASE UTILITY", ["", "Database Utility"], index=get_index(["", "Database Utility"], st.session_state.page), key="database_utility", on_change=update_page, args=("database_utility",))

st.sidebar.divider()
# Navigasi Cepat (Sudah tidak akan error opsi_menu lagi)
st.sidebar.selectbox("QUICK JUMP", options=opsi_menu, index=get_index(opsi_menu, st.session_state.page), key="nav_menu", on_change=update_page, args=("nav_menu",))

# 7. ROUTING
page = st.session_state.page

if page == "Dashboard":
    dashboard.show()
elif page == "Initial Component Installed":
    initial_install.show()
elif page == "Aircraft Configuration":
    structure.show(page)
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
elif page in mat_plan_opts:
    material_planning.show(page)
elif page == "Part Interchangeability Management":
    part_interchange_mgmt.show(page)
elif page == "Database Utility":
    show_database_utility_page()
else:
    st.info(f"Halaman '{page}' sedang dalam pengembangan.")

