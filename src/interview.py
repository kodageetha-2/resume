import json
import re
from src.skill_extractor import SKILL_CATALOG

def fallback_questions(job_skills, missing, resume=None):
    resume=resume or {}
    resume_skills=resume.get("technical_skills", [])
    focus=", ".join((resume_skills or job_skills or missing or ["your core skills"])[:3])
    project=(resume.get("projects") or "").strip()
    project_question=f"Walk me through this resume project: {project.splitlines()[0][:100]}" if project else "Walk me through a project from requirements to outcome."
    technical_question=f"Describe a real task where you used {focus}. What approach and result can you explain?" if resume_skills else f"How would you approach building evidence in {focus} for this role?"
    return [
      ("Technical", technical_question, "Explain the problem, your specific actions, trade-offs, and a verifiable result."),
      ("Project", project_question, "State only your own work; quantify impact only when you have real evidence."),
      ("Behavioral", "Describe a real time you received difficult feedback and what you changed.", "Use STAR: situation, task, action, result."),
      ("HR", "Why does this target role fit your next career step?", "Connect genuine interests and resume evidence to the role.")]

def evaluate_answer(answer: str):
    words = len(answer.split())
    score = min(100, round(words * 1.2 + (20 if any(x in answer.lower() for x in ["result", "impact", "learned"]) else 0)))
    return score, "Add a concrete example, your specific actions, and a measurable result." if score < 65 else "Good structure. Make the impact even more specific."

_SKILL_QUESTIONS = {
    "python": ("Which Python structure is best suited to map unique keys to values?", "A dictionary", ["A list", "A tuple", "A set"], "A dictionary stores values under unique keys."),
    "sql": ("Which SQL clause filters rows before aggregation?", "WHERE", ["ORDER BY", "HAVING", "LIMIT"], "WHERE filters source rows before GROUP BY; HAVING filters grouped results."),
    "pandas": ("Which Pandas operation combines DataFrames using a shared key?", "merge", ["melt", "describe", "dropna"], "merge joins DataFrames using one or more key columns."),
    "numpy": ("What lets NumPy apply operations across arrays without a Python loop?", "Vectorization", ["Serialization", "Inheritance", "Indexing only"], "Vectorized operations run element-wise through optimized array operations."),
    "git": ("Which Git command records staged changes in the repository history?", "git commit", ["git status", "git diff", "git fetch"], "git commit creates a repository commit from staged changes."),
    "machine learning": ("What is a common sign that a machine-learning model is overfitting?", "Training performance is strong but validation performance is weak", ["Both training and validation performance improve together", "The dataset has no labels", "The model has fewer parameters"], "A large train/validation gap commonly indicates overfitting."),
    "power bi": ("In Power BI, what is a measure typically used for?", "A calculation evaluated in the current filter context", ["A fixed image on a report page", "A source-control commit", "A PDF text extractor"], "Measures calculate values dynamically under report filters."),
    "excel": ("Which Excel feature is designed to summarize and group tabular data interactively?", "PivotTable", ["WordArt", "Page Break Preview", "Find and Replace"], "PivotTables aggregate and reorganize data for analysis."),
    "java": ("What does a Java constructor primarily do?", "Initialize a new object", ["Delete a package", "Sort every collection", "Compile source files at runtime"], "A constructor initializes a newly created instance."),
    "javascript": ("Which JavaScript construct is commonly used to handle a promise's success value?", ".then()", [".catchOnly()", ".resolveNow()", ".awaited()"], ".then() registers a handler for a fulfilled promise."),
  }

_ANSWER_CYCLE = ("A", "C", "B", "D")
MIN_MOCK_QUESTIONS = 10

def _place_correct_option(question, correct_text, distractors, explanation, index, topic):
    options=[correct_text, *distractors[:3]]
    answer=_ANSWER_CYCLE[index % len(_ANSWER_CYCLE)]
    labels=["A", "B", "C", "D"]
    options_by_label=dict(zip(labels, options))
    current=labels[0]
    options_by_label[current], options_by_label[answer]=options_by_label[answer], options_by_label[current]
    return {"question":question, "topic":topic, "options":options_by_label,
          "correct_answer":answer, "explanation":explanation}

