from src.resume_parser import pdf_to_text
from src.skill_extractor import extract_skills

def parse_job_description(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        raise ValueError("Please paste or upload a job description first.")
    skills = extract_skills(text)
    lines = [x.strip("•- ") for x in text.splitlines() if x.strip()]
    required = [x for x in lines if any(k in x.lower() for k in ("required", "must", "responsibil", "qualification"))]
    preferred = [x for x in lines if any(k in x.lower() for k in ("preferred", "nice to have", "plus"))]
    education = [x for x in lines if any(k in x.lower() for k in ("degree", "b.tech", "bachelor", "master"))]
    return {"raw_text": text, "skills": skills, "required_skills": skills["all"], "required": required,
            "preferred": preferred, "education_requirements": education, "keywords": skills["all"]}
