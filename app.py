import streamlit as st
import pandas as pd
import plotly.express as px
from src.resume_parser import pdf_to_text, parse_resume
from src.job_parser import parse_job_description
from src.similarity import analyze_match
from src.llm import generate
from src.prompts import resume_improvement_prompt, interview_prompt, career_blueprint_prompt
from src.roadmap import make_roadmap
from src.interview import fallback_questions, evaluate_answer
from src.rag import retrieve
from src.evaluation import prompt_comparison

st.set_page_config(page_title="Generative Career Assistant", page_icon="🎯", layout="wide")
st.markdown("""<style>
 .stApp {background:#fff; color:#161616; font-family:Arial, sans-serif;}
 [data-testid="stHeader"] {background:rgba(255,255,255,.96);}
 .block-container {max-width:1250px; padding-top:1.2rem;}
 [data-testid="stMetric"] {background:#fff; border:1px solid #e7e7e7; border-radius:8px; padding:14px; box-shadow:none;}
 .topline {border-bottom:1px solid #eee; padding-bottom:10px; margin-bottom:8px;}
 .hero-copy {padding:64px 5px 25px 55px;}
 .hero-copy h1 {font-size:4.1rem; line-height:1.03; letter-spacing:-.19rem; margin:0 0 25px; font-weight:800; color:#050505;}
 .hero-copy p {font-size:1.25rem; line-height:1.6; max-width:580px; color:#363636;}
 .resume-card {background:#fff; width:365px; min-height:465px; padding:27px 26px; margin:32px auto; border-top:13px solid #365cf5; box-shadow:0 12px 28px rgba(0,0,0,.18); color:#252525; font-family:Arial,sans-serif;}
 .resume-name {font-weight:800; color:#365cf5; font-size:1.22rem; margin:9px 0 16px;}
 .resume-rule {height:3px; background:#365cf5; margin:16px 0 7px;}
 .resume-label {font-size:.55rem; font-weight:800; color:#365cf5; letter-spacing:.08em;}
 .resume-lines {font-size:.57rem; line-height:1.45; color:#555;}
 .trust {display:inline-block; background:#f3f5ff; padding:11px 18px; border-radius:7px; font-weight:600; margin:12px 0;}
 .green {color:#00a878; font-weight:800;}
 .stButton>button {border-radius:27px; font-size:1rem; font-weight:700; min-height:3.7rem; padding:0 30px;}
 .stButton>button[kind="primary"] {background:#123b6d; border-color:#123b6d; color:#fff;}
 .stButton>button[kind="secondary"] {background:#f0f1f3; border-color:#f0f1f3; color:#262626;}
 [data-testid="stFileUploader"] {background:#f7f8fb; border:1px dashed #aeb8cc; border-radius:10px; padding:10px 14px;}
 [data-testid="stFileUploader"] button {background:#ffffff !important; border:1px solid #365cf5 !important; color:#2447c8 !important; font-weight:700 !important;}
 [data-testid="stFileUploader"] button * {color:#2447c8 !important;}
 [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] span {color:#424b5b !important;}
 textarea {background:#17233a !important; color:#ffffff !important; caret-color:#ffffff !important; border:1px solid #35527e !important;}
 textarea::placeholder {color:#c2cbda !important; opacity:1;}
 .helper {background:#f6f8fc; border:1px solid #e2e7f1; border-radius:10px; padding:18px 20px; margin:12px 0 20px; color:#394150;}
 .helper b {color:#1c2848;}
 .form-title {font-size:2rem; font-weight:800; letter-spacing:-.07rem; margin:18px 0 4px;}
 .nav-button .stButton>button {min-height:2.5rem; font-size:.83rem; border-radius:6px; padding:0 12px;}
 @media(max-width:850px) {.hero-copy {padding:25px 10px;}.hero-copy h1{font-size:2.75rem;}.resume-card{width:82%;}}
 </style>""", unsafe_allow_html=True)
st.markdown("<div class='topline'></div>", unsafe_allow_html=True)

def ready(): return "resume" in st.session_state and "job" in st.session_state
def load_resume(upload):
    st.session_state.resume = parse_resume(pdf_to_text(upload))
def load_job(text, upload):
    if upload: text = pdf_to_text(upload) if upload.name.lower().endswith(".pdf") else upload.getvalue().decode("utf-8", errors="replace")
    st.session_state.job = parse_job_description(text)
def need_data():
    if not ready(): st.info("First add a resume and job description on the **Home** page."); return True
    return False

