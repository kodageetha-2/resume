def make_roadmap(missing_skills):
    skills = missing_skills or ["portfolio refinement", "interview communication"]
    groups = [skills[i:i+2] for i in range(0, len(skills), 2)][:3]
    return [{"month": f"Month {i+1}", "topics": ", ".join(group), "why": "Closes a requirement identified in the target job.",
             "practice": f"Build a small project demonstrating {', '.join(group)}.", "outcome": "Add evidence and measurable outcomes to your portfolio."} for i, group in enumerate(groups)]
