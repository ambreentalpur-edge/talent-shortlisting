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
import urllib.parse
import html

# === PAGE CONFIGURATION & STATE ===
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
if "current_job" not in st.session_state:
    st.session_state.current_job = None

# === BRANDING CSS ===
st.markdown("""
    <style>
    h1, h2, h3 { color: #4a0f70 !important; font-family: 'Helvetica', sans-serif; }
    div.stButton > button { background-color: #4a0f70; color: white; border-radius: 8px; border: none; font-weight: bold; }
    div.stButton > button:hover { background-color: #914de8; color: white; }
    [data-testid="stSidebar"] { background-color: #f5f3fa; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] label { color: #4a0f70 !important; }
    </style>
    """, unsafe_allow_html=True)

# === FUNCTIONS ===

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
    
    # === THE FIX: Rename the messy Salesforce column in Candidate file ===
    if 'Candidate: Candidate Name' in df_c.columns:
        df_c.rename(columns={'Candidate: Candidate Name': 'Candidate Name'}, inplace=True)
    
    if int_file is not None:
        df_i = read_csv_safe(int_file)
        if 'Candidate: Candidate Name' in df_i.columns:
            df_i['Candidate Name'] = df_i['Candidate: Candidate Name'].str.strip()
    else:
        df_i = pd.DataFrame()

    def extract_link(html_string):
        if pd.isna(html_string) or str(html_string).strip() == "": 
            return None
        raw_string = str(html_string)
        
        # 1. Best Method: Grab the visible text of the link
        try:
            soup = BeautifulSoup(raw_string, 'html.parser')
            tag = soup.find('a')
            if tag and tag.text.strip().startswith('http'):
                return tag.text.strip()
        except:
            pass
        
        # 2. Fallback Method
        try:
            decoded = urllib.parse.unquote(raw_string)
            urls = re.findall(r'(https?://[^\s\'"<>]+)', decoded)
            if urls: return urls[0]
        except:
            pass
        return None

    if 'Public link' in df_c.columns:
        df_c['Clean_Resume_Link'] = df_c['Public link'].apply(extract_link)
    else:
        df_c['Clean_Resume_Link'] = None
    
    return df_c, df_o, df_i

