import streamlit as st
from database import init_db
from translations import get_text
import auth
import farmer_dashboard
import admin_dashboard

st.set_page_config(
    page_title="Smart KisanJal",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Noto+Sans+Devanagari:wght@400;600;700&display=swap');

:root {
    --bg:     #f3fbf4;
    --bg2:    #e7f6ea;
    --card:   #ffffff;
    --green:  #43a047;
    --dark:   #2e7d32;
    --text:   #163a2f;
    --muted:  #4a7a5a;
    --border: #c8e3cf;
    --shadow: 0 4px 16px rgba(30,90,50,0.09);
}

/* ── Base backgrounds ── */
html, body, .stApp,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"],
[data-testid="stBottom"],
[data-testid="stHeader"],
[data-testid="stDecoration"],
[data-testid="stToolbar"],
section.main, .main, .block-container {
    background-color: var(--bg) !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}
.stApp {
    background:
        radial-gradient(circle at 10% 8%, #eef9f1 0%, transparent 38%),
        radial-gradient(circle at 95% 92%, #e1f4e7 0%, transparent 28%),
        var(--bg) !important;
}

[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] > div > div {
    background-color: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}

/* ── Typography — targeted only, no wildcard div ── */
p, span, label, h1, h2, h3, h4, h5, h6,
li, a, small, td, th, pre, code,
input, textarea, select, option {
    color: var(--text) !important;
    font-family: 'Poppins', 'Noto Sans Devanagari', sans-serif !important;
}

/* ── Inputs ── */
input, textarea,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background-color: #ffffff !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
input:focus, textarea:focus {
    border-color: var(--green) !important;
    box-shadow: 0 0 0 3px rgba(67,160,71,0.15) !important;
    outline: none !important;
}

/* ── Selects / Dropdowns ── */
[data-baseweb="select"] > div,
[data-baseweb="select"] > div > div {
    background-color: #ffffff !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
[data-baseweb="popover"], [data-baseweb="popover"] div,
[data-baseweb="menu"], [role="listbox"], [role="option"] {
    background-color: #ffffff !important;
    color: var(--text) !important;
}
[role="option"]:hover { background-color: var(--bg2) !important; }

/* ── Default buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #59b66e, #3f9c56) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.6rem 1rem !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    width: 100% !important;
    min-height: 44px !important;
    box-shadow: 0 4px 12px rgba(53,128,67,0.22) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(53,128,67,0.32) !important;
}
.stButton > button p { color: #ffffff !important; margin: 0 !important; }
.stButton { width: 100% !important; }

/* ── File uploader — fix double text ── */
[data-testid="stFileUploadDropzone"] {
    background: #ffffff !important;
    border: 2px dashed var(--border) !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] {
    /* ensure clean single render */
    position: relative !important;
    overflow: hidden !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] div,
[data-testid="stFileUploaderDropzoneInstructions"] span {
    font-size: 0.88rem !important;
    color: var(--muted) !important;
}
[data-testid="stFileUploadDropzone"] button {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-weight: 600 !important;
}
/* Remove phantom pseudo-element text */
[data-testid="stFileUploadDropzone"] button span::before,
[data-testid="stFileUploadDropzone"] button span::after,
[data-testid="stFileUploadDropzone"] button::before,
[data-testid="stFileUploadDropzone"] button::after {
    display: none !important;
    content: none !important;
}
[data-testid="stFileUploadDropzone"] small { color: var(--muted) !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #e9f5ec !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 0.2rem !important;
    gap: 0.25rem !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px !important;
    color: var(--muted) !important;
    font-weight: 600 !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: var(--dark) !important;
    color: #ffffff !important;
}
.stTabs [aria-selected="true"] p { color: #ffffff !important; }

/* ── Expanders — fix garbled / doubled header text ── */
[data-testid="stExpander"] {
    background-color: #ffffff !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
/* Hide phantom duplicate text node */
[data-testid="stExpander"] details summary > div > p:not(:first-child) {
    display: none !important;
}
[data-testid="stExpander"] details summary p {
    color: var(--text) !important;
    font-weight: 600 !important;
    font-family: 'Poppins', sans-serif !important;
}
[data-testid="stExpanderDetails"] {
    background-color: var(--bg2) !important;
    border-top: 1px solid var(--border) !important;
}

/* ── Alerts ── */
[data-testid="stAlert"],
.stAlert, .stSuccess, .stInfo, .stWarning, .stError,
div[data-baseweb="notification"] {
    background-color: #eefaf1 !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
}

/* ── Radio ── */
.stRadio > div { flex-direction: row; gap: 1rem; }
.stRadio > div > label {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    color: var(--text) !important;
}

/* ── Dataframe ── */
.dataframe, [data-testid="stDataFrame"] {
    background: var(--card) !important;
    color: var(--text) !important;
}

/* ── Custom component classes ── */
.hero-container {
    background: linear-gradient(130deg, #f7fff8 0%, #edf9f0 55%, #e4f5e8 100%);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 2.6rem 1.8rem;
    text-align: center;
    margin-bottom: 1.35rem;
    box-shadow: var(--shadow);
}
.hero-title {
    font-size: clamp(2rem,4vw,2.8rem) !important;
    font-weight: 700 !important;
    color: var(--dark) !important;
    margin-bottom: 0.45rem;
}
.hero-subtitle { font-size: 1.05rem; color: var(--muted) !important; }
.kisan-card {
    background: var(--card);
    border: 1px solid var(--border) !important;
    border-radius: 14px;
    padding: 1.15rem;
    margin-bottom: 0.85rem;
    box-shadow: var(--shadow);
    transition: transform 0.2s ease;
}
.kisan-card:hover { transform: translateY(-1px); }
.metric-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
    box-shadow: var(--shadow);
}
.metric-value { font-size: 1.8rem; font-weight: 700; color: var(--green) !important; }
.metric-label { font-size: 0.85rem; color: var(--muted) !important; margin-top: 0.25rem; }
.alert-success { background:#eefaf1; border:1px solid #b7e0c1; border-radius:10px; padding:0.95rem; color:#2f7f44!important; margin:0.5rem 0; }
.alert-info    { background:#edf9ef; border:1px solid #b7e0c1; border-radius:10px; padding:0.95rem; color:#1f5b40!important; margin:0.5rem 0; }
.alert-warning { background:#effaf2; border:1px solid #b7e0c1; border-radius:10px; padding:0.95rem; color:#1f5b40!important; margin:0.5rem 0; }
.green-divider { height:2px; background:linear-gradient(90deg,transparent,var(--green),transparent); margin:1.5rem 0; border:none; }

/* ── India flag top-left pill ── */
#india-flag-topbar {
    position: fixed; top: 0.5rem; left: 1rem; z-index: 99999;
    display: flex; align-items: center; gap: 0.45rem;
    background: rgba(255,255,255,0.96); border: 1px solid var(--border);
    border-radius: 20px; padding: 0.28rem 0.85rem 0.28rem 0.6rem;
    box-shadow: 0 2px 10px rgba(30,90,50,0.12);
    pointer-events: none; user-select: none;
}
#india-flag-topbar .flag-emoji { font-size: 1.25rem; line-height: 1; }
#india-flag-topbar .flag-text  { font-size: 0.75rem; font-weight: 700; color: var(--text) !important; }

/* ── Top-right logout/login button container ──
   The real Streamlit button inside #topbar-btn-container is
   CSS-positioned to the top-right corner. No JS tricks needed. */
#topbar-btn-container {
    position: fixed !important;
    top: 0.52rem !important;
    right: 1.2rem !important;
    z-index: 99999 !important;
    width: auto !important;
}
#topbar-btn-container .stButton {
    width: auto !important;
}
#topbar-btn-container .stButton > button {
    width: auto !important;
    min-width: 110px !important;
    border-radius: 24px !important;
    padding: 0.52rem 1.35rem !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    min-height: 38px !important;
    background: linear-gradient(135deg, #43a047, #2e7d32) !important;
    box-shadow: 0 3px 14px rgba(46,125,50,0.32) !important;
    letter-spacing: 0.01em !important;
}
#topbar-btn-container .stButton > button:hover {
    box-shadow: 0 5px 18px rgba(46,125,50,0.42) !important;
    transform: translateY(-1px) !important;
}

/* ── Brand pill (no button, just label) ── */
#topbar-brand-pill {
    position: fixed; top: 0.52rem; right: 1.2rem; z-index: 99999;
    display: flex; align-items: center; gap: 0.5rem;
    background: linear-gradient(135deg, #43a047, #2e7d32);
    border: none; border-radius: 24px; padding: 0.52rem 1.35rem;
    box-shadow: 0 3px 14px rgba(46,125,50,0.32);
    pointer-events: none; user-select: none;
}
#topbar-brand-pill span { font-size: 0.92rem; font-weight: 700; color: #ffffff !important; }

/* Hide Streamlit chrome */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
.main .block-container { padding-top: 1.5rem; padding-bottom: 2.25rem; max-width: 1200px; }
</style>
""", unsafe_allow_html=True)

init_db()


def _do_logout():
    if st.session_state.get("user_type") == "admin":
        try:
            from database import log_admin_action
            log_admin_action(st.session_state.user_data["username"], "LOGOUT", "Logged out")
        except Exception:
            pass
    for k in ["logged_in", "user_type", "user_data"]:
        st.session_state[k] = None
    st.session_state.logged_in = False
    st.session_state.page = "language_select"
    st.rerun()


def show_topbar():
    logged_in = st.session_state.get("logged_in", False)
    page      = st.session_state.get("page", "language_select")

    # India flag — always shown top-left
    st.markdown("""
    <div id="india-flag-topbar">
        <span class="flag-emoji">&#127470;&#127475;</span>
        <span class="flag-text">India</span>
    </div>""", unsafe_allow_html=True)

    # Top-right: real Streamlit button inside a CSS-fixed container
    if logged_in:
        st.markdown('<div id="topbar-btn-container">', unsafe_allow_html=True)
        if st.button("🚪 Logout", key=f"topbar_logout_{page}"):
            _do_logout()
        st.markdown('</div>', unsafe_allow_html=True)

    elif page not in ("login", "language_select"):
        st.markdown('<div id="topbar-btn-container">', unsafe_allow_html=True)
        if st.button("🔑 Login", key=f"topbar_login_{page}"):
            st.session_state.page = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        # Language select / login pages — show brand pill (non-clickable)
        st.markdown("""
        <div id="topbar-brand-pill">
            <span>&#128167; Smart KisanJal</span>
        </div>""", unsafe_allow_html=True)


def init_session():
    for k, v in {
        'language': None, 'logged_in': False,
        'user_type': None, 'user_data': None,
        'page': 'language_select'
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()
page = st.session_state.page
show_topbar()

# ── Router ────────────────────────────────────────────────────────────────────
if page == 'language_select':
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">&#128167; Smart KisanJal</div>
        <div class="hero-subtitle">Empowering Farmers with Smart Technology</div>
        <div class="hero-subtitle" style="font-family:'Noto Sans Devanagari',sans-serif;margin-top:0.3rem;">
            &#2325;&#2367;&#2360;&#2366;&#2344;&#2379;&#2306; &#2325;&#2379; &#2360;&#2381;&#2350;&#2366;&#2352;&#2381;&#2335;
            &#2340;&#2325;&#2344;&#2368;&#2325; &#2360;&#2375; &#2360;&#2358;&#2325;&#2381;&#2340; &#2348;&#2344;&#2366;&#2344;&#2366;
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "<p style='text-align:center;font-size:1.08rem;color:#4c6f60;margin-bottom:1.6rem;'>"
        "Please select your preferred language / अपनी भाषा चुनें</p>",
        unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        r1c1, r1c2, r1c3 = st.columns(3)
        r2c1, r2c2, r2c3 = st.columns(3)
        for col, label, code in [
            (r1c1, "English",   "en"), (r1c2, "हिंदी",    "hi"), (r1c3, "বাংলা",   "bn"),
            (r2c1, "मराठी",    "mr"), (r2c2, "ગુજરાતી", "gu"), (r2c3, "தமிழ்",  "ta"),
        ]:
            with col:
                if st.button(label, use_container_width=True, key=f"lang_{code}"):
                    st.session_state.language = code
                    st.session_state.page = 'login'
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class='kisan-card' style='text-align:center;'>
            <p style='color:#4f6f61;font-size:0.9rem;margin:0;'>
                Irrigation Planning &nbsp;|&nbsp; Government Schemes &nbsp;|&nbsp; Complaint Management<br>
                सिंचाई योजना &nbsp;|&nbsp; सरकारी योजनाएं &nbsp;|&nbsp; शिकायत प्रबंधन
            </p>
        </div>""", unsafe_allow_html=True)

elif page == 'login':
    auth.show_login_page()

elif page == 'farmer_dashboard':
    farmer_dashboard.show()

elif page == 'admin_dashboard':
    admin_dashboard.show()
