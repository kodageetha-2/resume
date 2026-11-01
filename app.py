import html
import json
import logging
import streamlit as st
import pandas as pd
import plotly.express as px
from src.resume_parser import pdf_to_text, parse_resume
from src.job_parser import parse_job_description
from src.similarity import analyze_match
from src.llm import generate
from src.prompts import resume_improvement_prompt, interview_prompt, mock_interview_prompt, career_blueprint_prompt, enforce_blueprint_resume_keywords
from src.roadmap import make_roadmap
from src.interview import fallback_questions, fallback_mcqs, parse_mcqs
from src.rag import retrieve
from src.evaluation import prompt_comparison

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Career Foundry | Local Career Lab", page_icon="✳", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {--ink:#17332f; --paper:#f3f6f0; --line:#d7dfd7; --lime:#d9f36a; --coral:#ff725c; --muted:#64736c;}
.stApp {background-color:var(--paper); color:var(--ink); font-family:'Manrope',sans-serif;}
.stApp:before {content:''; position:fixed; inset:0; pointer-events:none; z-index:0; opacity:.2; background-image:radial-gradient(#9eafa4 .7px,transparent .7px); background-size:18px 18px;}
[data-testid="stHeader"] {background:transparent;}
.block-container {max-width:1320px; padding:1.1rem 2rem 4rem; position:relative;}
[data-testid="stSidebar"] {background:var(--ink); border-right:1px solid #31534c;}
[data-testid="stSidebar"] * {color:#f1f5ed;}
[data-testid="stSidebar"] [data-testid="stRadio"] label {font-size:.9rem;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {gap:.12rem;}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {color:var(--lime); font-weight:800;}
[data-testid="stSidebar"] hr {border-color:#426158;}
.brand {display:flex; align-items:center; gap:11px; padding:8px 0 24px; border-bottom:1px solid #426158; margin-bottom:18px;}
.brand-icon {display:grid; place-items:center; width:36px; height:36px; background:var(--lime); color:var(--ink); font-size:1.25rem; font-weight:800;}
.brand-name {font-size:.98rem; font-weight:800; line-height:1.12;}
.brand-sub {font-family:'DM Mono',monospace; color:#b8c8bd; font-size:.6rem; letter-spacing:.08em; margin-top:3px;}
[data-testid="stMetric"] {background:#fff; border:1px solid var(--line); border-bottom:3px solid var(--lime); border-radius:4px; padding:14px 16px;}
[data-testid="stMetricLabel"] {color:var(--muted); font-family:'DM Mono',monospace; text-transform:uppercase; font-size:.68rem;}
[data-testid="stMetricValue"] {color:var(--ink); font-weight:800;}
.masthead {display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--line); padding:4px 0 12px; margin-bottom:30px;}
.masthead-word {font-weight:800; font-size:.95rem; letter-spacing:.02em;}
.masthead-meta,.eyebrow,.mono {font-family:'DM Mono',monospace; font-size:.68rem; letter-spacing:.04em; text-transform:uppercase;}
.masthead-meta {color:var(--muted);}
.hero-copy {padding:26px 12px 30px 0;}
.hero-copy h1 {font-size:3.65rem; line-height:1.04; letter-spacing:0; margin:13px 0 18px; font-weight:800; color:var(--ink); max-width:700px;}
.hero-copy p {font-size:1.04rem; line-height:1.65; max-width:600px; color:#43544d;}
.eyebrow {color:#55746a; font-weight:500;}
.hero-panel {background:var(--ink); color:#f1f5ed; min-height:280px; padding:24px; margin:22px 0; border-radius:4px; position:relative; overflow:hidden;}
.hero-panel .eyebrow {color:var(--lime);}
.hero-panel h3 {font-size:1.3rem; color:#fff; margin:12px 0 18px;}
.flow-step {display:flex; gap:14px; border-top:1px solid #426158; padding:12px 0; align-items:center;}
.flow-num {font-family:'DM Mono',monospace; color:var(--lime); font-size:.72rem;}
.flow-copy {font-size:.86rem; color:#e1e9e2;}
.flow-copy small {display:block; color:#aebfb4; margin-top:2px;}
.helper {background:#fff; border-left:4px solid var(--coral); padding:15px 18px; margin:10px 0 18px; color:#405149;}
.helper b {color:var(--ink);}
.form-title {font-size:1.45rem; font-weight:800; margin:22px 0 3px; color:var(--ink);}
.section-head {display:flex; justify-content:space-between; align-items:flex-end; border-bottom:1px solid var(--line); padding:0 0 13px; margin:18px 0 22px;}
.section-head h2 {font-size:1.7rem; line-height:1.15; margin:5px 0 0; color:var(--ink);}
.studio-note {background:#e8efdf; border:1px solid #d4dfca; padding:12px 15px; border-radius:4px; color:#43544d; font-size:.9rem;}
.stButton>button {border-radius:4px; min-height:2.8rem; font-weight:800; transition:transform .15s ease, filter .15s ease;}
.stButton>button:hover {transform:translateY(-1px); filter:brightness(.97);}
.stButton>button[kind="primary"] {background:var(--lime); border-color:var(--lime); color:var(--ink);}
.stButton>button[kind="secondary"] {background:#fff; border-color:#bdcac0; color:#000 !important;}
.stButton>button[kind="secondary"] * {color:#000 !important;}
[data-testid="stFileUploader"] {background:#fff; border:1px dashed #9eafa4; border-radius:4px; padding:9px 12px;}
[data-testid="stFileUploader"] button {background:var(--ink) !important; border:1px solid var(--ink) !important; color:#fff !important; border-radius:3px !important; font-weight:700 !important;}
[data-testid="stFileUploader"] button * {color:#fff !important;}
[data-testid="stFileUploader"] small,[data-testid="stFileUploader"] span {color:#43544d !important;}
textarea,[data-testid="stTextInput"] input {background:#fff !important; color:var(--ink) !important; caret-color:var(--ink) !important; border:1px solid #bdcac0 !important; border-radius:4px !important;}
textarea::placeholder {color:#77867e !important; opacity:1;}
[data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] > label {background:#fff !important; color:#000 !important; border:1px solid #bdcac0; border-radius:4px; padding:10px 14px; margin:6px 0; transition:background .15s ease,border-color .15s ease;}
[data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] > label * {color:#000 !important;}
[data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] > label:hover {background:#e8efdf !important; border-color:#55746a;}
[data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) {background:var(--lime) !important; border-color:#819d25;}
[data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] > label:has(input:focus-visible) {outline:3px solid var(--coral); outline-offset:2px;}
[data-testid="stExpander"] {background:#fff !important; color:var(--ink) !important; border:1px solid var(--line); border-radius:4px; position:relative; z-index:1; overflow:visible;}
[data-testid="stExpander"] summary,[data-testid="stExpander"] [data-testid="stExpanderDetails"] {background:#fff !important; color:var(--ink) !important;}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] p,[data-testid="stExpander"] [data-testid="stExpanderDetails"] li,[data-testid="stExpander"] [data-testid="stExpanderDetails"] span {color:var(--ink) !important;}
.match-warning {background:#fff0a8; color:#241f0b; border:1px solid #d7bc44; border-left:4px solid #b28c00; padding:14px 17px; margin:14px 0; border-radius:4px; line-height:1.55;}
.match-warning * {color:#241f0b !important;}
@media(max-width:850px) {.block-container{padding:1rem 1rem 3rem;}.hero-copy{padding:14px 0;}.hero-copy h1{font-size:2.55rem;}.hero-panel{min-height:unset;margin:8px 0 20px;}.masthead{margin-bottom:18px;}}
</style>""", unsafe_allow_html=True)

def ready(): return "resume" in st.session_state and "job" in st.session_state
def load_resume(upload):
    text=pdf_to_text(upload)
    if not text.strip():
        raise ValueError("No readable text was found in this PDF. Try a text-based resume PDF.")
    st.session_state.resume = parse_resume(text)
def load_job(text, upload):
    if upload:
        text = pdf_to_text(upload) if upload.name.lower().endswith(".pdf") else upload.getvalue().decode("utf-8", errors="replace")
    st.session_state.job = parse_job_description(text)
def need_data():
    if not ready():
        st.info("First add a resume and job description on the **Home** page.")
        return True
    return False

def reset_workspace():
    st.session_state.clear()

def intake_form():
    """One friendly entry point for the documents used across the app."""
    if ready():
        match=analyze_match(st.session_state.resume, st.session_state.job)
        st.markdown("<div class='section-head'><div><div class='eyebrow'>WORKSPACE READY</div><h2>Your career signal snapshot</h2></div><div class='mono'>01 / OVERVIEW</div></div>", unsafe_allow_html=True)
        first, second, third=st.columns(3)
        first.metric("Role match", f"{match['score']}%")
        second.metric("Matching skills", len(match["matching"]))
        third.metric("Skills to build", len(match["missing"]))
        st.markdown("<div class='studio-note'>Your resume and job description are loaded. Choose a workspace from the left to explore your match, build a plan, or practise interviews.</div>", unsafe_allow_html=True)
        return
    if "resume" not in st.session_state:
        st.markdown("<div class='form-title'>01 / Add your resume</div><p>Start with the experience you already have. Your plan will be grounded in these details.</p>", unsafe_allow_html=True)
        st.progress(0.5, text="Step 1 of 2 · Resume")
        uploaded=st.file_uploader("Your resume (PDF)", type="pdf", key="home_resume")
        if uploaded:
            try:
                load_resume(uploaded)
                st.rerun()
            except ValueError as e:
                st.error(str(e))
        return
    r=st.session_state.resume
    st.markdown("<div class='form-title'>02 / Choose a target role</div><p>Your resume is in. Add a job description to map your evidence against its requirements.</p>", unsafe_allow_html=True)
    st.progress(1.0, text="Step 2 of 2 · Target role")
    st.markdown(f"<div class='helper'><b>Resume ready: {html.escape(r['name'])}</b><br>Detected skills: {html.escape(', '.join(r['technical_skills']) or 'No specific skills detected yet')}</div>", unsafe_allow_html=True)
    jd_text=st.text_area("Job description", height=160, key="home_jd", placeholder="Paste the job description here. Example: We are looking for a Data Analyst with Python, SQL, Excel, dashboarding, and communication skills...")
    st.caption("Or upload the job description if you have it as a document.")
    jd_file=st.file_uploader("Job description file (PDF or TXT)", type=["pdf", "txt"], key="home_jd_file")
    if st.button("Analyze my career fit", type="primary"):
        try:
            load_job(jd_text, jd_file)
            st.session_state.page="Career Studio ✨"
            st.rerun()
        except ValueError as e:
            st.error(str(e))

nav_pages=["Home", "Career Studio ✨", "Resume Analysis", "Job Matching", "Skill Gap", "Resume Improvement", "Career Roadmap", "Interview Preparation", "Mock Interview", "RAG Assistant", "Prompt Evaluation"]
if "page" not in st.session_state:
    st.session_state.page="Home"
controls={"role":"Data Analyst", "priority":"Skill building", "weeks":4, "depth":"practical", "tone":"supportive"}
with st.sidebar:
    st.markdown("<div class='brand'><div class='brand-icon'>✳</div><div><div class='brand-name'>CAREER<br>FOUNDRY</div><div class='brand-sub'>LOCAL CAREER LAB</div></div></div>", unsafe_allow_html=True)
    if ready():
        st.caption("WORKSPACE")
        current_page=st.session_state.page if st.session_state.page in nav_pages else "Career Studio ✨"
        page=st.radio("Workspace", nav_pages, index=nav_pages.index(current_page), key="workspace_page", label_visibility="collapsed")
        st.session_state.page=page
        if page == "Career Studio ✨":
            st.divider()
            st.caption("PLAN SETTINGS")
            controls={
                "role": st.text_input("Target role", "Data Analyst", key="studio_role"),
                "priority": st.selectbox("Focus", ["Skill building", "ATS resume", "Interview confidence", "Portfolio projects"], key="studio_priority"),
                "weeks": st.select_slider("Sprint length", options=[2, 4, 6, 8, 12], value=4, key="studio_weeks"),
                "depth": st.select_slider("Plan detail", options=["concise", "practical", "detailed"], value="practical", key="studio_depth"),
                "tone": st.selectbox("Coach voice", ["supportive", "direct", "professional"], key="studio_tone"),
            }
        st.divider()
        st.caption("LOCAL INFERENCE · OLLAMA")
        st.caption("Qwen 2.5 3B · runs on this machine")
        st.button("＋  Start a new analysis", use_container_width=True, on_click=reset_workspace)
    else:
        page="Home"
        st.caption("Add your resume and a target job to open your workspace.")
        st.divider()
        st.caption("LOCAL INFERENCE · OLLAMA")
        st.caption("Qwen 2.5 3B · runs on this machine")
st.markdown("<div class='masthead'><div class='masthead-word'>CAREER FOUNDRY</div><div class='masthead-meta'>Evidence in · next move out</div></div>", unsafe_allow_html=True)

if page == "Home":
    copy, preview=st.columns([1.25, .8], gap="large")
    with copy:
        st.markdown("""<div class="hero-copy"><div class="eyebrow">A LOCAL-FIRST CAREER LAB</div><h1>Make your next move<br>with evidence.</h1><p>Turn the experience on your resume into a practical plan for the role you want. Find your strongest signals, see the gaps, and build a next step that stays truthful.</p></div>""", unsafe_allow_html=True)
    with preview:
        st.markdown("""<div class="hero-panel"><div class="eyebrow">THE CAREER FOUNDRY METHOD</div><h3>From raw experience<br>to a clear next move.</h3><div class="flow-step"><div class="flow-num">01</div><div class="flow-copy">Bring your evidence<small>Resume skills, projects, and experience</small></div></div><div class="flow-step"><div class="flow-num">02</div><div class="flow-copy">Read the role signals<small>Compare your profile with a real job</small></div></div><div class="flow-step"><div class="flow-num">03</div><div class="flow-copy">Generate your next steps<small>Locally powered by Qwen 2.5 3B</small></div></div></div>""", unsafe_allow_html=True)
    st.markdown("<div class='section-head'><div><div class='eyebrow'>START HERE</div><h2>Build your career snapshot</h2></div><div class='mono'>TWO QUICK STEPS</div></div>", unsafe_allow_html=True)
    intake_form()

elif page == "Career Studio ✨":
    if not need_data():
        match=analyze_match(st.session_state.resume, st.session_state.job)
        role=html.escape(controls["role"] or "your target role")
        st.markdown(f"""<div class="section-head"><div><div class="eyebrow">CAREER STUDIO / PERSONALIZED SPRINT</div><h2>{role} action plan</h2></div><div class="mono">{controls['weeks']} WEEKS</div></div>""", unsafe_allow_html=True)
        left, mid, right=st.columns(3)
        left.metric("Match", f"{match['score']}%")
        mid.metric("Skills to strengthen", len(match["missing"]))
        right.metric("Evidence-backed skills", len(match["matching"]))
        st.progress(match["score"] / 100, text="Current role alignment")
        st.markdown("<div class='studio-note'>The plan uses evidence from your resume and the job description. Review generated suggestions before using them in an application.</div>", unsafe_allow_html=True)
        skill_cols=st.columns(3)
        for col, label, values in zip(skill_cols, ["ALREADY EVIDENCED", "RELATED SIGNALS", "NEXT SKILLS"], [match["matching"], match["partial"], match["missing"]]):
            col.markdown(f"<div class='eyebrow'>{label}</div>", unsafe_allow_html=True)
            col.write(", ".join(values) or "Nothing detected yet")
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
        if st.button("✳  Generate my career blueprint", type="primary", use_container_width=True):
            if not st.session_state.resume.get("raw_text", "").strip():
                st.error("The resume has no readable text. Upload a text-based PDF before generating a blueprint.")
            else:
                try:
                    with st.spinner("Building a blueprint from your resume and target role…"):
                        prompt=career_blueprint_prompt(st.session_state.resume, st.session_state.job, match, controls)
                        blueprint, live=generate(prompt, fallback, max_tokens=300)
                    if not blueprint.strip():
                        raise ValueError("The model returned an empty blueprint.")
                    if live:
                        blueprint=enforce_blueprint_resume_keywords(blueprint, controls["role"], st.session_state.resume)
                    st.session_state.blueprint=blueprint
                    st.session_state.blueprint_live=live
                except Exception as exc:
                    logger.exception("Career blueprint generation failed")
                    st.error(f"Could not generate the blueprint: {exc}")
        if "blueprint" in st.session_state:
            st.divider()
            st.caption("LOCAL MODEL · QWEN 2.5 3B" if st.session_state.blueprint_live else "OFFLINE · EVIDENCE-BASED PLAN")
            if not st.session_state.blueprint_live:
                st.warning("Ollama did not return a response. Showing the profile-based fallback plan instead.")
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
            with st.expander(title.title()):
                st.write(r.get(title) or f"No {title} section was detected in this resume.")

elif page == "Job Matching":
    if not need_data():
        a=analyze_match(st.session_state.resume, st.session_state.job)
        st.metric("Overall Job Match Score", f"{a['score']}%", help="60% semantic similarity + 40% explicit skill coverage")
        st.progress(a["score"] / 100)
        st.caption(f"Semantic similarity: {a['semantic_similarity']}%")
        cols=st.columns(3)
        for col,title,values in zip(cols,["Matching skills", "Partial match", "Missing skills"],[a["matching"],a["partial"],a["missing"]]):
            col.subheader(title)
            col.write(", ".join(values) or "None")
        if a["missing_requirements"]:
            requirements="<br>".join(html.escape(item) for item in a["missing_requirements"])
            st.markdown(f"<div class='match-warning'><strong>Potential missing requirements</strong><br>{requirements}</div>", unsafe_allow_html=True)

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
        if not st.session_state.resume.get("raw_text", "").strip():
            st.warning("No readable resume text is available. Upload a text-based resume PDF to get tailored recommendations.")
        else:
            fallback="""## Evidence-based improvement notes

### Content and ATS
Lead with verified strengths: %s. Reuse matching job keywords only where your resume supports them.

### Projects and experience
Describe your own action, the tool used, and a result you can verify. Add real metrics if available; do not estimate them.

### Skills to build
Practise these job requirements before claiming them: %s.""" % (", ".join(a["matching"]) or "the skills and projects already in your resume", ", ".join(a["missing"]) or "no explicit technical gaps detected")
            if st.button("Generate recommendations", type="primary"):
                try:
                    with st.spinner("Reviewing your resume against the target job…"):
                        output, live=generate(resume_improvement_prompt(st.session_state.resume, st.session_state.job), fallback, max_tokens=500)
                    if not output.strip():
                        raise ValueError("The model returned empty recommendations.")
                    st.session_state.recommendations=output
                    st.session_state.recommendations_live=live
                except Exception as exc:
                    logger.exception("Resume recommendation generation failed")
                    st.error(f"Could not generate recommendations: {exc}")
            if "recommendations" in st.session_state:
                st.caption("LOCAL MODEL · QWEN 2.5 3B" if st.session_state.recommendations_live else "OFFLINE · PROFILE-BASED GUIDANCE")
                if not st.session_state.recommendations_live:
                    st.warning("Ollama did not return a response. Showing profile-based guidance instead.")
                st.markdown(st.session_state.recommendations)

elif page == "Career Roadmap":
    if not need_data():
        a=analyze_match(st.session_state.resume, st.session_state.job)
        st.dataframe(pd.DataFrame(make_roadmap(a["missing"])), use_container_width=True, hide_index=True)

elif page == "Interview Preparation":
    if not need_data():
        a=analyze_match(st.session_state.resume, st.session_state.job)
        if not st.session_state.resume.get("raw_text", "").strip():
            st.warning("Add readable resume text before creating a tailored interview set.")
        else:
            fallback="\n\n".join(f"**{category}:** {question}\n\nAnswer guidance: {guidance}" for category,question,guidance in fallback_questions(st.session_state.job["required_skills"], a["missing"], st.session_state.resume))
            if st.button("Create interview set", type="primary"):
                try:
                    with st.spinner("Building questions from your profile and target role…"):
                        text, live=generate(interview_prompt(st.session_state.resume, st.session_state.job, a["missing"]), fallback, max_tokens=650)
                    if not text.strip():
                        raise ValueError("The model returned an empty interview set.")
                    st.session_state.interview_set=text
                    st.session_state.interview_set_live=live
                except Exception as exc:
                    logger.exception("Interview set generation failed")
                    st.error(f"Could not create the interview set: {exc}")
            if "interview_set" in st.session_state:
                st.caption("LOCAL MODEL · QWEN 2.5 3B" if st.session_state.interview_set_live else "OFFLINE · RESUME-BASED QUESTIONS")
                if not st.session_state.interview_set_live:
                    st.warning("Ollama did not return a response. Showing resume- and job-based questions instead.")
                st.markdown(st.session_state.interview_set)

elif page == "Mock Interview":
    if not need_data():
        resume=st.session_state.resume
        job=st.session_state.job
        if not resume.get("raw_text", "").strip():
            st.warning("Add readable resume text before starting a resume-based mock interview.")
        elif "mock_questions" not in st.session_state:
            st.markdown("<div class='section-head'><div><div class='eyebrow'>MOCK INTERVIEW / MULTIPLE CHOICE</div><h2>Questions from your profile</h2></div><div class='mono'>UP TO 5 QUESTIONS</div></div>", unsafe_allow_html=True)
            st.caption("The questions use skills, projects, and experience found in your resume, with the target job as secondary context.")
            if st.button("Generate resume-based question set", type="primary"):
                fallback=fallback_mcqs(resume, job)
                if not fallback:
                    st.error("No resume details were available to build questions.")
                else:
                    try:
                        with st.spinner("Generating and validating your MCQs…"):
                            fallback_json=json.dumps({"questions":fallback}, ensure_ascii=False)
                            response, live=generate(mock_interview_prompt(resume, job), fallback_json, max_tokens=750)
                            allowed_topics=list(resume.get("technical_skills", [])) + list(job.get("required_skills", []))
                            allowed_topics.extend(section.title() for section in ("education", "experience", "projects", "internships") if resume.get(section))
                            questions, valid=parse_mcqs(response, fallback, allowed_topics)
                            model_question_count=len(questions) if live and valid else 0
                            existing={question["question"].casefold() for question in questions}
                            if model_question_count:
                                for item in fallback:
                                    if item["question"].casefold() not in existing:
                                        questions.append(item)
                                        existing.add(item["question"].casefold())
                                    if len(questions) >= 5:
                                        break
                        if not questions:
                            raise ValueError("No valid questions could be created from this resume.")
                        st.session_state.mock_questions=questions
                        st.session_state.mock_questions_live=bool(model_question_count)
                        st.session_state.mock_questions_mixed=bool(model_question_count and len(questions)>model_question_count)
                        st.session_state.mock_answers={}
                        st.rerun()
                    except Exception as exc:
                        logger.exception("Mock interview question generation failed")
                        st.error(f"Could not generate the question set: {exc}")
        else:
            questions=st.session_state.mock_questions
            answers=st.session_state.mock_answers
            if st.session_state.mock_questions_live and not st.session_state.mock_questions_mixed:
                st.caption("LOCAL MODEL · VALIDATED JSON")
            elif st.session_state.mock_questions_mixed:
                st.caption("LOCAL MODEL + PROFILE-BASED COMPLETION")
            else:
                st.caption("PROFILE-BASED QUESTION SET · FALLBACK")
            current=next((index for index in range(len(questions)) if index not in answers), None)
            last_answer=st.session_state.pop("mock_last_answer", None)
            if last_answer is not None:
                answered=questions[last_answer]
                if answers[last_answer] == answered["correct_answer"]:
                    st.success("Correct answer")
                else:
                    st.error(f"Not quite. Correct answer: {answered['correct_answer']}. {answered['options'][answered['correct_answer']]}")
                st.info(answered["explanation"])
            if current is None:
                correct=sum(answers[index] == question["correct_answer"] for index, question in enumerate(questions))
                st.success(f"Interview set complete · {correct}/{len(questions)} correct")
                if st.button("Restart mock interview"):
                    for key in ("mock_questions", "mock_questions_live", "mock_questions_mixed", "mock_answers", "mock_last_answer"):
                        st.session_state.pop(key, None)
                    st.rerun()
            else:
                question=questions[current]
                st.progress(current / len(questions), text=f"Question {current + 1} of {len(questions)}")
                st.markdown(f"**{question['topic']}**")
                st.subheader(question["question"])
                labels=list(question["options"])
                selected=st.radio("Choose one answer", labels, format_func=lambda label:f"{label}. {question['options'][label]}", key=f"mock_answer_{current}", label_visibility="collapsed")
                if st.button("Submit answer", type="primary", key=f"submit_mock_{current}"):
                    st.session_state.mock_answers[current]=selected
                    st.session_state.mock_last_answer=current
                    st.rerun()

elif page == "RAG Assistant":
    if "rag_history" not in st.session_state:
        st.session_state.rag_history=[]
    with st.form("rag_question_form", clear_on_submit=True):
        question=st.text_input("Ask about your resume, target job, or placement preparation")
        ask=st.form_submit_button("Ask Career Foundry", type="primary")
    if ask:
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            documents=[
                {"source":"Your resume", "text":st.session_state.resume.get("raw_text", "")},
                {"source":"Target job", "text":st.session_state.job.get("raw_text", "")},
            ]
            sources=retrieve(question, documents=documents)
            if not sources:
                answer="I couldn't find relevant information in the loaded resume, target job, or career notes. Try asking about a detail those documents contain."
                st.session_state.rag_history.append({"question":question, "answer":answer, "sources":[]})
            else:
                context="\n\n".join(f"Source: {source['source']}\n{source['text']}" for source in sources)
                history="\n".join(f"Earlier question: {turn['question']}\nEarlier answer: {turn['answer']}" for turn in st.session_state.rag_history[-3:])
                prompt=f"Answer the question using only the retrieved context below. If the context does not contain the answer, say that you could not find it. Do not add outside facts.\nConversation history:\n{history or 'None'}\nRetrieved context:\n{context}\nQuestion: {question}"
                with st.spinner("Searching your documents and preparing a grounded answer…"):
                    answer, live=generate(prompt, "I couldn't produce an answer from the retrieved context. Please try a more specific question.", max_tokens=250)
                if not live:
                    st.warning("Ollama did not respond. The retrieved sources are still available below.")
                st.session_state.rag_history.append({"question":question, "answer":answer, "sources":sources})
    for turn in st.session_state.rag_history:
        st.markdown("**You asked**")
        st.write(turn["question"])
        st.markdown("**Career Foundry**")
        st.write(turn["answer"])
        for source in turn["sources"]:
            st.expander(f"Source: {source['source']} · relevance {source['score']:.2f}").write(source["text"])

elif page == "Prompt Evaluation":
    task=st.text_area("Prompt to evaluate", "Suggest a truthful summary tailored to my target job.", height=100)
    if st.button("Compare prompts"):
        if not task.strip():
            st.warning("Enter a prompt to compare.")
        else:
            resume_text=st.session_state.resume.get("raw_text", "") if ready() else ""
            job_text=st.session_state.job.get("raw_text", "") if ready() else ""
            evidence=f"Resume:\n{resume_text}\nTarget job:\n{job_text}".strip()
            zero_prompt=f"Perform this task using only the supplied evidence. If evidence is missing, say so.\nTask: {task}\nEvidence:\n{evidence or 'No resume or job is loaded.'}"
            few_prompt=f"Perform the task using only supplied evidence. Structure the answer as: verified evidence, role relevance, concise recommendation. Use placeholders for missing facts and never invent details.\nTask: {task}\nEvidence:\n{evidence or 'No resume or job is loaded.'}"
            try:
                with st.spinner("Running both prompt variants through the local model…"):
                    zero, zero_live=generate(zero_prompt, "", max_tokens=300)
                    few, few_live=generate(few_prompt, "", max_tokens=300)
                if not zero_live or not few_live:
                    logger.error("Prompt evaluation could not obtain both model outputs")
                    st.error("Prompt comparison could not complete because the local model did not return both outputs. Check that Ollama is running, then retry.")
                else:
                    st.session_state.prompt_evaluation={"task":task, "evidence":evidence, "zero":zero, "few":few,
                        "scores":prompt_comparison(zero, few, task, evidence)}
            except Exception as exc:
                logger.exception("Prompt evaluation failed")
                st.error(f"Could not evaluate the prompt: {exc}")
    if "prompt_evaluation" in st.session_state:
        result=st.session_state.prompt_evaluation
        st.caption("Scores are heuristic comparisons of task-term relevance, evidence overlap, and response detail.")
        st.dataframe(result["scores"].drop(columns=["Output"]), use_container_width=True, hide_index=True)
        st.subheader("Generated outputs")
        out_cols=st.columns(2)
        out_cols[0].markdown("**Zero-shot**")
        out_cols[0].write(result["zero"])
        out_cols[1].markdown("**Structured prompt**")
        out_cols[1].write(result["few"])
