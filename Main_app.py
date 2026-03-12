import streamlit as st
from streamlit_lottie import st_lottie
import time

# --- 1. CONFIGURATION (Wajib Paling Atas) ---
st.set_page_config(page_title="AERO-SYNCH Enterprise", page_icon="✈️", layout="centered")

# --- 2. LOGIKA LOGIN & SIDEBAR ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Sembunyikan Sidebar jika belum login
if not st.session_state['logged_in']:
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none; }
            [data-testid="stSidebarNav"] { display: none; }
        </style>
    """, unsafe_allow_html=True)

# --- 3. DATA ANIMASI (Langsung di dalam Kode) ---
# Ini adalah animasi pesawat sederhana (Lottie format)
airplane_anim = {
    "v": "5.5.7", "fr": 30, "ip": 0, "op": 60, "w": 200, "h": 200, "nm": "Plane", "ddd": 0,
    "assets": [],
    "layers": [{
        "ddd": 0, "ind": 1, "ty": 4, "nm": "PlaneBody", "sr": 1,
        "ks": {
            "o": {"a": 0, "k": 100},
            "p": {"a": 1, "k": [
                {"t": 0, "s": [-100, 100], "h": 1},
                {"t": 60, "s": [300, 100], "h": 1}
            ]},
            "s": {"a": 0, "k": [100, 100]}
        },
        "shapes": [{
            "ty": "gr", "it": [
                {"ty": "rc", "s": {"a": 0, "k": [50, 15]}, "p": {"a": 0, "k": [0, 0]}, "nm": "Body"},
                {"ty": "fl", "c": {"a": 0, "k": [0.1, 0.5, 0.9, 1]}}
            ]
        }]
    }]
}

# --- 4. TAMPILAN INTERFACE ---
if not st.session_state['logged_in']:
    # Tampilkan Animasi
    st_lottie(airplane_anim, speed=1, height=180, key="login_anim")
    
    st.markdown("<h1 style='text-align: center;'>AERO-SYNCH</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Reliability Management System</p>", unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            with st.form("login_gate"):
                u_id = st.text_input("User ID")
                u_pw = st.text_input("Password", type="password")
                submit = st.form_submit_button("SYSTEM ACCESS", use_container_width=True)
                
                if submit:
                    if u_id == "hery" and u_pw == "airfast123":
                        st.session_state['logged_in'] = True
                        st.success("Access Granted!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid ID or Password.")
else:
    # Tampilan Dashboard Utama
    st.title("🚀 Aero-Synch Management Dashboard")
    st.write(f"Selamat datang kembali, **Pak Hery**!")
    
    st.divider()
    st.info("Sidebar navigasi sekarang sudah muncul. Pilih modul di sebelah kiri.")

    # Tombol Logout di Sidebar
    if st.sidebar.button("Logout System"):
        st.session_state['logged_in'] = False
        st.rerun()