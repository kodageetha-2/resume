from src.resume_parser import parse_resume
from src.job_parser import parse_job_description
from src.similarity import analyze_match

def test_matching_runs():
    resume=parse_resume("Asha\nSkills: Python, SQL, Pandas, Git\nProject: data dashboard")
    job=parse_job_description("Required: Python, SQL, Pandas, Power BI")
    result=analyze_match(resume, job)
    assert 0 <= result["score"] <= 100
    assert "python" in result["matching"]
