import re

SKILL_CATALOG = {
    "programming": ["python", "java", "c++", "c", "javascript", "typescript", "sql", "r", "html", "css"],
    "frameworks": ["react", "angular", "node.js", "django", "flask", "fastapi", "spring boot", "streamlit", "tensorflow", "pytorch"],
    "data_ai": ["machine learning", "deep learning", "nlp", "generative ai", "llm", "pandas", "numpy", "scikit-learn", "data visualization", "power bi", "tableau"],
    "tools": ["git", "github", "docker", "aws", "azure", "gcp", "linux", "excel", "jupyter", "mongodb", "postgresql", "mysql", "rest api", "faiss"],
}

def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9+#.]", "", value.lower())

def extract_skills(text: str) -> dict:
    lowered = text.lower()
    found = {}
    for category, skills in SKILL_CATALOG.items():
        items = [s for s in skills if re.search(r"(?<!\w)" + re.escape(s) + r"(?!\w)", lowered)]
        found[category] = items
    found["all"] = sorted({s for items in found.values() for s in items})
    return found

def skill_overlap(resume_skills, job_skills):
    resume, job = set(resume_skills), set(job_skills)
    matching = sorted(resume & job)
    partial = sorted(s for s in job - resume if any(s in r or r in s for r in resume))
    missing = sorted(job - resume - set(partial))
    return matching, partial, missing
