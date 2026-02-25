import streamlit as st
import pandas as pd
import os
from openai import OpenAI
import json

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Shortlister | EdgeOS", layout="wide")

# --- SIDEBAR & BRANDING ---
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

# --- HEADER ---
header_logo = "../Edge_Lockup_H_Plum.jpg"
col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists(header_logo): st.image(header_logo, width=120)
with col2: 
    st.title("Talent Matching & AI Shortlister")

# --- AI MATCHING LOGIC ---
def analyze_with_ai(api_key, resume_text, job_tasks):
    client = OpenAI(api_key=api_key)
    if not resume_text or pd.isna(resume_text) or len(str(resume_text)) < 50:
        return {"score": 0, "justification": "Resume text missing or too short."}

    prompt = f"""
    You are an expert recruiter. Score this resume (0-100) based strictly on these job tasks: {job_tasks}.
    Focus on transferable skills and relevant experience.
    Resume Text: {str(resume_text)[:5000]}
    
    Return ONLY a JSON object:
    {{ "score": int, "justification": "One clear sentence explaining the score." }}
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
    opp_list = df_o['Opportunity: Opportunity Name'].unique()
    selected_job = st.selectbox("Select Target Opportunity", opp_list)
    
    # Ensure this index matches where your tasks are in the Opportunity CSV
    job_row = df_o[df_o['Opportunity: Opportunity Name'] == selected_job].iloc[0]
    job_tasks = job_row.iloc[10:40].dropna().tolist()

    st.sidebar.subheader("Matching Settings")
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    match_limit = st.sidebar.slider("Number of candidates to analyze", 5, 50, 10)

    if st.button("🚀 Run AI Shortlisting", use_container_width=True):
        if not api_key:
            st.warning("Please enter your OpenAI API key in the sidebar.")
        else:
            # Only score candidates that actually have resume text
            valid_cands = df_c[df_c['Resume Text'].notna()].head(match_limit)
            
            if valid_cands.empty:
                st.error("No valid resume text found. Check your database.")
            else:
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, (idx, cand) in enumerate(valid_cands.iterrows()):
                    name = cand.get('Candidate Name', 'Unknown')
                    status_text.text(f"Analyzing: {name}...")
                    
                    res = analyze_with_ai(api_key, cand['Resume Text'], job_tasks)
                    results.append({
                        "Name": name,
                        "Industry": cand.get('Industry', 'N/A'),
                        "Score": res.get('score', 0),
                        "Justification": res.get('justification', '')
                    })
                    progress_bar.progress((i + 1) / len(valid_cands))

                shortlist_df = pd.DataFrame(results).sort_values(by="Score", ascending=False)
                status_text.text("✅ Shortlisting Complete!")
                
                st.write("### AI-Ranked Candidates")
                st.dataframe(shortlist_df, use_container_width=True)
                
                csv_output = shortlist_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Shortlist CSV", csv_output, "shortlist.csv", "text/csv")
else:
    st.info("Please ensure both your candidate database is synced and 'Opportunity Information.csv' is uploaded.")
