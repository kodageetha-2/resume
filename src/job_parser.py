import re
from src.resume_parser import pdf_to_text
from src.skill_extractor import extract_skills

def parse_job_description(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        raise ValueError("Please paste or upload a job description first.")
    skills = extract_skills(text)
    sections=re.split(r"(?i)(?=\b(?:required|must(?:-have)?|preferred|nice\s+to\s+have|responsibilities|qualifications?)\b\s*[:\-]?)", text)
    preferred_text=" ".join(section for section in sections if re.match(r"(?i)^\s*(?:preferred|nice\s+to\s+have)\b", section))
    preferred_skills=extract_skills(preferred_text)["all"]
    required_skills=[skill for skill in skills["all"] if skill not in set(preferred_skills)]
    lines = [x.strip("•- ") for x in text.splitlines() if x.strip()]
    required = [x for x in lines if any(k in x.lower() for k in ("required", "must", "responsibil", "qualification"))]
    preferred = [x for x in lines if any(k in x.lower() for k in ("preferred", "nice to have", "plus"))]
    education = [x for x in lines if any(k in x.lower() for k in ("degree", "b.tech", "bachelor", "master"))]
    return {"raw_text": text, "skills": skills, "required_skills": required_skills,
            "preferred_skills": preferred_skills, "required": required,
            "preferred": preferred, "education_requirements": education, "keywords": skills["all"]}
