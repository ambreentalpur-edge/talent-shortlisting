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

# --- PRECISION AI SCORING LOGIC ---
def analyze_with_ai(api_key, resume_text, target_emr, call_required, other_tasks):
    client = OpenAI(api_key=api_key)
    if not resume_text or pd.isna(resume_text) or len(str(resume_text)) < 50:
        return {"score": 0, "justification": "Resume missing or too short."}

    prompt = f"""
    You are a strict screening bot. Score this candidate (0-100) based on these EXACT rules:
    
    1. EMR/AMS TOOL MATCH (30 Points Max):
       - Target System: "{target_emr}"
       - Award 30 pts if resume mentions "{target_emr}".
       - Award 10 pts if resume mentions ANY other EMR, CRM, AMS, or EHR tool.
       - Award 0 pts if no system experience is found.
    
    2. CALLS & INTERACTION (30 Points Max):
       - Interaction Required: {call_required}
       - If required, award 30 pts if resume mentions "calls", "interaction", "dealing with customers", or "patients".
       - Otherwise, 0 pts for this section.
    
    3. INDUSTRY & CORE TASKS (40 Points Max):
       - Evaluate fit for: {other_tasks}
       - Soft skills must be ignored (0 points).
    
    CANDIDATE RESUME:
    {str(resume_text)[:5000]}
    
    Return ONLY a JSON object:
    {{ "score": int, "justification": "Breakdown: EMR pts, Call pts, Task pts." }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[{"role": "system", "content": "You are a binary screening tool. Do not award points for soft skills."},
                      {"role": "user", "content": prompt}],
            temperature=0
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"score": 0, "justification": f"API Error"}

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
    # REFRESH / RANDOMIZE BUTTON
    if st.button("🔄 Refresh & Shuffle Candidates"):
        st.cache_data.clear()
        st.rerun()

    df_c = pd.read_csv(db_path)
    df_o = pd.read_csv(opp_path)
    
    st.write("---")
    
    if 'Opportunity: Opportunity Name' in df_o.columns:
        opp_list = df_o['Opportunity: Opportunity Name'].dropna().unique()
        selected_job = st.selectbox("Select Target Opportunity", opp_list)
        
        job_row = df_o[df_o['Opportunity: Opportunity Name'] == selected_job].iloc[0]
        
        # Extract the specific variables for the prompt
        target_emr = str(job_row.get('AMS/CRM/EMR/EHR/PMS', 'Not Specified'))
        in_call = str(job_row.get('Inbound Calls', ''))
        out_call = str(job_row.get('Outbound Calls', ''))
        call_req = "Yes" if (in_call.strip() or out_call.strip()) else "No"
        other_tasks = f"{job_row.get('Industry', '')} - {job_row.get('Background', '')}"
        
        with st.expander("🔍 Scoring Logic for this Role"):
            st.write(f"**Target EMR/AMS:** {target_emr}")
            st.write(f"**Call Interaction Required:** {call_req}")
            st.write(f"**Industry Context:** {other_tasks}")
            
    else:
        st.error("Opportunity column not found.")
        target_emr, call_req, other_tasks = "N/A", "N/A", "N/A"

    # Settings
    st.sidebar.subheader("Matching Settings")
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    match_limit = st.sidebar.slider("Number of candidates to analyze", 3, 50, 3)

    if st.button("🚀 Run AI Shortlisting", use_container_width=True):
        if not api_key:
            st.warning("Enter your OpenAI API key.")
        else:
            resume_col = next((c for c in df_c.columns if 'resume text' in c.lower()), None)
            # Pick a fresh random batch
            valid_cands = df_c[df_c[resume_col].notna()].sample(frac=1).head(match_limit)
            
            if valid_cands.empty:
                st.error("No resumes found.")
            else:
                results = []
                prog = st.progress(0)
                status = st.empty()

                for i, (idx, cand) in enumerate(valid_cands.iterrows()):
                    name_col = next((c for c in df_c.columns if 'name' in c.lower()), 'Candidate Name')
                    name = cand.get(name_col, 'Unknown')
                    
                    status.text(f"Analyzing: {name}...")
                    res = analyze_with_ai(api_key, cand[resume_col], target_emr, call_req, other_tasks)
                    
                    results.append({
                        "Name": name,
                        "Score": res.get('score', 0),
                        "Justification": res.get('justification', ''),
                        "Country": cand.get('Country', 'N/A')
                    })
                    prog.progress((i + 1) / len(valid_cands))

                shortlist_df = pd.DataFrame(results).sort_values(by="Score", ascending=False)
                status.text("✅ Ranking Complete!")
                st.dataframe(shortlist_df, use_container_width=True)
                
                st.download_button("📥 Download Shortlist CSV", shortlist_df.to_csv(index=False).encode('utf-8'), "shortlist.csv", "text/csv")
else:
    st.info("Ensure both CSV files are uploaded to begin.")
