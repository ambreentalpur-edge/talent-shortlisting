import streamlit as st
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="EdgeOS", page_icon="Edge_Logomark_Plum.jpg", layout="wide")

# --- NATIVE BUTTON MUTATION (THE CLICK FIX) ---
st.markdown("""
<style>
    /* This targets Streamlit's native buttons and turns them into large Plum cards */
    div.stButton > button {
        background-color: #4a0f70 !important;
        color: white !important;
        height: 220px; /* Makes the box tall */
        width: 100%;
        border-radius: 12px;
        border: none !important;
        white-space: normal !important; /* Forces the description text to wrap */
        padding: 20px !important;
        font-size: 18px !important;
        line-height: 1.5 !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #5e1a8a !important;
        transform: translateY(-5px);
        box-shadow: 0px 8px 15px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
header_logo = "Edge_Logomark_Plum.jpg"
h_col1, h_col2 = st.columns([1, 6])
with h_col1:
    # Looks for logo. If you just uploaded it to GitHub, ensure it is spelled exactly like this.
    if os.path.exists(header_logo):
        st.image(header_logo, width=120)

with h_col2:
    st.title("Welcome to EdgeOS")
    st.markdown("### *Find fast. Place smarter.*")

st.write("---")

# --- NARROWER LAYOUT (THE WIDTH FIX) ---
# The '2's on the outside act as large padding, squeezing the '3's in the middle.
col_left, col_a, col_b, col_right = st.columns([2, 3, 3, 2])

with col_a:
    # Because of our CSS, this text will wrap inside the massive plum button
    if st.button("🔍 TALENT DATABASE SEARCH \n\n Access your global talent pool. Filter candidates and update records daily.", use_container_width=True):
        st.switch_page("pages/1_Talent_Database.py")

with col_b:
    if st.button("🎯 AI SHORTLISTER \n\n Match candidates against opportunities instantly using GPT-4o logic.", use_container_width=True):
        st.switch_page("pages/2_AI_Shortlister.py")
