import streamlit as st
import pandas as pd
import requests
import io
from bs4 import BeautifulSoup
import re
from pypdf import PdfReader
from openai import OpenAI
import json
import os

# --- PAGE CONFIGURATION & STATE ---
st.set_page_config(
    page_title="Edge Talent Shortlister",
    page_icon="🟣",
    layout="wide"
)

# Initialize Session State (Memory)
if "extra_requirements" not in st.session_state:
    st.session_state.extra_requirements = []
if "shortlist_results" not in st.session_state:
    st.session_state.shortlist_results = None

# --- BRANDING CSS ---
st.markdown("""
    <style>
    h1, h2, h3 { color: #4a0f70 !important; font-family: 'Helvetica', sans-serif; }
    div.stButton > button { background-color: #4a0f70; color: white; border-radius: 8px; border: none; font-weight: bold; }
    div.stButton > button:hover { background-color: #914de8; color: white; }
    [data-testid="stSidebar"] { background-color: #f5f3fa; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] label { color: #4a0f70 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---

@st.cache_data
def load_and_clean_data(cand_file, opp_file, int_file):
    def read_csv_safe(file):
        try:
            file.seek(0)
            return pd.read_csv(file, encoding='utf-8')
        except UnicodeDecodeError:
            file.seek(0)
            return pd.read_csv(file, encoding='ISO-8859-1')

    df_c = read_csv_safe(cand_file)
    df_o = read_csv_safe(opp_file)
    
    if int_file is not None:
        df_i = read_csv_safe(int_file)
        if 'Candidate: Candidate Name' in df_i.columns:
            df_i['Candidate Name'] = df_i['Candidate: Candidate Name'].str.strip()
    else:
        df_i = pd.DataFrame()

    def extract_link(html_string):
        if pd.isna(html_string): return None
        try:
            soup = BeautifulSoup(str(html_string), 'html.parser')
            tag = soup.find('a')
            if tag and tag.has_attr('href'):
                href = tag['href']
                if "javascript" in href:
                    urls = re.findall(r'(https?://[^\s\'"]+)', str(html_string))
                    if urls: return urls[0]
                return href
            return html_string 
        except:
            return html_string

    if 'Public link' in df_c.columns:
        df_c['Clean_Resume_Link'] = df_c['Public link'].apply(extract_link)
    else:
        df_c['Clean_Resume_Link'] = None
    
    return df_c, df_o, df_i

def extract_text_from_pdf(url):
    if not url or pd.isna(url): return ""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            f = io.BytesIO(response.content)
            reader = PdfReader(f)
            text = "".join(page.extract_text() for page in reader.pages)
            return text
    except Exception:
        return ""
    return ""

def evaluate_resume_with_ai(api_key, resume_text, tasks_list, extra_reqs):
    if not resume_text.strip():
        return 0, "No readable text found in resume."
    
    client = OpenAI(api_key=api_key)
    extra_reqs_text = "\n".join([f"- {req}" for req in extra_reqs]) if extra_reqs else "None."
    
    prompt = f"""
    You are an expert HR recruiter. Evaluate the candidate's resume against the standard job tasks and any additional custom requirements requested by the hiring manager.
    
    Standard Required Tasks:
    {', '.join(tasks_list)}
    
    Additional Custom Requirements (Prioritize these heavily):
    {extra_reqs_text}
    
    Resume Text:
    {resume_text[:4000]}
    
    Return a JSON object with two keys:
    1. "score": An integer from 0 to 100 representing how well the candidate's skills match the tasks and additional requirements.
    2. "justification": A one-sentence explanation for the score, specifically referencing if they met the additional custom requirements.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        result = json.loads(response.choices[0].message.content)
        return int(result.get("score", 0)), result.get("justification", "AI processing completed.")
    except Exception as e:
        return 0, f"AI Error: {str(e)}"

def score_candidate(candidate, opportunity, dyn_country, dyn_industry, dyn_gender, interview_data, tasks_list, extra_reqs, api_key):
    score = 0
    breakdown = []

    # --- NAME EXCLUSION LOGIC ---
    cand_name = str(candidate.get('Candidate Name', '')).strip().lower()
    for req in extra_reqs:
        req_lower = req.lower()
        if any(word in req_lower for word in ['remove', 'exclude', 'drop', 'ignore', 'skip']):
            if cand_name in req_lower:
                return 0, ["Manually excluded via chat request"]

    # Dynamic Country Filter
    cand_country = str(candidate.get('Country', '')).strip()
    if dyn_country.lower() != 'any':
        if dyn_country.lower() != cand_country.lower():
            return 0, ["Missed Country Requirement"]

    # Dynamic Gender Filter
    cand_gender = str(candidate.get('Gender', '')).strip()
    if dyn_gender.lower() not in ['nan', 'no preference', 'both', 'any', '']:
        if dyn_gender.lower() != cand_gender.lower():
            return 0, ["Missed Gender Requirement"]

    # Dynamic Industry Match
    cand_school = str(candidate.get('School', '')).strip()
    if dyn_industry.lower() == cand_school.lower() and dyn_industry != "":
        score += 20
        breakdown.append("Industry/School Match (+20)")

    if not interview_data.empty:
        feedback = interview_data[interview_data['Candidate Name'].str.lower() == cand_name]
        if not feedback.empty:
            status = str(feedback.iloc[0].get('Status', '')).lower()
            rating = str(feedback.iloc[0].get('Total Score', '')).lower()
            if status == 'selected': score += 30; breakdown.append("Feedback: Selected (+30)")
            elif status == 'not selected': score -= 10; breakdown.append("Feedback: Not Selected (-10)")
            if 'good' in rating or 'passed' in rating: score += 10; breakdown.append("Feedback: Good Score (+10)")

    required_skills = [task for task in tasks_list if 'yes' in str(opportunity.get(task, '')).lower() or 'occasional' in str(opportunity.get(task, '')).lower()]
    
    resume_url = candidate.get('Clean_Resume_Link')
    if resume_url and (required_skills or extra_reqs):
        resume_text = extract_text_from_pdf(resume_url)
        ai_score, ai_justification = evaluate_resume_with_ai(api_key, resume_text, required_skills, extra_reqs)
        scale_factor = 0.7 if extra_reqs else 0.5
        scaled_ai_score = int(ai_score * scale_factor) 
        score += scaled_ai_score
        breakdown.append(f"AI Score: {ai_score}/100 - {ai_justification}")

    return score, breakdown

def generate_shortlist(df_cand, job_row, dyn_country, dyn_industry, dyn_gender, df_int, task_columns, extra_reqs, api_key):
    results = []
    progress_bar = st.progress(0, text="AI is reading resumes and analyzing requirements...")
    total_cands = len(df_cand)
    
    for index, cand in df_cand.iterrows():
        progress_bar.progress((index + 1) / total_cands, text=f"Analyzing candidate {index + 1} of {total_cands}...")
        final_score, notes = score_candidate(cand, job_row, dyn_country, dyn_industry, dyn_gender, df_int, task_columns, extra_reqs, api_key)
        
        if final_score > 0:
            results.append({
                "Candidate Name": cand['Candidate Name'],
                "Email": cand['Personal Email'],
                "Match Score": final_score,
                "Country": cand['Country'],
                "School": cand['School'],
                "Resume": cand['Clean_Resume_Link'],
                "Match Notes": " | ".join(notes)
            })
    
    progress_bar.empty()
    if results:
        results_df = pd.DataFrame(results).sort_values(by="Match Score", ascending=False)
        st.session_state.shortlist_results = results_df
    else:
        st.session_state.shortlist_results = pd.DataFrame()


# --- MAIN APP LAYOUT ---

if os.path.isfile("Edge_Logomark_Plum.jpg"):
    st.sidebar.image("Edge_Logomark_Plum.jpg", width=100)

st.sidebar.title("Talent Shortlister")
st.sidebar.markdown("---")

openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
uploaded_cand = st.sidebar.file_uploader("Upload Candidate Info", type="csv")
uploaded_opp = st.sidebar.file_uploader("Upload Opportunity Info", type="csv")
uploaded_int = st.sidebar.file_uploader("Upload Interview Feedback (Optional)", type="csv")

if st.sidebar.button("Clear AI Chat History"):
    st.session_state.extra_requirements = []
    st.session_state.shortlist_results = None
    st.rerun()

if uploaded_cand and uploaded_opp:
    if not openai_api_key:
        st.warning("Please enter your OpenAI API key in the sidebar to enable resume analysis.")
        st.stop()

    df_cand, df_opp, df_int = load_and_clean_data(uploaded_cand, uploaded_opp, uploaded_int)
    
    st.header("1. Job Details & Dynamic Filters")
    opp_list = df_opp['Opportunity: Opportunity Name'].dropna().unique()
    selected_opp_name = st.selectbox("Choose a Job to Shortlist For:", opp_list)
    
    job_row = df_opp[df_opp['Opportunity: Opportunity Name'] == selected_opp_name].iloc[0]
    task_columns = df_opp.columns[10:40] 

    # --- DYNAMIC OVERRIDE UI ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1: 
        dyn_industry = st.text_input("Industry / School Match", value=str(job_row.get('Industry', '')))
        
    with col2: 
        cand_countries = [str(c).strip() for c in df_cand['Country'].dropna().unique() if str(c).strip() != '']
        all_countries = ["Any"] + sorted(list(set(cand_countries)))
        
        default_c = str(job_row.get('Country Preference', 'Any')).strip()
        if pd.isna(default_c) or default_c == '' or default_c.lower() in ['no preference', 'nan']:
            default_c = "Any"
        if default_c not in all_countries and default_c != "Any":
            all_countries.append(default_c)
            
        dyn_country = st.selectbox("Target Country", options=all_countries, index=all_countries.index(default_c))
        
    with col3: 
        default_g = str(job_row.get('Gender', 'Any')).strip().capitalize()
        if default_g not in ["Male", "Female", "Both", "Any"]: default_g = "Any"
        dyn_gender = st.selectbox("Target Gender", options=["Any", "Male", "Female", "Both"], index=["Any", "Male", "Female", "Both"].index(default_g))
        
    with col4: 
        dyn_placements = st.number_input("Placements Needed", min_value=1, value=int(job_row.get('Placements', 1)))

    st.markdown("---")
    
    # Generate Button
    if st.button("Generate Initial Shortlist"):
        st.session_state.extra_requirements = [] 
        generate_shortlist(df_cand, job_row, dyn_country, dyn_industry, dyn_gender, df_int, task_columns, st.session_state.extra_requirements, openai_api_key)

    # Display Results & Chat
    if st.session_state.shortlist_results is not None:
        st.header("2. Shortlist Results")
        
        if not st.session_state.shortlist_results.empty:
            shortlist_count = int(dyn_placements) * 4
            shortlist = st.session_state.shortlist_results.head(shortlist_count)
            
            st.success(f"Found matching candidates based on JD and {len(st.session_state.extra_requirements)} custom requirements.")
            
            st.dataframe(
                shortlist,
                column_config={
                    "Resume": st.column_config.LinkColumn("Resume Link"),
                    "Match Score": st.column_config.ProgressColumn("Fit Score", min_value=0, max_value=120, format="%d")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.warning("No candidates matched the criteria.")

        st.markdown("---")
        
        # --- CHAT INTERFACE ---
        st.header("💬 Refine with AI")
        st.caption("Tell the AI Recruiter what else to look for. (e.g., 'Only show candidates with pediatric experience' or 'Remove Ramsha Durrani')")
        
        for req in st.session_state.extra_requirements:
            with st.chat_message("user", avatar="👤"):
                st.write(f"Requirement Added: **{req}**")

        if new_req := st.chat_input("Enter a new requirement..."):
            st.session_state.extra_requirements.append(new_req)
            
            with st.chat_message("user", avatar="👤"):
                st.write(f"Requirement Added: **{new_req}**")
                
            with st.spinner("AI is re-analyzing resumes against your new requirement..."):
                generate_shortlist(df_cand, job_row, dyn_country, dyn_industry, dyn_gender, df_int, task_columns, st.session_state.extra_requirements, openai_api_key)
            st.rerun()

else:
    st.info("Please upload the required CSV files and provide an API key in the sidebar.")
