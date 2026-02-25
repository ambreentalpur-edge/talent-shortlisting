import streamlit as st
import os

# --- PAGE CONFIG ---
tab_logo = "logo.jpg"
st.set_page_config(page_title="EdgeOS", page_icon=tab_logo, layout="wide")

# --- BRANDING COLORS ---
brand_plum = "#4a0f70"
text_white = "#f8f9fa"

# --- REFINED CSS FOR CLICKABLE TILES ---
st.markdown(f"""
<style>
    /* Container for the tile to control width */
    .tile-wrapper {{
        position: relative;
        width: 100%;
        max-width: 400px; /* Limits the width of the boxes */
        margin: auto;
    }}

    .card-box {{
        background-color: {brand_plum};
        color: {text_white};
        padding: 25px;
        border-radius: 15px;
        height: 260px;
        transition: transform 0.3s, background-color 0.3s;
        border: 1px solid #320a4d;
        display: flex;
        flex-direction: column;
        justify-content: center;
        text-align: center;
        pointer-events: none; /* Allows the button underneath to catch the click */
    }}

    .tile-wrapper:hover .card-box {{
        transform: translateY(-10px);
        background-color: #5e1a8a;
    }}

    .card-title {{ font-size: 22px; font-weight: bold; margin-bottom: 12px; }}
    .card-text {{ font-size: 15px; line-height: 1.4; opacity: 0.9; }}
    
    /* Transparent button that captures the click */
    .stButton > button {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 260px;
        background: transparent !important;
        color: transparent !important;
        border: none !important;
        z-index: 10;
        cursor: pointer;
    }}
    
    .stButton > button:hover {{
        background: transparent !important;
        color: transparent !important;
        border: none !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- HEADER (LOGO FIX) ---
header_logo = "Edge_Logomark_Plum.jpg"
# Buffers [2, 1, 6, 2] help center the logo and title without stretching them
h_col_l, h_col1, h_col2, h_col_r = st.columns([2, 1, 6, 2])

with h_col1:
    if os.path.exists(header_logo):
        st.image(header_logo, width=120)
    elif os.path.exists(f"../{header_logo}"):
        st.image(f"../{header_logo}", width=120)

with h_col2:
    st.title("Welcome to EdgeOS")
    st.markdown("### *Find fast. Place smarter.*")

st.write("---")

# --- CLICKABLE NAVIGATION TILES (FIXED WIDTH) ---
# [1, 2, 2, 1] creates the centering effect
col_left, col_a, col_b, col_right = st.columns([1, 2, 2, 1])

with col_a:
    st.markdown(f'''
        <div class="tile-wrapper">
            <div class="card-box">
                <div class="card-title">🔍 Talent Database Search</div>
                <div class="card-text">Access your global talent pool. Use the AI Chatbot to filter candidates and update records daily.</div>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    if st.button(" ", key="db_nav"):
        st.switch_page("pages/1_Talent_Database.py")

with col_b:
    st.markdown(f'''
        <div class="tile-wrapper">
            <div class="card-box">
                <div class="card-title">🎯 AI Shortlister</div>
                <div class="card-text">Match candidates against opportunities using GPT-4o logic to find the perfect fit instantly.</div>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    if st.button("  ", key="short_nav"):
        st.switch_page("pages/2_AI_Shortlister.py")
