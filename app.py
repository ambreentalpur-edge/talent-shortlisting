import streamlit as st
import os

# --- LOGO PATHS ---
tab_logo = "logo.jpg"            
app_logo = "Edge_Lockup_H_Plum.jpg" 

# --- 1. SET BROWSER TAB ICON ---
st.set_page_config(
    page_title="EdgeOS", 
    page_icon=tab_logo if os.path.exists(tab_logo) else "🟣",
    layout="wide"
)

# --- 2. SET SIDEBAR LOGO (FIXED SIZE) ---
if os.path.exists(app_logo):
    # Adjust 'width' (e.g., 100 or 150) until it looks right to you
    st.sidebar.image(app_logo, width=120) 
else:
    st.sidebar.title("EdgeOS")


# --- DATA LOADING ---
def load_data(cand_file, opp_file):
    try:
        df_c = pd.read_csv(cand_file)
        df_o = pd.read_csv(opp_file)
        
        # Standardize Salesforce Column Names
        if 'Candidate: Candidate Name' in df_c.columns:
            df_c.rename(columns={'Candidate: Candidate Name': 'Candidate Name'}, inplace=True)
            
        return df_c, df_o
    except Exception as e:
        st.error(f"Error loading files: {e}")
        return None, None

# --- AI ANALYSIS LOGIC ---
def analyze_with_ai(api_key, resume_text, job_tasks, model="gpt-4o-mini"):
    client = OpenAI(api_key=api_key)
    
    # Prompting the AI to return a specific JSON format
    prompt = f"""
    You are an expert recruiter. Score this resume (0-100) based strictly on these job tasks: {job_tasks}.
    Focus on transferable skills and experience.
    
    Resume Text: {str(resume_text)[:5000]} 
    
    Return ONLY a JSON object:
    {{
        "score": int,
        "justification": "One sentence explaining the score."
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            response_format={ "type": "json_object" },
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {"score": 0, "justification": "Analysis error."}

# --- UI LAYOUT ---
# 1. Create two columns for the header alignment
header_logo = "Edge_Lockup_Plum.jpg"
col1, col2 = st.columns([1, 6]) # Adjust the numbers to change spacing

with col1:
    if os.path.exists(header_logo):
        # Setting a width of 80 to 100 usually works best for a title icon
        st.image(header_logo, width=100)

with col2:
    st.title("EdgeOS")
st.markdown("### Talent Matching & AI Shortlisting")

# Sidebar for Settings
st.sidebar.header("Settings")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")
uploaded_cand = st.sidebar.file_uploader("Upload Scraped Candidate CSV", type="csv")
uploaded_opp = st.sidebar.file_uploader("Upload Opportunity CSV", type="csv")

if uploaded_cand and uploaded_opp:
    df_c, df_o = load_data(uploaded_cand, uploaded_opp)
    
    if df_c is not None and df_o is not None:
        # Step 1: Select the Job
        st.write("---")
        opp_list = df_o['Opportunity: Opportunity Name'].unique()
        selected_job = st.selectbox("Select Target Opportunity", opp_list)
        
        # Get Job Details (Tasks/Description)
        job_row = df_o[df_o['Opportunity: Opportunity Name'] == selected_job].iloc[0]
        # Assuming tasks start around index 10 in your CSV, adjust as needed
        job_tasks = job_row.iloc[10:40].dropna().tolist()

        # Step 2: Run Shortlist
        if st.button("🚀 Run AI Shortlisting"):
            if not api_key:
                st.warning("Please enter your OpenAI API key in the sidebar.")
            else:
                # Filter out candidates with empty resume text
                valid_cands = df_c[df_c['Resume Text'].notna()].head(50) # Set limit for speed/cost
                
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, (idx, cand) in enumerate(valid_cands.iterrows()):
                    status_text.text(f"Analyzing: {cand['Candidate Name']}...")
                    res = analyze_with_ai(api_key, cand['Resume Text'], job_tasks)
                    
                    results.append({
                        "Name": cand['Candidate Name'],
                        "Score": res['score'],
                        "Justification": res['justification']
                    })
                    progress_bar.progress((i + 1) / len(valid_cands))

                st.session_state.shortlist_results = pd.DataFrame(results).sort_values(by="Score", ascending=False)
                status_text.text("Shortlisting Complete!")

        # Step 3: Display Results
        if st.session_state.shortlist_results is not None:
            st.write("### AI-Ranked Candidates")
            st.dataframe(st.session_state.shortlist_results, use_container_width=True)
            
            # Export Button
            csv_output = st.session_state.shortlist_results.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Shortlist", csv_output, "shortlist.csv", "text/csv")
else:
    st.info("Please upload your Scraped Candidate CSV and Opportunity CSV to begin.")
