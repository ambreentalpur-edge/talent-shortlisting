import streamlit as st
import os

# --- PAGE CONFIG ---
tab_logo = "Edge_Logomark_Plum.jpg"
st.set_page_config(page_title="EdgeOS", page_icon=tab_logo, layout="wide")

# --- BRANDING COLORS ---
brand_plum = "#4a0f70"
text_white = "#f8f9fa"

# --- SIMPLIFIED CLICKABLE CSS ---
st.markdown(f"""
<style>
    .tile-wrapper {{
        position: relative;
        width: 100%;
        max-width: 400px;
        margin: auto;
    }}
    .card-box {{
        background-color: {brand_plum};
        color: {text_white};
        padding: 25px;
        border-radius: 15px;
        height: 260px;
        border: 1px solid #320a4d;
        display: flex;
        flex-direction: column;
        justify-content: center;
        text-align: center;
        pointer-events: none; /* Crucial: lets the click pass to the button */
    }}
    /* The actual Streamlit button made invisible and full-size */
    div.stButton > button {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 260px;
        background: transparent !important;
        color: transparent !important;
        border: none !important;
        z-index: 10;
    }}
</style>
""", unsafe_allow_html=True)

# --- HEADER (LOGO FIX) ---
header_logo = "Edge_Logomark_Plum.jpg"
h_col1, h_col2 = st.columns([1, 6])
with h_col1:
    # Check current dir and parent dir for the logo
    logo_path = header_logo if os.path.exists(header_logo) else f"../{header_logo}"
    if os.path.exists(logo_path):
        st.image(logo_path, width=120)

with h_col2:
    st.title("Welcome to EdgeOS")
    st.markdown("### *Find fast. Place smarter.*")

st.write("---")

# --- NAVIGATION TILES ---
col_left, col_a, col_b, col_right = st.columns([1, 2, 2, 1])

with col_a:
    st.markdown(f'''<div class="tile-wrapper"><div class="card-box">
                <div style="font-size:22px; font-weight:bold;">🔍 Talent Database Search</div>
                <div style="font-size:15px; margin-top:10px;">Access global talent and update records daily.</div>
                </div></div>''', unsafe_allow_html=True)
    # EXACT FILENAME CHECK: Ensure this matches your file in the pages/ folder
    if st.button("Open DB", key="nav_db"):
        st.switch_page("pages/1_Talent_Database.py")

with col_b:
    st.markdown(f'''<div class="tile-wrapper"><div class="card-box">
                <div style="font-size:22px; font-weight:bold;">🎯 AI Shortlister</div>
                <div style="font-size:15px; margin-top:10px;">Match candidates against opportunities instantly.</div>
                </div></div>''', unsafe_allow_html=True)
    # EXACT FILENAME CHECK: Ensure this matches your file in the pages/ folder
    if st.button("Open Short", key="nav_short"):
        st.switch_page("pages/2_AI_Shortlister.py")
