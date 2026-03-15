import streamlit as st
from streamlit_lottie import st_lottie

# --- CONFIGURATION ---
st.set_page_config(page_title="AERO-SYNCH Enterprise", page_icon="✈️", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- LOGIN INTERFACE ---
if not st.session_state['logged_in']:
    st.markdown("<style>[data-testid='stSidebar'] { display: none; }</style>", unsafe_allow_html=True)
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
    # --- NAVIGASI ---
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
