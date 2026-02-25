import streamlit as st
import pandas as pd
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Talent Database | EdgeOS", layout="wide")

# --- BRANDING & SIDEBAR ---
st.sidebar.markdown("""
<style>
    div.stButton > button { background-color: #4a0f70 !important; color: white !important; border-radius: 8px; border: none; }
    div.stButton > button:hover { background-color: #320a4d !important; }
</style>
""", unsafe_allow_html=True)

nav_logo = "../Edge_Logomark_Plum.jpg"
if os.path.exists(nav_logo): st.sidebar.image(nav_logo, width=80)
if st.sidebar.button("🏠 Return to Dashboard", use_container_width=True): st.switch_page("app.py")
st.sidebar.write("---")

# --- DATABASE ENGINE ---
def update_database(new_df):
    master_path = "master_database.csv"
    if os.path.exists(master_path):
        master_df = pd.read_csv(master_path)
        updated = pd.concat([master_df, new_df])
        # Safely find the name or ID column to drop duplicates
        dup_col = next((c for c in updated.columns if 'name' in c.lower() or 'id' in c.lower()), updated.columns[0])
        updated = updated.drop_duplicates(subset=[dup_col], keep='last')
        updated.to_csv(master_path, index=False)
    else:
        new_df.to_csv(master_path, index=False)

# --- HEADER ---
header_logo = "../Edge_Lockup_Plum.jpg"
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

# --- DYNAMIC SEARCH & MULTI-FILTERS ---
if os.path.exists("master_database.csv"):
    df_db = pd.read_csv("master_database.csv")
    cols = df_db.columns.tolist()
    st.sidebar.info(f"📊 Total Talent Pool: **{len(df_db)} candidates**")
    
    st.sidebar.subheader("Quick Filters")
    
    # 1. Industry Filter
    if 'Industry' in cols:
        industries = ["All"] + df_db['Industry'].dropna().unique().tolist()
        sel_ind = st.sidebar.selectbox("Industry", industries)
        if sel_ind != "All": df_db = df_db[df_db['Industry'] == sel_ind]
        
    # 2. Country Filter (Dynamically looks for 'country' in the column name)
    country_col = next((c for c in cols if 'country' in c.lower()), None)
    if country_col:
        countries = ["All"] + df_db[country_col].astype(str).dropna().unique().tolist()
        sel_country = st.sidebar.selectbox("Country", countries)
        if sel_country != "All": df_db = df_db[df_db[country_col].astype(str) == sel_country]
        
    # 3. Gender Filter
    gender_col = next((c for c in cols if 'gender' in c.lower()), None)
    if gender_col:
        genders = ["All"] + df_db[gender_col].astype(str).dropna().unique().tolist()
        sel_gender = st.sidebar.selectbox("Gender", genders)
        if sel_gender != "All": df_db = df_db[df_db[gender_col].astype(str) == sel_gender]
        
    # 4. Education Filter (Catches 'School', 'Education', or 'University')
    edu_col = next((c for c in cols if c.lower() in ['school', 'education', 'university', 'degree']), None)
    if edu_col:
        schools = ["All"] + df_db[edu_col].astype(str).dropna().unique().tolist()
        sel_school = st.sidebar.selectbox("Education", schools)
        if sel_school != "All": df_db = df_db[df_db[edu_col].astype(str) == sel_school]

    st.write("---")
    st.subheader("🤖 AI Talent Scout")
    user_query = st.text_input("Search the database (e.g., 'Find candidates with biostatistics experience')")

    # Filter by AI Search
    resume_col = next((c for c in cols if 'resume text' in c.lower()), None)
    if user_query and resume_col:
        results = df_db[df_db[resume_col].astype(str).str.contains(user_query, case=False, na=False)]
    else:
        results = df_db

    # --- DISPLAY FIX (Prevents the KeyError) ---
    if not results.empty:
        st.write(f"**Showing {len(results)} candidates:**")
        
        # Safely build the columns to display based ONLY on what actually exists in your CSV
        display_cols = []
        name_col = next((c for c in cols if 'name' in c.lower()), cols[0]) 
        display_cols.append(name_col)
        
        if 'Industry' in cols: display_cols.append('Industry')
        if country_col: display_cols.append(country_col)
        if gender_col: display_cols.append(gender_col)
        if edu_col: display_cols.append(edu_col)
        if resume_col: display_cols.append(resume_col)
        
        # Remove any duplicate columns just in case
        display_cols = list(dict.fromkeys(display_cols))
        
        st.dataframe(results[display_cols], use_container_width=True)
    else:
        st.warning("No matches found. Try broadening your search terms.")
        
    # Debug Tool: Helps you see exactly what your CSV columns are named
    with st.expander("🛠️ System Diagnostics: View Raw CSV Columns"):
        st.write("If a filter isn't showing up, the column in your CSV might be named differently. Here are the exact column names the app sees:")
        st.write(cols)

else:
    st.info("Your database is empty. Please upload your final CSV using the expander above.")
