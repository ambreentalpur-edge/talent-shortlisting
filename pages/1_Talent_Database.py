import streamlit as st
import pandas as pd

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