def extract_text_from_pdf(url):
    if not url or pd.isna(url): return ""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        session = requests.Session()
        res = session.get(url, headers=headers, timeout=10)
        
        # === SALESFORCE BYPASS LOGIC ===
        if "salesforce.com" in url and b'%PDF' not in res.content[:10]:
            match = re.search(r'(/sfc/(?:dist|servlet)[^\'"]*download[^\'"]*)', res.text)
            if match:
                parsed = urllib.parse.urlparse(url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                direct_url = base_url + html.unescape(match.group(1))
                res = session.get(direct_url, headers=headers, timeout=10)
                
        if res.status_code == 200 and b'%PDF' in res.content[:10]:
            f = io.BytesIO(res.content)
            reader = PdfReader(f)
            text = "".join(page.extract_text() for page in reader.pages)
            return text
        else:
            return ""
    except Exception:
        return ""

def evaluate_resume_with_ai(api_key, resume_text, tasks_list, extra_reqs):
    if not resume_text.strip():
        return 0, "No readable text found in resume."
    
    client = OpenAI(api_key=api_key)
    extra_reqs_text = "\n".join([f"- {req}" for req in extra_reqs]) if extra_reqs else "None."
    
    prompt = f"""
    You are an expert HR recruiter. Evaluate the candidate's resume against the standard job tasks and any custom requirements.
    
    Standard Required Tasks:
    {', '.join(tasks_list)}
    
    Additional Custom Requirements:
    {extra_reqs_text}
    
    IMPORTANT SCORING RULES:
    1. Do not require a 100% perfect exact keyword match. Score based on the highest degree of overall capability.
    2. Strongly consider TRANSFERABLE SKILLS. If a candidate has broad experience (like "inbound and outbound calls", "call center", or "customer support"), credit them for specific sub-tasks related to that experience (like scheduling, triaging, voicemails, or general inquiries).
    3. Reward candidates who demonstrate the core competencies needed to perform the required tasks even if they use different terminology.
    
    Resume Text:
    {resume_text[:4000]}
    
    Return a JSON object with two keys:
    1. "score": An integer from 0 to 100 representing their alignment based on the rules above.
    2. "justification": A one-sentence explanation for the score highlighting their transferable skills.
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
    breakdown = []

    # === 1. STRICT HARD FILTERS ===
    resume_url = candidate.get('Clean_Resume_Link')
    if not resume_url or pd.isna(resume_url):
        return 0, ["Disqualified: No Resume Link Found in CSV"]

    cand_name = str(candidate.get('Candidate Name', '')).strip().lower()
    for req in extra_reqs:
        req_lower = req.lower()
        if any(word in req_lower for word in ['remove', 'exclude', 'drop', 'ignore', 'skip']):
            if cand_name in req_lower:
                return 0, ["Manually excluded via chat request"]

    cand_country = str(candidate.get('Country', '')).strip()
    if dyn_country.lower() != 'any':
        if dyn_country.lower() != cand_country.lower():
            return 0, [f"Missed Country Requirement (Needs {dyn_country}, has {cand_country})"]

    cand_gender = str(candidate.get('Gender', '')).strip()
    if dyn_gender.lower() not in ['nan', 'no preference', 'both', 'any', '']:
        if dyn_gender.lower() != cand_gender.lower():
            return 0, [f"Missed Gender Requirement (Needs {dyn_gender}, has {cand_gender})"]

    # === 2. STRICT RESUME MATCHING (NO SAFETY NET) ===
    required_skills = [task for task in tasks_list if 'yes' in str(opportunity.get(task, '')).lower() or 'occasional' in str(opportunity.get(task, '')).lower()]
    
    resume_text = extract_text_from_pdf(resume_url)
    
    if not resume_text.strip():
        return 0, ["Disqualified: Could not extract text from the resume link (Salesforce Block or Scanned Image)"]

    ai_score, ai_justification = evaluate_resume_with_ai(api_key, resume_text, required_skills, extra_reqs)
    final_score = ai_score
    breakdown.append(f"AI Match: {ai_score}% | {ai_justification}")

    # === 3. SUPPLEMENTARY INFO ===
    cand_school = str(candidate.get('School', '')).strip()
    if dyn_industry.lower() == cand_school.lower() and dyn_industry != "":
        breakdown.append("Industry Matches JD")

    if not interview_data.empty:
        feedback = interview_data[interview_data['Candidate Name'].str.lower() == cand_name]
        if not feedback.empty:
            status = str(feedback.iloc[0].get('Status', '')).lower()
            if status == 'selected': breakdown.append("Past Feedback: Selected")
            elif status == 'not selected': breakdown.append("Past Feedback: Not Selected")

    return final_score, breakdown

def generate_shortlist(df_cand, job_row, dyn_country, dyn_industry, dyn_gender, df_int, task_columns, extra_reqs, api_key):
    results = []
    progress_bar = st.progress(0, text="AI is reading resumes and analyzing requirements...")
    total_cands = len(df_cand)
    
    for index, cand in df_cand.iterrows():
        progress_bar.progress((index + 1) / total_cands, text=f"Analyzing candidate {index + 1} of {total_cands}...")
        final_score, notes = score_candidate(cand, job_row, dyn_country, dyn_industry, dyn_gender, df_int, task_columns, extra_reqs, api_key)
        
        if final_score >= 0:
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


# === MAIN APP LAYOUT ===

if os.path.isfile("Edge_Logomark_Plum.jpg"):
    st.sidebar.image("Edge_Logomark_Plum.jpg", width=100)

st.sidebar.title("Edge Navigator")
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
    
    tab1, tab2 = st.tabs(["🎯 AI Shortlister", "🔍 Talent Search Database"])
    
    # ==========================================
    # TAB 1: AI JOB SHORTLISTER
    # ==========================================
    with tab1:
        st.header("1. Job Details & Dynamic Filters")
        opp_list = df_opp['Opportunity: Opportunity Name'].dropna().unique()
        selected_opp_name = st.selectbox("Choose a Job to Shortlist For:", opp_list)
        
        if st.session_state.current_job != selected_opp_name:
            st.session_state.current_job = selected_opp_name
            st.session_state.shortlist_results = None
            st.session_state.extra_requirements = []
        
        job_row = df_opp[df_opp['Opportunity: Opportunity Name'] == selected_opp_name].iloc[0]
        task_columns = df_opp.columns[10:40] 

        col1, col2, col3, col4 = st.columns(4)
        with col1: dyn_industry = st.text_input("Industry Match", value=str(job_row.get('Industry', '')))
        with col2: 
            cand_countries = [str(c).strip() for c in df_cand['Country'].dropna().unique() if str(c).strip() != '']
            all_countries = ["Any"] + sorted(list(set(cand_countries)))
            default_c = str(job_row.get('Country Preference', 'Any')).strip()
            if pd.isna(default_c) or default_c == '' or default_c.lower() in ['no preference', 'nan']: default_c = "Any"
            if default_c not in all_countries and default_c != "Any": all_countries.append(default_c)
            dyn_country = st.selectbox("Target Country", options=all_countries, index=all_countries.index(default_c))
        with col3: 
            default_g = str(job_row.get('Gender', 'Any')).strip().capitalize()
            if default_g not in ["Male", "Female", "Both", "Any"]: default_g = "Any"
            dyn_gender = st.selectbox("Target Gender", options=["Any", "Male", "Female", "Both"], index=["Any", "Male", "Female", "Both"].index(default_g))
        with col4: dyn_placements = st.number_input("Placements Needed", min_value=1, value=int(job_row.get('Placements', 1)))

        st.markdown("---")
        
        if st.button("Generate Initial Shortlist"):
            st.session_state.extra_requirements = [] 
            generate_shortlist(df_cand, job_row, dyn_country, dyn_industry, dyn_gender, df_int, task_columns, st.session_state.extra_requirements, openai_api_key)

        if st.session_state.shortlist_results is not None:
            st.header("2. Shortlist Results")
            if not st.session_state.shortlist_results.empty:
                shortlist_count = int(dyn_placements) * 4
                st.success(f"Displaying top matches and diagnostic notes.")
                st.dataframe(
                    st.session_state.shortlist_results.head(max(shortlist_count, 15)),
                    column_config={
                        "Resume": st.column_config.LinkColumn("Resume Link"),
                        "Match Score": st.column_config.ProgressColumn("Fit Score", min_value=0, max_value=100, format="%d")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.warning("No candidates matched the criteria.")

            st.markdown("---")
            st.header("💬 Refine with AI")
            st.caption("Tell the AI Recruiter what else to look for. (e.g., 'Only show candidates with pediatric experience' or 'Remove Ramsha')")
            
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

    # ==========================================
    # TAB 2: TALENT SEARCH DATABASE
    # ==========================================
    with tab2:
        st.header("Talent Search Database")
        st.markdown("Instantly filter your entire candidate pool by specific skills, background, or demographics.")
        
        if not df_int.empty:
            df_merged = pd.merge(
                df_cand, 
                df_int[['Candidate Name', 'Speciality', 'Background', 'Professional Skills', 'Status', 'Total Score']].drop_duplicates(subset=['Candidate Name']), 
                on='Candidate Name', 
                how='left'
            )
        else:
            df_merged = df_cand.copy()
            for col in ['Speciality', 'Background', 'Professional Skills', 'Status', 'Total Score']:
                df_merged[col] = ""

        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            all_countries_db = [str(c).strip() for c in df_merged['Country'].dropna().unique() if str(c).strip() != '']
            filter_country = st.multiselect("Filter by Country", options=sorted(all_countries_db))
        with f_col2:
            all_schools_db = [str(s).strip() for s in df_merged['School'].dropna().unique() if str(s).strip() != '']
            filter_industry = st.multiselect("Filter by Industry (School)", options=sorted(all_schools_db))
        with f_col3:
            filter_keyword = st.text_input("🔍 Search Skills/Experience (e.g. Scheduling, Triage)")

        filtered_df = df_merged.copy()
        
        if filter_country:
            filtered_df = filtered_df[filtered_df['Country'].isin(filter_country)]
        if filter_industry:
            filtered_df = filtered_df[filtered_df['School'].isin(filter_industry)]
        if filter_keyword:
            search_cols = ['Speciality', 'Background', 'Professional Skills', 'School']
            for col in search_cols:
                if col in filtered_df.columns:
                    filtered_df[col] = filtered_df[col].fillna("")
            
            mask = filtered_df[search_cols].apply(lambda x: x.str.contains(filter_keyword, case=False, na=False)).any(axis=1)
            filtered_df = filtered_df[mask]

        st.success(f"Found {len(filtered_df)} candidates matching your criteria.")
        
        st.dataframe(
            filtered_df[['Candidate Name', 'Personal Email', 'Country', 'School', 'Speciality', 'Background', 'Professional Skills', 'Status', 'Clean_Resume_Link']],
            column_config={
                "Clean_Resume_Link": st.column_config.LinkColumn("Resume Link"),
                "Personal Email": st.column_config.TextColumn("Email")
            },
            hide_index=True,
            use_container_width=True
        )

else:
    st.info("Please upload the required CSV files and provide an API key in the sidebar.")
