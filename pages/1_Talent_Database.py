import streamlit as st
import pandas as pd
import os
# --- SUB-PAGE LOGO LOGIC ---
header_logo = "Edge_Logomark_Plum.jpg"

# Logic to find the logo if the script is running from the 'pages' folder
if not os.path.exists(header_logo):
    header_logo = "../Edge_Logomark_Plum.jpg"

if os.path.exists(header_logo):
    # If using in a column next to title
    col1, col2 = st.columns([1, 6])
    with col1:
        st.image(header_logo, width=100)
    with col2:
        st.title("EdgeOS")
        
# --- BRANDED SIDEBAR NAVIGATION ---
# Using the specific Logomark you mentioned for the app interface
nav_logo = "Edge_Logomark_Plum.jpg" 

if os.path.exists(nav_logo):
    st.sidebar.image(nav_logo, width=80)
else:
    # Fallback if the logo is in the root directory while you are in the /pages folder
    if os.path.exists("../Edge_Logomark_Plum.jpg"):
        st.sidebar.image("../Edge_Logomark_Plum.jpg", width=80)

# The navigation button styled as a "Return"
if st.sidebar.button("Return to Dashboard", use_container_width=True):
    st.switch_page("app.py")

st.sidebar.write("---")

st.sidebar.write("---") # Visual separator
def update_master_database(new_df):
    if os.path.exists("master_database.csv"):
        master_df = pd.read_csv("master_database.csv")
        # Combine and remove duplicates based on Candidate ID
        updated_df = pd.concat([master_df, new_df]).drop_duplicates(subset=['Candidate: ID'], keep='last')
        updated_df.to_csv("master_database.csv", index=False)
    else:
        new_df.to_csv("master_database.csv", index=False)

# --- UI FOR UPLOADING DAILY ---
uploaded_file = st.file_uploader("Upload Daily Batch", type="csv")
if uploaded_file:
    new_data = pd.read_csv(uploaded_file)
    update_master_database(new_data)
    st.success("Database Updated!")
