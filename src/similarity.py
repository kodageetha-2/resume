from src.embeddings import semantic_similarity
from src.skill_extractor import skill_overlap

def analyze_match(resume: dict, job: dict) -> dict:
    matching, partial, missing = skill_overlap(resume["technical_skills"], job["required_skills"])
    semantic = semantic_similarity(resume["raw_text"], job["raw_text"])
    skill_score = len(matching) / max(1, len(job["required_skills"]))
    score = round(100 * (0.60 * semantic + 0.40 * skill_score))
    return {"score": max(0, min(100, score)), "semantic_similarity": round(semantic * 100, 1),
            "matching": matching, "partial": partial, "missing": missing,
            "missing_requirements": job["required"][:5]}