def fallback_mcqs(resume, job=None, count=MIN_MOCK_QUESTIONS):
    skills=list(dict.fromkeys(resume.get("technical_skills", [])))
    required=(job or {}).get("required_skills", [])
    skills.extend(skill for skill in required if skill not in skills)
    profile_text=(resume.get("raw_text") or "").strip()
    profile_lines=[line.strip() for line in profile_text.splitlines()
                   if line.strip() and line.strip().casefold() != str(resume.get("name", "")).strip().casefold()]
    if not profile_text:
      return []
    questions=[]
    resume_sections=[(section, label) for section, label in (("projects", "project"), ("experience", "experience"), ("internships", "internship")) if (resume.get(section) or "").strip()]
    skill_limit=max(1, count - 1) if resume_sections else count
    for skill in skills:
      if len(questions) >= skill_limit:
        break
      bank=_SKILL_QUESTIONS.get(skill.lower())
      if bank:
        question, correct, distractors, explanation=bank
      else:
        question=f"Your resume lists {skill}. Which response best demonstrates hands-on experience with it?"
        correct=f"Describe a specific task completed with {skill}, your approach, and a verifiable result."
        distractors=["Repeat the skill name without an example.", "Describe a result without explaining your contribution.", "Claim a metric that is not supported by the resume."]
        explanation="A specific action and verifiable outcome provide evidence of practical experience."
      questions.append(_place_correct_option(question, correct, distractors, explanation, len(questions), skill))
    for section, label in resume_sections:
      details=(resume.get(section) or "").strip()
      if details and len(questions) < count:
        anchor=details.splitlines()[0][:100]
        question=f"When discussing this resume {label}: {anchor}, what best demonstrates your contribution?"
        correct="Explain your own actions, the tools used, and an outcome you can verify."
        distractors=["Describe only what the team did.", "Add an unverified percentage to make the result sound larger.", "List tasks without connecting them to the project's goal."]
        questions.append(_place_correct_option(question, correct, distractors, "A specific action, tools, and a verifiable outcome make the example credible.", len(questions), label.title()))
    for skill in skills:
      if len(questions) >= count:
        break
      question=f"Which detail would best support your resume's {skill} claim in an interview?"
      correct=f"Explain a specific task where you used {skill}, your own action, and an outcome you can verify."
      distractors=["Repeat the skill name without an example.", "Describe a team result without your contribution.", "Add a metric that is not documented in the resume."]
      explanation=f"A concrete example of using {skill} connects the resume claim to verifiable evidence."
      questions.append(_place_correct_option(question, correct, distractors, explanation, len(questions), skill))
    if not questions:
      anchor=(profile_lines[0] if profile_lines else "the profile details provided")[:100]
      question=f"Which interview response best supports the resume detail: {anchor}?"
      questions.append(_place_correct_option(question, "Give a concrete example that explains your own action and its result.", ["State an unsupported achievement.", "Repeat the detail without context.", "Describe a skill absent from the resume."], "A concrete example provides support for the resume claim without adding new facts.", 0, "Resume evidence"))
    evidence=[]
    evidence.extend((skill, skill) for skill in skills)
    evidence.extend((label.title(), (resume.get(section) or "").strip().splitlines()[0][:100])
                    for section, label in resume_sections)
    evidence.extend(("Resume profile", line[:100]) for line in profile_lines)
    follow_ups=[
      ("Which response best explains your contribution to {detail}?", "Describe your own actions and separate them from the team's work.", ["Claim ownership of the entire team's work.", "Add an achievement not present in your resume.", "Repeat the detail without explaining your role."], "Clear ownership keeps the answer grounded in the supplied resume."),
      ("When discussing {detail}, which evidence should you include?", "A specific example and an outcome you can verify.", ["An estimated metric presented as fact.", "A result without explaining how it was achieved.", "A responsibility not listed in your resume."], "Verifiable evidence makes the resume detail credible."),
      ("What is the strongest way to expand on {detail} in an interview?", "Explain the context, your action, and what you learned.", ["Add unrelated experience to make the answer longer.", "Describe only what others did.", "Invent a result that sounds impressive."], "Context, personal action, and learning give a truthful, complete answer."),
      ("If asked about {detail}, how should you support your answer?", "Use a concrete example from the experience in your resume.", ["Claim expertise beyond the evidence provided.", "Give a hypothetical result as if it happened.", "Avoid describing your own contribution."], "A concrete resume-based example avoids unsupported claims."),
      ("Which follow-up would make your explanation of {detail} clearest?", "Name the steps you personally took and the evidence of the outcome.", ["Use a number you cannot verify.", "Focus only on the team's general responsibilities.", "Add a tool or skill absent from your profile."], "Specific actions and verifiable outcomes clarify the candidate's role."),
      ("What should you emphasize when presenting {detail}?", "The problem or goal, your contribution, and a truthful result.", ["A result with no supporting example.", "An achievement from someone else's work.", "A skill you have not used."], "This structure communicates impact without adding unsupported facts."),
      ("How can you answer a follow-up about {detail} accurately?", "Stay within the supplied experience and explain what you know firsthand.", ["Guess at details you do not remember.", "Present an assumption as a measured result.", "Claim work that is not yours."], "Firsthand, evidence-based details preserve accuracy."),
      ("Which answer best reflects learning from {detail}?", "Describe a lesson supported by the experience and how you would apply it.", ["Claim a lesson unrelated to the experience.", "Invent a challenge that is not in the profile.", "Avoid explaining what you learned."], "A relevant lesson connects the experience to future work without inventing facts."),
      ("What is the most credible way to discuss {detail}?", "Be precise about your role and use only outcomes you can substantiate.", ["Overstate your responsibility.", "Add an unverified percentage.", "Describe an outcome without evidence."], "Precise ownership and substantiated outcomes are credible."),
      ("How should you respond if asked for more detail about {detail}?", "Give a specific, truthful example and clarify any limits in your experience.", ["Claim experience you do not have.", "Use vague claims instead of examples.", "Turn an estimate into a confirmed fact."], "A specific answer that acknowledges limits stays truthful."),
    ]
    for template_index, template in enumerate(follow_ups):
      for topic, anchor in evidence:
        question_template, correct, distractors, explanation=template
        question=question_template.format(detail=anchor)
        if question.casefold() in {item["question"].casefold() for item in questions}:
          continue
        questions.append(_place_correct_option(question, correct, distractors, explanation, len(questions), topic))
        break
      if len(questions) >= count:
        break
    return questions[:count]

