def fallback_questions(job_skills, missing):
    focus = ", ".join((missing or job_skills or ["your core skills"])[:3])
    return [
      ("Technical", f"Explain how you would use {focus} in this role.", "Use a structured example: problem, approach, trade-offs, result."),
      ("Project", "Walk me through a project from requirements to outcome.", "State only real work; quantify impact where you can."),
      ("Behavioral", "Tell me about a time you received difficult feedback.", "Use STAR: situation, task, action, result."),
      ("HR", "Why does this role fit your next career step?", "Connect genuine interests and current evidence to the role.")]

def evaluate_answer(answer: str):
    words = len(answer.split())
    score = min(100, round(words * 1.2 + (20 if any(x in answer.lower() for x in ["result", "impact", "learned"]) else 0)))
    return score, "Add a concrete example, your specific actions, and a measurable result." if score < 65 else "Good structure. Make the impact even more specific."
