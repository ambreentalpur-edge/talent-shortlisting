import streamlit as st
import pandas as pd
import os
from openai import OpenAI
import json

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

sidebar_logo = "../Edge_Lockup_H_Plum.jpg"
if os.path.exists(sidebar_logo): 
    st.sidebar.image(sidebar_logo, use_container_width=True)

st.sidebar.write("---")

# Routing strictly back to app.py
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
        return {"score": 0, "justification": "Resume text missing or too short."}

    prompt = f"""
    You are an expert executive recruiter. Score this candidate's resume (0-100) based STRICTLY on these job requirements:
    
    JOB REQUIREMENTS:
    {job_context}
    
    CANDIDATE RESUME:
    {str(resume_text)[:6000]}
    
    Evaluate their direct experience with the specific tools, tasks, and soft skills requested.
    Return ONLY a JSON object:
    {{ "score": int, "justification": "One clear sentence explaining the exact reason for the score." }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {"score": 0, "justification": "AI Analysis Error."}

# --- MAIN UI ---
db_path = "master_database.csv"
opp_path = "Opportunity Information.csv"

if os.path.exists(db_path) and os.path.exists(opp_path):
    df_c = pd.read_csv(db_path)
    df_o = pd.read_csv(opp_path)
    
    st.write("---")
    
    # 1. Select the Job safely
    if 'Opportunity: Opportunity Name' in df_o.columns:
        opp_list = df_o['Opportunity: Opportunity Name'].dropna().unique()
        selected_job = st.selectbox("Select Target Opportunity", opp_list)
        
        # 2. Dynamically extract the specific job requirements from the Opportunity CSV
        job_row = df_o[df_o['Opportunity: Opportunity Name'] == selected_job].iloc[0]
        job_details = []
        
        # Starts scanning from the 'Industry' column onwards, grabbing any requirement that isn't blank
        start_idx = df_o.columns.get_loc('Industry') if 'Industry' in df_o.columns else 2
        for col in df_o.columns[start_idx:]:
            val = job_row[col]
            if pd.notna(val) and str(val).strip() != "" and str(val).strip() != "nan":
                job_details.append(f"{col}: {val}")
        
        job_context = "\n".join(job_details)
        
        with st.expander("👀 View what the AI is analyzing for this job"):
            st.text(job_context)
            
    else:
        st.error("Could not find 'Opportunity: Opportunity Name' in your CSV.")
        job_context = ""

    # Settings
    st.sidebar.subheader("Matching Settings")
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    match_limit = st.sidebar.slider("Number of candidates to analyze", 5, 100, 20)

    # Run AI
    if st.button("🚀 Run AI Shortlisting", use_container_width=True):
        if not api_key:
            st.warning("Please enter your OpenAI API key in the sidebar.")
        else:
            resume_col = next((c for c in df_c.columns if 'resume text' in c.lower()), None)
            valid_cands = df_c[df_c[resume_col].notna()].head(match_limit) if resume_col else pd.DataFrame()
            
            if valid_cands.empty:
                st.error("No valid resume text found in your database. Check your Talent Database sync.")
            else:
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, (idx, cand) in enumerate(valid_cands.iterrows()):
                    # Find candidate name dynamically
                    name_col = next((c for c in df_c.columns if 'name' in c.lower()), 'Unknown')
                    name = cand.get(name_col, 'Unknown')
                    
                    status_text.text(f"Analyzing: {name}...")
                    
                    res = analyze_with_ai(api_key, cand[resume_col], job_context)
                    
                    # Package the results, dynamically grabbing Country and Status if they exist
                    row_data = {
                        "Name": name,
                        "Score": res.get('score', 0),
                        "Justification": res.get('justification', '')
                    }
                    
                    country_col = next((c for c in df_c.columns if 'country' in c.lower()), None)
                    if country_col: row_data["Country"] = cand.get(country_col, '')
                    
                    status_col = next((c for c in df_c.columns if 'go live status' in c.lower()), None)
                    if status_col: row_data["Status"] = cand.get(status_col, '')
                    
                    results.append(row_data)
                    progress_bar.progress((i + 1) / len(valid_cands))

                # Display Results
                shortlist_df = pd.DataFrame(results).sort_values(by="Score", ascending=False)
                status_text.text("✅ Shortlisting Complete!")
                
                st.write("### AI-Ranked Candidates")
                
                # Make the table visually appealing (Score first, Justification last)
                cols_order = ['Name', 'Score']
                if 'Country' in shortlist_df.columns: cols_order.append('Country')
                if 'Status' in shortlist_df.columns: cols_order.append('Status')
                cols_order.append('Justification')
                
                st.dataframe(shortlist_df[cols_order], use_container_width=True)
                
                csv_output = shortlist_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Shortlist CSV", csv_output, "shortlist.csv", "text/csv")
else:
    st.info("Please ensure both your candidate database is synced and 'Opportunity Information.csv' is uploaded to the main folder.")
