import streamlit as st
import os

# --- PAGE CONFIG ---
tab_logo = "logo.jpg"
app_logo = "Edge_Lockup_H_Plum.jpg"
st.set_page_config(page_title="EdgeOS", page_icon=tab_logo, layout="wide")

# --- CSS FOR HOVER CARDS ---
st.markdown("""
<style>
    .card {
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ddd;
        transition: 0.3s;
        cursor: pointer;
        height: 200px;
        background-color: #f9f9f9;
    }
    .card:hover {
        border-color: #7b2cbf;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        height: 250px;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists("Edge_Lockup_Plum.jpg"):
        st.image("Edge_Lockup_Plum.jpg", width=100)
with col2:
    st.title("Welcome to EdgeOS")
    st.markdown("### *Find fast. Place smarter.*")

st.write("---")

# --- NAVIGATION CARDS ---
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""
    <div class="card">
        <h3>🔍 Talent Database Search</h3>
        <p>Access your global talent pool. Use the AI Chatbot to filter candidates by skills, location, or experience.</p>
        <p><i>(Hover for details - Click sidebar to enter)</i></p>
    </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown("""
    <div class="card">
        <h3>🎯 AI Shortlister</h3>
        <p>Match candidates against specific job opportunities using GPT-4o logic to find the perfect fit instantly.</p>
        <p><i>(Hover for details - Click sidebar to enter)</i></p>
    </div>
    """, unsafe_allow_html=True)
