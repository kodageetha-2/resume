def resume_improvement_prompt(resume, job):
    return f"Using only the following resume facts, suggest ATS-safe improvements for this job. Clearly label recommendations. Resume: {resume['raw_text']}\nJob: {job['raw_text']}"

def interview_prompt(resume, job, missing):
    return f"Create concise technical, HR, project and behavioral interview questions with answer guidance for this role. Resume: {resume['raw_text']} Job: {job['raw_text']} Missing skills: {', '.join(missing)}"

def career_blueprint_prompt(resume, job, match, controls):
    return f"""You are a precise career coach. Create a {controls['depth']} personalized career blueprint for a student targeting {controls['role']}.
Tone: {controls['tone']}. Prioritize: {controls['priority']}.
Use ONLY supported facts from the resume. Treat missing skills as learning goals, never existing skills. Use crisp markdown headings:
1. Career positioning (2 sentences)
2. Resume headline and ATS keywords supported by evidence
3. {controls['weeks']}-week action sprint, including a practice project
4. Three interview stories to prepare using STAR
5. One next action for today
Resume: {resume['raw_text']}
Job description: {job['raw_text']}
Matching skills: {', '.join(match['matching']) or 'none'}
Missing skills: {', '.join(match['missing']) or 'none'}"""
