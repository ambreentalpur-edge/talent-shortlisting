import streamlit as st
import pandas as pd
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Talent Database | EdgeOS", layout="wide")

# --- BRANDING & SIDEBAR ---
st.sidebar.markdown("""
<style>
    div.stButton > button {
        background-color: #4a0f70 !important;
        color: white !important;
        border-radius: 8px;
        border: none;
    }
    div.stButton > button:hover { background-color: #320a4d !important; }
</style>
""", unsafe_allow_html=True)

nav_logo = "../Edge_Logomark_Plum.jpg"
if os.path.exists(nav_logo): st.sidebar.image(nav_logo, width=80)
if st.sidebar.button(":edge_logomark: Return to Dashboard", use_container_width=True): st.switch_page("app.py")
st.sidebar.write("---")

# --- DATABASE ENGINE ---
def update_database(new_df):
    master_path = "master_database.csv"
    if os.path.exists(master_path):
        master_df = pd.read_csv(master_path)
        # Drop duplicates based on Candidate Name to keep the most recent record
        updated = pd.concat([master_df, new_df]).drop_duplicates(subset=['Candidate Name'], keep='last')
        updated.to_csv(master_path, index=False)
    else:
        new_df.to_csv(master_path, index=False)

# --- HEADER ---
header_logo = "../Edge_Logomark_Plum.jpg"
col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists(header_logo): st.image(header_logo, width=120)
with col2: 
    st.title("Talent Database & AI Search")

# --- UPLOAD SECTION ---
with st.expander("➕ Upload Final Database / Daily Sync"):
    new_batch = st.file_uploader("Upload EdgeOS_Final_Database.csv here", type="csv")
    if st.button("Sync to Master Database") and new_batch is not None:
        df_new = pd.read_csv(new_batch)
        update_database(df_new)
        st.success("✅ Database synced successfully! Your candidates are now loaded.")

# --- SEARCH & FILTERS ---
if os.path.exists("master_database.csv"):
    df_db = pd.read_csv("master_database.csv")
    st.sidebar.info(f"📊 Total Talent Pool: **{len(df_db)} candidates**")
    
    # Dynamic Sidebar Filters
    st.sidebar.subheader("Quick Filters")
    if 'Industry' in df_db.columns:
        industries = ["All"] + df_db['Industry'].dropna().unique().tolist()
        sel_industry = st.sidebar.selectbox("Filter by Industry", industries)
        if sel_industry != "All":
            df_db = df_db[df_db['Industry'] == sel_industry]

    st.write("---")
    st.subheader("🤖 AI Talent Scout")
    # You can search for specific things like "biostatistics" or "public health" here
    user_query = st.text_input("Search the database (e.g., 'Find candidates with project management experience')")

    if user_query:
        # Filters rows where the Resume Text contains the user's query
        results = df_db[df_db['Resume Text'].str.contains(user_query, case=False, na=False)]
    else:
        results = df_db # Show all if no query

    if not results.empty:
        # Display clean columns
        display_cols = ['Candidate Name']
        if 'Industry' in df_db.columns: display_cols.append('Industry')
        if 'Resume Text' in df_db.columns: display_cols.append('Resume Text')
        
        st.write(f"**Showing {len(results)} candidates:**")
        st.dataframe(results[display_cols], use_container_width=True)
    else:
        st.warning("No matches found. Try broadening your search terms.")
else:
    st.info("Your database is empty. Please upload your final CSV using the expander above.")