def intake_form():
    """One friendly entry point for the documents used across the app."""
    if "resume" not in st.session_state:
        st.markdown("<div class='form-title'>Get your personalised career plan</div><p>Begin by uploading your resume. The next step will open automatically.</p>", unsafe_allow_html=True)
        st.markdown("<div class='helper'><b>Step 1 of 2 — Upload your resume</b><br>Use a PDF resume. We will extract the skills and projects you already have, so every recommendation stays truthful.</div>", unsafe_allow_html=True)
        uploaded=st.file_uploader("Your resume (PDF)", type="pdf", key="home_resume")
        if uploaded:
            try:
                load_resume(uploaded)
                st.rerun()
            except ValueError as e:
                st.error(str(e))
        return
    r=st.session_state.resume
    st.markdown("<div class='form-title'>Resume uploaded successfully</div><p>Great—your resume is ready. Now add the job you want to target.</p>", unsafe_allow_html=True)
    st.markdown(f"<div class='helper'><b>✓ Resume profile ready: {r['name']}</b><br>Detected skills: {', '.join(r['technical_skills']) or 'No specific skills detected yet'}<br><br><b>Step 2 of 2 — Add your target job below</b></div>", unsafe_allow_html=True)
    jd_text=st.text_area("Job description", height=160, key="home_jd", placeholder="Paste the job description here. Example: We are looking for a Data Analyst with Python, SQL, Excel, dashboarding, and communication skills...")
    st.caption("Or upload the job description if you have it as a document.")
    jd_file=st.file_uploader("Job description file (PDF or TXT)", type=["pdf", "txt"], key="home_jd_file")
    if st.button("Analyze my career fit", type="primary"):
        try:
            load_job(jd_text, jd_file)
            st.session_state.page="Career Studio ✨"
            st.rerun()
        except ValueError as e: st.error(str(e))

nav_pages=["Home", "Career Studio ✨", "Resume Analysis", "Job Matching", "Skill Gap", "Resume Improvement", "Career Roadmap", "Interview Preparation", "Mock Interview", "RAG Assistant", "Prompt Evaluation"]
if "page" not in st.session_state: st.session_state.page="Home"
if ready():
    st.markdown("<div class='nav-button'>", unsafe_allow_html=True)
    for row in [nav_pages[:7], nav_pages[7:]]:
        nav_cols=st.columns(len(row))
        for col, item in zip(nav_cols, row):
            with col:
                if st.button(item, key=f"nav_{item}", type="primary", use_container_width=True):
                    st.session_state.page=item
    st.markdown("</div>", unsafe_allow_html=True)
    page=st.session_state.page
else:
    page="Home"
st.divider()
controls={"role":"Data Analyst", "priority":"Skill building", "weeks":4, "depth":"practical", "tone":"supportive"}
if page == "Career Studio ✨":
    st.markdown("<div class='helper'><b>Set your plan preferences</b><br>These choices guide the Career Studio to create a plan that fits your target job and current priority. You can change them anytime.</div>", unsafe_allow_html=True)
    with st.expander("Choose plan preferences", expanded=True):
        control_cols=st.columns(5)
        controls={
            "role": control_cols[0].text_input("Target role", "Data Analyst"),
            "priority": control_cols[1].selectbox("Focus", ["Skill building", "ATS resume", "Interview confidence", "Portfolio projects"]),
            "weeks": control_cols[2].select_slider("Sprint", options=[2, 4, 6, 8, 12], value=4),
            "depth": control_cols[3].select_slider("Detail", options=["concise", "practical", "detailed"], value="practical"),
            "tone": control_cols[4].selectbox("Coach voice", ["supportive", "direct", "professional"]),
        }

if page == "Home":
    copy, preview=st.columns([1.25, .95], gap="large")
    with copy:
        st.markdown("""<div class="hero-copy"><h1>Your career,<br>made clearer.</h1><p>Turn your existing resume into a role-focused action plan. See what matches, what to learn next, and how to prepare—without making up a single detail.</p></div>""", unsafe_allow_html=True)
        action, secondary=st.columns([1, 1])
        with action:
            if st.button("Analyze my resume", type="primary", use_container_width=True): st.session_state.home_action="Resume Analysis"
        with secondary:
            if st.button("Explore career studio", use_container_width=True): st.session_state.home_action="Career Studio ✨"
        st.markdown("<div class='trust'><span class='green'>● ● ● ● ●</span>&nbsp; Evidence-based guidance for students</div>", unsafe_allow_html=True)
    with preview:
        st.markdown("""<div class="resume-card"><div class="resume-label">CAREERCRAFT / PROFILE</div><div class="resume-name">YOUR NAME</div><div class="resume-lines">Target role · Email · Portfolio<br><br>Motivated student preparing for career opportunities through practical projects and focused learning.</div><div class="resume-rule"></div><div class="resume-label">SKILLS</div><div class="resume-lines">Python · SQL · Data Analysis · Git<br>Communication · Problem Solving</div><div class="resume-rule"></div><div class="resume-label">PROJECT HIGHLIGHT</div><div class="resume-lines">Built a practical project, documented the approach, and explained the outcome clearly.</div><div class="resume-rule"></div><div class="resume-label">AI INSIGHT</div><div class="resume-lines">Upload your own resume to generate an evidence-backed plan.</div></div>""", unsafe_allow_html=True)
    st.divider()
    intake_form()
    if st.session_state.get("home_action"):
        st.info(f"Choose **{st.session_state.home_action}** in the navigation above to continue.")

