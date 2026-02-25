import streamlit as st
import pandas as pd
from openai import OpenAI
import json
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="AI Shortlister | EdgeOS", layout="wide")

# --- AI MATCHING LOGIC ---
def analyze_with_ai(api_key, resume_text, job_tasks):
    client = OpenAI(api_key=api_key)
    if not resume_text or len(str(resume_text)) < 50:
        return {"score": 0, "justification": "Resume text too short for analysis."}

    prompt = f"""
    You are an expert recruiter. Score this resume (0-100) based strictly on these job tasks: {job_tasks}.
    Focus on transferable skills and relevant experience.
    
    Resume Text: {str(resume_text)[:5000]}
    
    Return ONLY a JSON object:
    {{
        "score": int,
        "justification": "One sentence explaining why this candidate is a good or poor fit."
    }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"score": 0, "justification": f"AI Error: {str(e)}"}

# --- UI HEADER ---
header_logo = "Edge_Lockup_Plum.jpg"
col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists(header_logo):
        st.image(header_logo, width=100)
with col2:
    st.title("Talent Matching & AI Shortlister")

# --- LOAD DATA ---
if os.path.exists("master_database.csv") and os.path.exists("Opportunity Information.csv"):
    df_c = pd.read_csv("master_database.csv")
    df_o = pd.read_csv("Opportunity Information.csv")
    
    # 1. Select the Job
    st.write("---")
    opp_list = df_o['Opportunity: Opportunity Name'].unique()
    selected_job = st.selectbox("Select Target Opportunity", opp_list)
    
    # 2. Extract Job Tasks
    job_row = df_o[df_o['Opportunity: Opportunity Name'] == selected_job].iloc[0]
    job_tasks = job_row.iloc[10:40].dropna().tolist()

    # 3. Settings & Filters
    st.sidebar.header("Matching Settings")
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    match_limit = st.sidebar.slider("Number of candidates to analyze", 5, 50, 20)

    if st.button("🚀 Run AI Shortlisting"):
        if not api_key:
            st.warning("Please enter your OpenAI API key in the sidebar.")
        else:
            # Only analyze candidates who have scraped Resume Text
            valid_cands = df_c[df_c['Resume Text'].str.len() > 50].head(match_limit)
            
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, (idx, cand) in enumerate(valid_cands.iterrows()):
                status_text.text(f"Analyzing: {cand['Candidate Name']}...")
                res = analyze_with_ai(api_key, cand['Resume Text'], job_tasks)
                
                results.append({
                    "Name": cand['Candidate Name'],
                    "Score": res['score'],
                    "Justification": res['justification'],
                    "Location": cand.get('Country', 'N/A'),
                    "Gender": cand.get('Gender', 'N/A')
                })
                progress_bar.progress((i + 1) / len(valid_cands))

            # Display Results
            shortlist_df = pd.DataFrame(results).sort_values(by="Score", ascending=False)
            st.write("### AI-Ranked Candidates")
            st.dataframe(shortlist_df, use_container_width=True)
            
            # Export
            csv_output = shortlist_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Shortlist", csv_output, "shortlist.csv", "text/csv")
            status_text.text("Shortlisting Complete!")
else:
    st.error("Missing Data: Please ensure 'master_database.csv' and 'Opportunity Information.csv' exist.")
