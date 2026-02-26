import streamlit as st
import pandas as pd
import os
from openai import OpenAI
import json
import random

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Shortlister | EdgeOS", layout="wide")

# --- BRANDING & SIDEBAR ---
st.sidebar.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none !important;}
    div.stButton > button { background-color: #4a0f70 !important; color: white !important; border-radius: 8px; border: none; }
    div.stButton > button:hover { background-color: #320a4d !important; }
</style>
""", unsafe_allow_html=True)

sidebar_logo = "Edge_Lockup_H_Plum.jpg"
if os.path.exists(sidebar_logo): 
    st.sidebar.image(sidebar_logo, use_container_width=True)

st.sidebar.write("---")

if st.sidebar.button("🏠 Return to Dashboard", use_container_width=True): 
    st.switch_page("app.py")
st.sidebar.write("---")

# --- HEADER ---
header_logo = "../Edge_Lockup_Plum.jpg"
col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists(header_logo): st.image(header_logo, width=120)
with col2: 
    st.title("Talent Matching & AI Shortlister")

# --- AI MATCHING LOGIC ---
def analyze_with_ai(api_key, resume_text, job_context):
    client = OpenAI(api_key=api_key)
    if not resume_text or pd.isna(resume_text) or len(str(resume_text)) < 50:
        return {"score": 0, "justification": "Resume text is too short or missing."}

    prompt = f"""
    You are an expert recruiter. Score this candidate (0-100) based on these requirements:
    {job_context}
    
    Resume:
    {str(resume_text)[:5000]}
    
    Return ONLY a JSON object:
    {{ "score": int, "justification": "Short explanation." }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"score": 0, "justification": f"API Error: {str(e)[:50]}"}

# --- UPLOAD SECTION ---
with st.expander("➕ Update Opportunity List (Upload CSV)"):
    new_opps = st.file_uploader("Upload Opportunity Information.csv here", type="csv")
    if st.button("Sync Opportunities") and new_opps is not None:
        df_new_o = pd.read_csv(new_opps)
        df_new_o.to_csv("Opportunity Information.csv", index=False)
        st.success("✅ Opportunity list updated!")

# --- MAIN UI ---
db_path = "master_database.csv"
opp_path = "Opportunity Information.csv"

if os.path.exists(db_path) and os.path.exists(opp_path):
    # RELOAD DATA BUTTON (The Refresh you asked for)
    if st.button("🔄 Refresh Candidate Pool & Clear Filters"):
        st.cache_data.clear()
        st.rerun()

    df_c = pd.read_csv(db_path)
    df_o = pd.read_csv(opp_path)
    
    st.write("---")
    
    if 'Opportunity: Opportunity Name' in df_o.columns:
        opp_list = df_o['Opportunity: Opportunity Name'].dropna().unique()
        selected_job = st.selectbox("Select Target Opportunity", opp_list)
        
        job_row = df_o[df_o['Opportunity: Opportunity Name'] == selected_job].iloc[0]
        # Logic to grab job requirements from CSV
        job_details = [f"{col}: {job_row[col]}" for col in df_o.columns[5:] if pd.notna(job_row[col])]
        job_context = "\n".join(job_details)
    else:
        st.error("Opportunity column not found.")
        job_context = ""

    # Settings
    st.sidebar.subheader("Matching Settings")
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    match_limit = st.sidebar.slider("Number of candidates to analyze", 5, 100, 10)

    if st.button("🚀 Run AI Shortlisting", use_container_width=True):
        if not api_key:
            st.warning("Enter your OpenAI API key.")
        else:
            resume_col = next((c for c in df_c.columns if 'resume text' in c.lower()), None)
            
            # THE SHUFFLE: This picks a NEW random set of candidates every time you refresh
            valid_cands = df_c[df_c[resume_col].notna()].sample(frac=1).head(match_limit)
            
            if valid_cands.empty:
                st.error("No resumes found to score.")
            else:
                results = []
                prog = st.progress(0)
                status = st.empty()

                for i, (idx, cand) in enumerate(valid_cands.iterrows()):
                    name = cand.get('Candidate Name', cand.get('Candidate: Candidate Name', 'Unknown'))
                    status.text(f"Analyzing: {name}...")
                    
                    res = analyze_with_ai(api_key, cand[resume_col], job_context)
                    
                    results.append({
                        "Name": name,
                        "Score": res.get('score', 0),
                        "Justification": res.get('justification', ''),
                        "Status": cand.get('Go Live Status', 'N/A')
                    })
                    prog.progress((i + 1) / len(valid_cands))

                shortlist_df = pd.DataFrame(results).sort_values(by="Score", ascending=False)
                status.text("✅ Analysis Complete!")
                st.dataframe(shortlist_df, use_container_width=True)
else:
    st.info("Ensure 'master_database.csv' and 'Opportunity Information.csv' are loaded.")