elif page == "Career Studio ✨":
    if not need_data():
        match=analyze_match(st.session_state.resume, st.session_state.job)
        st.markdown(f"""<div class="hero"><div class="eyebrow">Career Studio</div><h2>{controls['role']} action sprint</h2><p>{controls['weeks']} weeks · {controls['priority']} · {controls['depth']} plan</p></div>""", unsafe_allow_html=True)
        left, mid, right=st.columns(3)
        left.metric("Match", f"{match['score']}%")
        mid.metric("Skills to strengthen", len(match["missing"]))
        right.metric("Evidence-backed skills", len(match["matching"]))
        st.caption("Change controls in the sidebar, then regenerate. This is your planning workspace—not a generic chatbot.")
        fallback = f"""## Your {controls['weeks']}-week {controls['role']} sprint

### Career positioning
Focus your applications on roles that value {', '.join(match['matching']) or 'your demonstrated coursework and projects'}. Do not claim {', '.join(match['missing']) or 'new skills'} until you have practised them.

### Resume headline
Student candidate with evidence of {', '.join(match['matching']) or 'relevant foundational work'}, preparing for {controls['role']} opportunities.

### Weekly actions
1. **Week 1:** Learn and practise {', '.join(match['missing'][:2]) or 'core job requirements'}.
2. **Week 2:** Build one small, documented practice project.
3. **Week 3:** Add truthful project bullets using action + tool + outcome.
4. **Week 4:** Rehearse STAR stories and tailor applications.

### Today
Choose one missing skill and create a 45-minute learning/practice session."""
        if st.button("✨ Generate my career blueprint", type="primary", use_container_width=True):
            prompt=career_blueprint_prompt(st.session_state.resume, st.session_state.job, match, controls)
            blueprint, live=generate(prompt, fallback)
            st.session_state.blueprint=blueprint; st.session_state.blueprint_live=live
        if "blueprint" in st.session_state:
            st.caption("Live AI blueprint" if st.session_state.blueprint_live else "Offline, evidence-based blueprint")
            st.markdown(st.session_state.blueprint)
            st.download_button("Download blueprint", st.session_state.blueprint, "career_blueprint.md", "text/markdown")

elif page == "Resume Analysis":
    st.markdown("<div class='form-title'>Your extracted resume profile</div><p>These details were found in the documents you added on the Home page.</p>", unsafe_allow_html=True)
    if "resume" not in st.session_state:
        st.info("No resume has been analysed yet. Go to **Home** and add your resume and job description.")
    if "resume" in st.session_state:
        r=st.session_state.resume
        st.subheader("Extracted resume information")
        st.write(f"**Name:** {r['name']}  |  **Email:** {r['email']}")
        st.write("**Detected technical skills:**", ", ".join(r["technical_skills"]) or "None detected")
        for title in ["education", "experience", "projects", "internships", "certifications"]:
            if r[title]: st.expander(title.title()).write(r[title])

elif page == "Job Matching":
    if not need_data():
        a=analyze_match(st.session_state.resume, st.session_state.job)
        st.metric("Overall Job Match Score", f"{a['score']}%", help="60% semantic similarity + 40% explicit skill coverage")
        st.progress(a["score"] / 100)
        st.caption(f"Semantic similarity: {a['semantic_similarity']}%")
        cols=st.columns(3)
        for col,title,values in zip(cols,["Matching skills", "Partial match", "Missing skills"],[a["matching"],a["partial"],a["missing"]]): col.subheader(title); col.write(", ".join(values) or "None")
        if a["missing_requirements"]: st.warning("Potential missing requirements:\n\n" + "\n".join("- "+x for x in a["missing_requirements"]))

