import streamlit as st
import os

# --- HEADER ---
header_logo = "Edge_Logomark_Plum.jpg"

# Create centered layout for the header
h_col_left, h_col1, h_col2, h_col_right = st.columns([1, 1, 6, 1])

with h_col1:
    if os.path.exists(header_logo):
        st.image(header_logo, width=120)
    else:
        # This will help you debug if the filename is wrong
        st.error(f"Logo not found: {header_logo}") 

with h_col2:
    st.title("Welcome to EdgeOS")
    st.markdown("### *Find fast. Place smarter.*")

# --- BRANDING COLORS ---
brand_plum = "#4a0f70"
text_white = "#f8f9fa"

# --- CUSTOM CSS ---
st.markdown(f"""
<style>
    .card-box {{
        background-color: {brand_plum};
        color: {text_white};
        padding: 25px;
        border-radius: 15px;
        height: 260px; /* Slightly shorter height for better proportions */
        transition: transform 0.3s;
        border: 1px solid #320a4d;
        margin-bottom: 10px;
        display: flex;
        flex-direction: column;
    }}
    .card-box:hover {{
        transform: translateY(-10px);
        background-color: #5e1a8a;
    }}
    .card-title {{ font-size: 22px; font-weight: bold; margin-bottom: 12px; }}
    .card-text {{ font-size: 15px; line-height: 1.4; }}
    
    /* Button styling to match card width */
    div.stButton > button {{
        background-color: {brand_plum};
        color: white;
        border-radius: 10px;
        border: 1px solid white;
        margin-top: 5px;
    }}
</style>
""", unsafe_allow_html=True)


# --- NAVIGATION CARDS (CENTERED & NARROWER) ---
# [1, 2, 2, 1] creates empty space on the ends to keep cards in the middle
col_left, col_a, col_b, col_right = st.columns([1, 2, 2, 1])

with col_a:
    st.markdown(f'''
        <div class="card-box">
            <div class="card-title">🔍 Talent Database Search</div>
            <div class="card-text">
                Access your global talent pool. Use the AI Chatbot to filter candidates and update records daily.
            </div>
        </div>
    ''', unsafe_allow_html=True)
    if st.button("Open Database", key="db_btn", use_container_width=True):
        st.switch_page("pages/1_Talent_Database.py")

with col_b:
    st.markdown(f'''
        <div class="card-box">
            <div class="card-title">🎯 AI Shortlister</div>
            <div class="card-text">
                Match candidates against opportunities using GPT-4o logic to find the perfect fit instantly.
            </div>
        </div>
    ''', unsafe_allow_html=True)
    if st.button("Open Shortlister", key="short_btn", use_container_width=True):
        st.switch_page("pages/2_AI_Shortlister.py")
