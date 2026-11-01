import re

def resume_improvement_prompt(resume, job):
    return f"""Act as a careful resume coach. Use only facts explicitly supported by the candidate's resume; never invent skills, employers, dates, metrics, or outcomes. Tailor advice to the target job and separate verified edits from skills the candidate should learn.
Return concise Markdown sections for: summary/content edits, ATS keywords already supported by evidence, project and experience bullet improvements, job-alignment gaps, and truthful next steps. When suggesting a rewritten bullet, use placeholders for missing metrics rather than making them up.
Resume: {resume.get('raw_text', '')}
Detected resume skills: {', '.join(resume.get('technical_skills', []))}
Target job: {job.get('raw_text', '')}
Job skills: {', '.join(job.get('required_skills', []))}"""

def interview_prompt(resume, job, missing):
    return f"""Create a concise interview set tailored to this candidate's actual resume and target job. Include technical questions only for skills evidenced by the resume or explicitly required by the job, plus questions about the candidate's actual projects and experience. Include a short answer approach for each question; do not invent candidate achievements.
Resume: {resume.get('raw_text', '')}
Resume skills: {', '.join(resume.get('technical_skills', []))}
Target job: {job.get('raw_text', '')}
Missing job skills (learning topics, not existing skills): {', '.join(missing)}"""

def mock_interview_prompt(resume, job):
    return f"""Create five unique resume-based interview multiple-choice questions as valid JSON only, with no Markdown fences. Use this exact shape: {{"questions":[{{"question":"...","topic":"...","options":{{"A":"...","B":"...","C":"...","D":"..."}},"correct_answer":"A","explanation":"..."}}]}}.
Each question must be based on a skill, project, education, or experience explicitly present in the resume. Use job skills only when they are explicitly required by the target job. Give exactly four distinct options and exactly one correct answer letter (A-D), with a brief factual explanation. Vary correct-answer letters. Avoid duplicate questions and unsupported candidate claims.
Resume: {resume.get('raw_text', '')}
Resume skills: {', '.join(resume.get('technical_skills', []))}
Projects: {resume.get('projects', '')}
Experience: {resume.get('experience', '')}\nInternships: {resume.get('internships', '')}
Required target-job skills: {', '.join(job.get('required_skills', [])) or 'none detected'}
Allowed technical topics: {', '.join(dict.fromkeys(resume.get('technical_skills', []) + job.get('required_skills', []))) or 'resume projects and experience only'}
Do not ask about preferred skills unless they are also listed in the resume. Target job: {job.get('raw_text', '')}"""

def career_blueprint_prompt(resume, job, match, controls):
    return f"""You are a concise career coach. Create a practical {controls['depth']} blueprint for a student targeting {controls['role']}. Tone: {controls['tone']}; priority: {controls['priority']}.
Use ONLY supported resume facts. Never present a missing skill as an existing skill or invent results, metrics, or experience. Keep the entire response under 200 words and use exactly these five Markdown headings:
1. Career positioning: one sentence.
2. Resume headline and ATS keywords: one headline plus four supported keywords.
3. {controls['weeks']}-week action sprint: four short milestones spanning the sprint; include one practice project.
4. Interview stories: three brief STAR story prompts grounded in the resume.
5. Today: one concrete action that takes under an hour.
Prefer short bullets, no introduction or conclusion.
Resume: {resume['raw_text']}
Job description: {job['raw_text']}
Resume-verified skills (may appear as current strengths): {', '.join(resume.get('technical_skills', [])) or 'none detected'}
Verified job matches: {', '.join(match['matching']) or 'none'}
Job skills missing from the resume (learning goals only; never list as current skills or past experience): {', '.join(match['missing']) or 'none'}
Do not use a job requirement as evidence that the student already has that skill. Interview story prompts may refer only to resume-listed projects, education, experience, or verified skills."""

def enforce_blueprint_resume_keywords(output, role, resume):
    lines=output.splitlines()
    start=next((index for index,line in enumerate(lines) if re.match(r"\s*2[.)]\s*Resume headline and ATS keywords\b", line, re.IGNORECASE)), None)
    if start is None:
        return output
    end=next((index for index in range(start+1, len(lines)) if re.match(r"\s*3[.)]\s*", lines[index])), len(lines))
    supported=resume.get("technical_skills", [])
    headline=f"{role} candidate with resume evidence in {', '.join(supported)}." if supported else f"{role} candidate with evidence from the listed projects and education."
    keywords=", ".join(supported) if supported else "Use only keywords explicitly supported by the resume."
    replacement=["2. Resume headline and ATS keywords:", f"- Headline: {headline}", f"- Supported keywords: {keywords}"]
    lines[start:end]=replacement
    return "\n".join(lines)