elif page == "Skill Gap":
    if not need_data():
        a=analyze_match(st.session_state.resume, st.session_state.job)
        rows=[]
        for label, skills, explanation in [("Strong Match",a["matching"],"Explicitly supported by your resume."),("Partial Match",a["partial"],"Related evidence exists; describe it precisely."),("Missing",a["missing"],"Not detected; learn it before claiming it.")]:
            rows += [{"Skill":s,"Category":label,"Explanation":explanation} for s in skills]
        df=pd.DataFrame(rows or [{"Skill":"No job skills detected","Category":"—","Explanation":"Use a more detailed description."}])
        st.dataframe(df, use_container_width=True)
        st.plotly_chart(px.bar(df, x="Category", color="Category", title="Skill-gap distribution"), use_container_width=True)

elif page == "Resume Improvement":
    if not need_data():
        a=analyze_match(st.session_state.resume, st.session_state.job)
        fallback="""**Recommendations (verify against your actual experience)**\n\n- Professional summary: State your strongest matching skills: %s.\n- Project bullets: use action + tool + outcome; only include real metrics.\n- ATS keywords supported by your resume: %s.\n- Do not add missing skills (%s) until you have learned and practiced them.""" % (", ".join(a["matching"]) or "relevant coursework/projects", ", ".join(a["matching"]), ", ".join(a["missing"]))
        if st.button("Generate recommendations"):
            output, live=generate(resume_improvement_prompt(st.session_state.resume, st.session_state.job), fallback)
            st.caption("LLM-generated" if live else "Offline, fact-constrained guidance")
            st.markdown(output)

elif page == "Career Roadmap":
    if not need_data():
        a=analyze_match(st.session_state.resume, st.session_state.job)
        st.dataframe(pd.DataFrame(make_roadmap(a["missing"])), use_container_width=True, hide_index=True)

elif page == "Interview Preparation":
    if not need_data():
        a=analyze_match(st.session_state.resume, st.session_state.job)
        if st.button("Create interview set"):
            fallback="\n\n".join(f"**{c}:** {q}\n\nAnswer guidance: {g}" for c,q,g in fallback_questions(st.session_state.job["required_skills"], a["missing"]))
            text, live=generate(interview_prompt(st.session_state.resume, st.session_state.job, a["missing"]), fallback)
            st.caption("LLM-generated" if live else "Offline interview set"); st.markdown(text)

elif page == "Mock Interview":
    if not need_data():
        a=analyze_match(st.session_state.resume, st.session_state.job)
        if "mock" not in st.session_state: st.session_state.mock=fallback_questions(st.session_state.job["required_skills"], a["missing"]); st.session_state.mock_index=0; st.session_state.mock_scores=[]
        i=st.session_state.mock_index
        if i < len(st.session_state.mock):
            category, question, guidance=st.session_state.mock[i]
            st.subheader(f"Question {i+1}: {category}"); st.write(question)
            answer=st.text_area("Your answer", key=f"answer_{i}")
            if st.button("Submit answer"):
                if not answer.strip(): st.warning("Please enter an answer.")
                else:
                    score, feedback=evaluate_answer(answer); st.session_state.mock_scores.append(score); st.success(f"Score: {score}/100 — {feedback}"); st.session_state.mock_index += 1
        else:
            average=round(sum(st.session_state.mock_scores)/len(st.session_state.mock_scores))
            st.success(f"Mock interview complete. Overall score: {average}/100")
            st.write("Strong areas: responses with structure and outcomes. Improvement: practise concise STAR answers and prepare concrete projects.")
            if st.button("Restart mock interview"): del st.session_state.mock; st.rerun()

elif page == "RAG Assistant":
    q=st.text_input("Ask about placement preparation")
    if q:
        sources=retrieve(q)
        st.subheader("Retrieved sources")
        for source in sources: st.expander(f"{source['source']} ({source['score']:.2f})").write(source["text"])
        context="\n".join(s["text"] for s in sources)
        out, live=generate(f"Answer only from this career context. Context: {context}\nQuestion: {q}", "Based on the retrieved guidance: " + context)
        st.subheader("Answer"); st.write(out)

elif page == "Prompt Evaluation":
    task=st.text_input("Task", "Suggest a truthful one-line resume summary for a Python student")
    if st.button("Compare prompts"):
        zero,_=generate(task, "Zero-shot baseline: emphasise only verified Python learning and projects.")
        few,_=generate("Example: Facts: SQL dashboard project. Summary: Built a SQL dashboard project.\nNow " + task, "Few-shot structured: mention verified skills, project context, and target role; omit unsupported claims.")
        df=prompt_comparison(zero, few); st.dataframe(df.drop(columns=["Output"]), use_container_width=True); st.subheader("Outputs"); st.write("**Zero-shot:**", zero); st.write("**Few-shot:**", few)