def parse_mcqs(response, fallback, allowed_topics=None):
    text=(response or "").strip()
    if text.startswith("```"):
      text=text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
      if text.lower().startswith("json"):
        text=text[4:].strip()
    try:
      payload=json.loads(text)
    except (TypeError, json.JSONDecodeError):
      return fallback, False
    items=payload.get("questions") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
      return fallback, False
    valid=[]
    seen=set()
    allowed={re.sub(r"[^a-z0-9+#]", "", str(topic).lower()) for topic in (allowed_topics or [])}
    known_skills={re.sub(r"[^a-z0-9+#]", "", skill.lower()) for skills in SKILL_CATALOG.values() for skill in skills}
    for item in items:
      if not isinstance(item, dict):
        continue
      question=str(item.get("question", "")).strip()
      topic=str(item.get("topic", "Resume profile")).strip()
      options=item.get("options")
      if isinstance(options, list) and len(options)==4:
        options=dict(zip(("A", "B", "C", "D"), options))
      if not isinstance(options, dict):
        continue
      normalized={key:str(options.get(key, "")).strip() for key in ("A", "B", "C", "D")}
      answer=str(item.get("correct_answer", "")).strip().upper()
      if len(answer)>1 and answer[0] in normalized and answer[1] in ".): ":
        answer=answer[0]
      explanation=str(item.get("explanation", "")).strip()
      question_text=question + " " + normalized.get(answer, "")
      topic_text=re.sub(r"[^a-z0-9+#]", "", topic.lower())
      mentioned_skills={skill for skill in known_skills if skill and re.search(r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])", question_text, re.IGNORECASE)}
      unsupported=mentioned_skills - allowed
      if allowed and (not any(skill in topic_text or topic_text in skill for skill in allowed if skill)
              or unsupported):
        continue
      if (not question or question.casefold() in seen or not explanation or answer not in normalized
          or any(not value for value in normalized.values()) or len(set(normalized.values()))<4):
        continue
      seen.add(question.casefold())
      valid.append({"question":question, "topic":topic,
              "options":normalized, "correct_answer":answer, "explanation":explanation})
    if not valid:
      return fallback, False
    for index, item in enumerate(valid):
      target=_ANSWER_CYCLE[index % len(_ANSWER_CYCLE)]
      answer=item["correct_answer"]
      item["options"][answer], item["options"][target]=item["options"][target], item["options"][answer]
      item["correct_answer"]=target
    return valid[:MIN_MOCK_QUESTIONS], True
