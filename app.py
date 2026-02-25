import streamlit as st
import pandas as pd
import requests
import io
from bs4 import BeautifulSoup
import re
from pypdf import PdfReader
from openai import OpenAI
import json

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Edge Talent Shortlister",
    page_icon="🟣",
    layout="wide"
)

# --- BRANDING CSS ---
st.markdown("""
    <style>
    h1, h2, h3 { color: #4a0f70 !important; font-family: 'Helvetica', sans-serif; }
    div.stButton > button { background-color: #4a0f70; color: white; border-radius: 8px; border: none; font-weight: bold; }
    div.stButton > button:hover { background-color: #914de8; color: white; }
    [data-testid="stSidebar"] { background-color: #003731; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] label { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---

@st.cache_data
def load_and_clean_data(cand_file, opp_file, int_file):
    df_c = pd.read_csv(cand_file)
    df_o = pd.read_csv(opp_file)
    
    # Process interview feedback only if uploaded
    if int_file is not None:
        df_i = pd.read_csv(int_file)
        if 'Candidate: Candidate Name' in df_i.columns:
            df_i['Candidate Name'] = df_i['Candidate: Candidate Name'].str.strip()
    else:
        df_i = pd.DataFrame() # Empty dataframe if not provided

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

def evaluate_resume_with_ai(api_key, resume_text, tasks_list):
    """Calls OpenAI API to evaluate the resume against the required tasks."""
    if not resume_text.strip():
        return 0, "No readable text found in resume."
    
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
    You are an expert HR recruiter. Evaluate the candidate's resume against the required tasks for an open position.
    
    Required Tasks:
    {', '.join(tasks_list)}
    
    Resume Text:
    {resume_text[:4000]} # Limiting to 4000 characters to manage token usage
    
    Return a JSON object with two keys:
    1. "score": An integer from 0 to 100 representing how well the candidate's skills match the required tasks.
    2. "justification": A one-sentence explanation for the score.
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

def score_candidate(candidate, opportunity, interview_data, tasks_list, api_key):
    score = 0
    breakdown = []

    # 1. HARD FILTERS
    opp_country = str(opportunity.get('Country Preference', '')).strip()
    cand_country = str(candidate.get('Country', '')).strip()
    if opp_country and opp_country.lower() not in ['nan', 'no preference', 'any', '']:
        if opp_country.lower() != cand_country.lower():
            return 0, ["Missed Country Requirement"]

    opp_gender = str(opportunity.get('Gender', '')).strip()
    cand_gender = str(candidate.get('Gender', '')).strip()
    if opp_gender.lower() not in ['nan', 'no preference', 'both', '']:
        if opp_gender.lower() != cand_gender.lower():
            return 0, ["Missed Gender Requirement"]

    # 2. INDUSTRY MATCH
    opp_industry = str(opportunity.get('Industry', '')).strip()
    cand_school = str(candidate.get('School', '')).strip()
    if opp_industry.lower() == cand_school.lower():
        score += 20
        breakdown.append("Industry/School Match (+20)")

    # 3. INTERVIEW FEEDBACK (OPTIONAL)
    if not interview_data.empty:
        cand_name = candidate.get('Candidate Name', '')
        feedback = interview_data[interview_data['Candidate Name'] == cand_name]
        
        if not feedback.empty:
            status = str(feedback.iloc[0].get('Status', '')).lower()
            rating = str(feedback.iloc[0].get('Total Score', '')).lower()
            
            if status == 'selected':
                score += 30
                breakdown.append("Feedback: Selected (+30)")
            elif status == 'not selected':
                score -= 10
                breakdown.append("Feedback: Not Selected (-10)")
            
            if 'good' in rating or 'passed' in rating:
                score += 10
                breakdown.append("Feedback: Good Score (+10)")

    # 4. AI RESUME MATCHING
    required_skills = [task for task in tasks_list if 'yes' in str(opportunity.get(task, '')).lower() or 'occasional' in str(opportunity.get(task, '')).lower()]
    
    resume_url = candidate.get('Clean_Resume_Link')
    if resume_url and required_skills:
        resume_text = extract_text_from_pdf(resume_url)
        ai_score, ai_justification = evaluate_resume_with_ai(api_key, resume_text, required_skills)
        
        # Scale the AI score to a maximum of 50 points to balance with other metrics
        scaled_ai_score = int(ai_score * 0.5) 
        score += scaled_ai_score
        breakdown.append(f"AI Match Score: {ai_score}/100 (+{scaled_ai_score} pts) - {ai_justification}")

    return score, breakdown

# --- MAIN APP LAYOUT ---

st.sidebar.image("Edge_Logomark_Plum.jpg", width=100)
st.sidebar.title("Talent Shortlister")
st.sidebar.markdown("---")

# API Configuration
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")

uploaded_cand = st.sidebar.file_uploader("Upload Candidate Info", type="csv")
uploaded_opp = st.sidebar.file_uploader("Upload Opportunity Info", type="csv")
uploaded_int = st.sidebar.file_uploader("Upload Interview Feedback (Optional)", type="csv")

if uploaded_cand and uploaded_opp:
    if not openai_api_key:
        st.warning("Please enter your OpenAI API key in the sidebar to enable resume analysis.")
        st.stop()

    df_cand, df_opp, df_int = load_and_clean_data(uploaded_cand, uploaded_opp, uploaded_int)
    
    st.header("1. Select an Opportunity")
    opp_list = df_opp['Opportunity: Opportunity Name'].dropna().unique()
    selected_opp_name = st.selectbox("Choose a Job to Shortlist For:", opp_list)
    
    job_row = df_opp[df_opp['Opportunity: Opportunity Name'] == selected_opp_name].iloc[0]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Industry", job_row.get('Industry', 'N/A'))
    with col2: st.metric("Country", job_row.get('Country Preference', 'Any'))
    with col3: st.metric("Placements Needed", job_row.get('Placements', 1))
    with col4: st.metric("Target Shortlist", int(job_row.get('Placements', 1)) * 4)

    # Identify Task Columns - Adjust indices if necessary
    task_columns = df_opp.columns[10:40] 

    if st.button("Run Shortlisting Algorithm"):
        results = []
        progress_bar = st.progress(0)
        total_cands = len(df_cand)
        
        for index, cand in df_cand.iterrows():
            progress_bar.progress((index + 1) / total_cands)
            
            final_score, notes = score_candidate(cand, job_row, df_int, task_columns, openai_api_key)
            
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
            placements = int(job_row.get('Placements', 1))
            shortlist_count = placements * 4
            shortlist = results_df.head(shortlist_count)
            
            st.success(f"Found {len(shortlist)} matching candidates.")
            
            st.dataframe(
                shortlist,
                column_config={
                    "Resume": st.column_config.LinkColumn("Resume Link"),
                    "Match Score": st.column_config.ProgressColumn("Fit Score", min_value=0, max_value=120, format="%d")
                },
                hide_index=True,
                use_container_width=True
            )
            
            csv = shortlist.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Shortlist CSV",
                data=csv,
                file_name=f"Shortlist_{selected_opp_name}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No candidates matched the criteria.")

else:
    st.info("Please upload the required CSV files and provide an API key in the sidebar.")
