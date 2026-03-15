import streamlit as st
from streamlit_lottie import st_lottie
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="AERO-SYNCH Enterprise", page_icon="✈️", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- ANIMASI LOGIN ---
airplane_anim = {"v": "5.5.7", "fr": 30, "ip": 0, "op": 60, "w": 200, "h": 200, "nm": "Plane", "ddd": 0, "assets": [], "layers": [{"ddd": 0, "ind": 1, "ty": 4, "nm": "PlaneBody", "sr": 1, "ks": {"o": {"a": 0, "k": 100}, "p": {"a": 1, "k": [{"t": 0, "s": [-100, 100], "h": 1}, {"t": 60, "s": [300, 100], "h": 1}]}, "s": {"a": 0, "k": [100, 100]}}, "shapes": [{"ty": "gr", "it": [{"ty": "rc", "s": {"a": 0, "k": [50, 15]}, "p": {"a": 0, "k": [0, 0]}, "nm": "Body"}, {"ty": "fl", "c": {"a": 0, "k": [0.1, 0.5, 0.9, 1]}}]}]}]}

if not st.session_state['logged_in']:
    st.markdown("<style>[data-testid='stSidebar'] { display: none; }</style>", unsafe_allow_html=True)
    st_lottie(airplane_anim, speed=1, height=180, key="login_anim")
    st.markdown("<h1 style='text-align: center;'>AERO-SYNCH</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_gate"):
            u_id = st.text_input("User ID")
            u_pw = st.text_input("Password", type="password")
            if st.form_submit_button("SYSTEM ACCESS", use_container_width=True):
                if u_id == "hery" and u_pw == "airfast123":
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Invalid ID or Password.")
else:
    # --- DEFINISI NAVIGASI ---
    pages = [
        st.Page("pages/1_📝_Tech_Log_Entry.py", title="Tech Log Entry", icon="📝"),
        st.Page("pages/2_📊_Utilization_Dashboard.py", title="Utilization Dashboard", icon="📊"),
        st.Page("pages/3_🛠️_Pirep_Marep_History.py", title="Pirep/Marep History", icon="🛠️"),
    ]
    
    pg = st.navigation(pages)
    
    if st.sidebar.button("Logout System"):
        st.session_state['logged_in'] = False
        st.rerun()
        
    pg.run()