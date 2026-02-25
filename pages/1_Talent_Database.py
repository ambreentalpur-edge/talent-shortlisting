import streamlit as st
import pandas as pd
import os

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
