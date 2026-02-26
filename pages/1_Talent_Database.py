import streamlit as st
import pandas as pd
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Talent Database | EdgeOS", layout="wide")
# --- HIDE DEFAULT SIDEBAR MENU ---
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# --- BRANDING & SIDEBAR ---
st.sidebar.markdown("""
<style>
    div.stButton > button { background-color: #4a0f70 !important; color: white !important; border-radius: 8px; border: none; }
    div.stButton > button:hover { background-color: #320a4d !important; }
</style>
""", unsafe_allow_html=True)

# --- BRANDING & SIDEBAR ---
st.sidebar.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none !important;}
    div.stButton > button { background-color: #4a0f70 !important; color: white !important; border-radius: 8px; border: none; }
    div.stButton > button:hover { background-color: #320a4d !important; }
</style>
""", unsafe_allow_html=True)

# Add the new horizontal logo
sidebar_logo = "../Edge_Lockup_H_Plum.jpg"
if os.path.exists(sidebar_logo): 
    st.sidebar.image(sidebar_logo, use_container_width=True)

st.sidebar.write("---") # Adds a nice divider line under the logo

if st.sidebar.button("🏠 Return to Dashboard", use_container_width=True): 
    st.switch_page("app.py")

# --- DATABASE ENGINE ---
def update_database(new_df):
    master_path = "master_database.csv"
    if os.path.exists(master_path):
        master_df = pd.read_csv(master_path)
        updated = pd.concat([master_df, new_df])
        dup_col = next((c for c in updated.columns if 'name' in c.lower() or 'id' in c.lower()), updated.columns[0])
        updated = updated.drop_duplicates(subset=[dup_col], keep='last')
        updated.to_csv(master_path, index=False)
    else:
        new_df.to_csv(master_path, index=False)

# --- HEADER ---
header_logo = "../Edge_Lockup_H_Plum.jpg"
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
        
    # 2. Country Filter
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

    # 4. Go Live Status Filter
    status_col = next((c for c in cols if 'go live status' in c.lower()), None)
    if status_col:
        statuses = ["All"] + df_db[status_col].astype(str).dropna().unique().tolist()
        sel_status = st.sidebar.selectbox("Go Live Status", statuses)
        if sel_status != "All": df_db = df_db[df_db[status_col].astype(str) == sel_status]
        
    # 5. School Filter
    school_col = next((c for c in cols if 'school' in c.lower()), None)
    if school_col:
        schools = ["All"] + df_db[school_col].astype(str).dropna().unique().tolist()
        sel_school = st.sidebar.selectbox("School / University", schools)
        if sel_school != "All": df_db = df_db[df_db[school_col].astype(str) == sel_school]

    st.write("---")
    st.subheader("🤖 AI Talent Scout")
    # Updated placeholder text to reflect the new comma functionality
    user_query = st.text_input("Search keywords (use commas for 'AND', e.g., 'doctor, ECW' or 'public health, biostatistics')")

    # Filter by AI Search (UPDATED FOR COMMAS)
    resume_col = next((c for c in cols if 'resume text' in c.lower()), None)
    if user_query and resume_col:
        # Splits the query by commas and removes any extra spaces around the words
        keywords = [kw.strip() for kw in user_query.split(',') if kw.strip()]
        
        if keywords:
            mask = df_db[resume_col].astype(str).str.contains(keywords[0], case=False, na=False)
            for kw in keywords[1:]:
                mask &= df_db[resume_col].astype(str).str.contains(kw, case=False, na=False)
            results = df_db[mask]
        else:
            results = df_db
    else:
        results = df_db

    # --- DISPLAY LOGIC ---
    if not results.empty:
        st.write(f"**Showing {len(results)} candidates:**")
        
        display_cols = []
        name_col = next((c for c in cols if 'name' in c.lower()), cols[0]) 
        display_cols.append(name_col)
        
        if 'Industry' in cols: display_cols.append('Industry')
        if country_col: display_cols.append(country_col)
        if status_col: display_cols.append(status_col)
        
        display_cols = list(dict.fromkeys(display_cols))
        st.dataframe(results[display_cols], use_container_width=True)
    else:
        st.warning("No matches found. Try broadening your search terms.")
        
    with st.expander("🛠️ System Diagnostics: View Raw CSV Columns"):
        st.write(cols)

else:
    st.info("Your database is empty. Please upload your final CSV using the expander above.")
