import re
from src.skill_extractor import extract_skills

SECTIONS = ["education", "experience", "projects", "internships", "certifications"]

def pdf_to_text(uploaded_file) -> str:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except ImportError as exc:
        raise ValueError("PDF support is not installed. Run: pip install -r requirements.txt") from exc
    except Exception as exc:
        raise ValueError(f"Could not read this PDF: {exc}") from exc

def parse_resume(text: str) -> dict:
    text = (text or "").strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = lines[0] if lines and len(lines[0]) < 70 else "Not detected"
    email = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    sections = {key: "" for key in SECTIONS}
    current = None
    for line in lines:
        candidate = line.lower().strip(":")
        matched = next((s for s in SECTIONS if s in candidate), None)
        if matched:
            current = matched
        elif current:
            sections[current] += line + "\n"
    skills = extract_skills(text)
    return {"name": name, "email": email.group(0) if email else "Not detected", "skills": skills,
            "technical_skills": skills["all"], **sections, "raw_text": text}
