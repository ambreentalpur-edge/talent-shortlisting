import streamlit as st
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="EdgeOS", page_icon="Edge_Logomark_Plum.jpg", layout="wide")

# --- NATIVE STREAMLIT CSS ---
# We use this just to make the Streamlit buttons match your plum brand
st.markdown("""
<style>
    /* Style the Primary Buttons to match #4a0f70 */
    div.stButton > button[kind="primary"] {
        background-color: #4a0f70;
        color: white;
        border: none;
        font-weight: bold;
        border-radius: 8px;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #320a4d;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
col1, col2 = st.columns([1, 8])
with col1:
    if os.path.exists("Edge_Logomark_Plum.jpg"):
        st.image("Edge_Logomark_Plum.jpg", width=100)
    else:
        st.warning("Logo missing")

with col2:
    st.title("Welcome to EdgeOS")
    st.markdown("### *Find fast. Place smarter.*")

st.write("---")

# --- RELIABLE NAVIGATION CARDS ---
# Centered layout using Streamlit's native columns
c_left, c_main1, c_main2, c_right = st.columns([1, 2, 2, 1])

with c_main1:
    # A simple, solid colored box using standard HTML
    st.markdown("""
    <div style='background-color: #4a0f70; color: #f8f9fa; padding: 25px; border-radius: 12px; height: 200px; margin-bottom: 10px;'>
        <h3 style='color: white; margin-top: 0;'>🔍 Talent Database Search</h3>
        <p style='font-size: 16px;'>Access your global talent pool. Use the AI Chatbot to filter candidates and update records daily.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Native Streamlit button - 100% reliable for navigation
    if st.button("Open Database", type="primary", use_container_width=True):
        st.switch_page("pages/1_Talent_Database.py")

with c_main2:
    st.markdown("""
    <div style='background-color: #4a0f70; color: #f8f9fa; padding: 25px; border-radius: 12px; height: 200px; margin-bottom: 10px;'>
        <h3 style='color: white; margin-top: 0;'>🎯 AI Shortlister</h3>
        <p style='font-size: 16px;'>Match candidates against opportunities using GPT-4o logic to find the perfect fit instantly.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Open Shortlister", type="primary", use_container_width=True):
        st.switch_page("pages/2_AI_Shortlister.py")
