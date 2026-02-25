import streamlit as st
import os

# --- PAGE CONFIG ---
# Using the filenames you confirmed earlier
tab_logo = "logo.jpg"
st.set_page_config(page_title="EdgeOS", page_icon=tab_logo, layout="wide")

# --- BRANDING COLORS ---
brand_plum = "#7b2cbf"  # Your primary plum color
text_white = "#f8f9fa"  # Off-white for readability

# --- CUSTOM CSS FOR PLUM CARDS ---
st.markdown(f"""
<style>
    /* Main Card Styling */
    .card-box {{
        background-color: {brand_plum};
        color: {text_white};
        padding: 30px;
        border-radius: 15px;
        height: 280px;
        transition: transform 0.3s, box-shadow 0.3s;
        border: 1px solid #5a189a;
        margin-bottom: 20px;
    }}
    
    /* Hover Effect */
    .card-box:hover {{
        transform: translateY(-10px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        background-color: #9d4edd; /* Slightly lighter plum on hover */
    }}

    .card-title {{
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 15px;
    }}
    
    .card-text {{
        font-size: 16px;
        line-height: 1.5;
    }}
</style>
""", unsafe_allow_html=True)

# --- HEADER LOGO CHECK ---
header_logo = "Edge_Lockup_Plum.jpg"
col1, col2 = st.columns([1, 6])

with col1:
    # Check if file exists in the current directory
    if os.path.exists(header_logo):
        st.image(header_logo, width=120)
    else:
        st.error(f"Missing: {header_logo}") # Debugging message

with col2:
    st.title("Welcome to EdgeOS")
    st.markdown("### *Find fast. Place smarter.*")

st.write("---")

# --- CLICKABLE NAVIGATION CARDS ---
col_a, col_b = st.columns(2)

with col_a:
    st.markdown(f"""
    <div class="card-box">
        <div class="card-title">🔍 Talent Database Search</div>
        <div class="card-text">
            Access your global talent pool. Use the AI Chatbot to filter candidates by skills, 
            location, or experience and update your records daily.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Database", use_container_width=True):
        st.switch_page("pages/1_Talent_Database.py")

with col_b:
    st.markdown(f"""
    <div class="card-box">
        <div class="card-title">🎯 AI Shortlister</div>
        <div class="card-text">
            Match candidates against specific job opportunities using GPT-4o logic. 
            Rank talent instantly based on transferable skills and job requirements.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Shortlister", use_container_width=True):
        st.switch_page("pages/2_AI_Shortlister.py")
