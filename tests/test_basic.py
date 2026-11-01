import json
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.resume_parser import parse_resume
from src.job_parser import parse_job_description
from src.similarity import analyze_match
from src.embeddings import semantic_similarity
from src.evaluation import prompt_comparison
from src.interview import fallback_mcqs, parse_mcqs
from src.rag import retrieve
from src.prompts import enforce_blueprint_resume_keywords
from src import llm

def test_matching_runs():
    resume=parse_resume("Asha\nSkills: Python, SQL, Pandas, Git\nProject: data dashboard")
    job=parse_job_description("Required: Python, SQL, Pandas, Power BI")
    result=analyze_match(resume, job)
    assert 0 <= result["score"] <= 100
    assert "python" in result["matching"]

class CareerAssistantServiceTests(unittest.TestCase):
    def setUp(self):
        self.resume = parse_resume("""Asha Example
Skills: Python, SQL, Pandas
Education
BSc Data Science
Experience
Analyst intern at Acme
Projects
Sales dashboard using Python, SQL, and Pandas""")
        self.job = parse_job_description("Required: Python, SQL, Pandas, Excel")

    def test_matching_handles_resume_and_job(self):
        result = analyze_match(self.resume, self.job)
        self.assertIn("python", result["matching"])
        self.assertGreaterEqual(result["score"], 0)

    def test_preferred_job_skills_are_not_marked_as_required(self):
        job = parse_job_description("Required: Python and SQL. Preferred: Power BI and Tableau.")
        self.assertEqual(set(job["required_skills"]), {"python", "sql"})
        self.assertEqual(set(job["preferred_skills"]), {"power bi", "tableau"})

    def test_generate_uses_configured_local_ollama(self):
        response = types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Local answer"))])
        client = Mock()
        client.chat.completions.create.return_value = response
        openai = Mock(return_value=client)
        with patch.dict(sys.modules, {"openai": types.SimpleNamespace(OpenAI=openai)}), patch.dict(os.environ, {"OLLAMA_MODEL": "qwen2.5:3b"}):
            answer, live = llm.generate("Use the profile", "offline fallback")
        self.assertEqual((answer, live), ("Local answer", True))
        self.assertEqual(openai.call_args.kwargs["base_url"], "http://localhost:11434/v1")
        self.assertEqual(client.chat.completions.create.call_args.kwargs["model"], "qwen2.5:3b")
        self.assertEqual(client.chat.completions.create.call_args.kwargs["max_tokens"], 600)
        self.assertEqual(client.chat.completions.create.call_args.kwargs["extra_body"]["keep_alive"], "30m")

    def test_generate_returns_fallback_on_api_failure(self):
        openai = Mock(side_effect=ConnectionError("offline"))
        with patch.dict(sys.modules, {"openai": types.SimpleNamespace(OpenAI=openai)}):
            answer, live = llm.generate("Use the profile", "offline fallback")
        self.assertEqual(answer, "offline fallback")
        self.assertFalse(live)

    def test_rag_retrieves_resume_and_knowledge_sources(self):
        results = retrieve("Python SQL sales dashboard", documents=[{"source": "resume.txt", "text": self.resume["raw_text"]}], min_score=0.01)
        self.assertIn("resume.txt", {result["source"] for result in results})
        self.assertEqual(retrieve("", documents=[]), [])

    def test_fallback_mcqs_use_resume_skills_and_have_four_options(self):
        questions = fallback_mcqs(self.resume, self.job)
        self.assertEqual(len(questions), 5)
        self.assertIn("python", {question["topic"] for question in questions})
        for question in questions:
            self.assertEqual(set(question["options"]), {"A", "B", "C", "D"})
            self.assertIn(question["correct_answer"], question["options"])
            self.assertTrue(question["explanation"])

    def test_mcq_parser_rejects_malformed_and_varies_correct_answers(self):
        fallback = fallback_mcqs(self.resume, self.job)
        malformed, valid = parse_mcqs("not json", fallback)
        self.assertFalse(valid)
        self.assertEqual(malformed, fallback)
        payload = {"questions": [{"question": f"Question {index}?", "topic": "SQL",
            "options": {"A": "Correct", "B": "Option B", "C": "Option C", "D": "Option D"},
            "correct_answer": "A", "explanation": "A verified explanation."} for index in range(4)]}
        questions, valid = parse_mcqs(json.dumps(payload), fallback)
        self.assertTrue(valid)
        self.assertEqual(len({question["correct_answer"] for question in questions}), 4)
        off_profile = {"questions": [{"question": "How does React render components?", "topic": "React",
            "options": {"A": "Correct", "B": "Option B", "C": "Option C", "D": "Option D"},
            "correct_answer": "A", "explanation": "An explanation."}]}
        rejected, valid = parse_mcqs(json.dumps(off_profile), fallback, ["python", "sql", "project"])
        self.assertFalse(valid)
        self.assertEqual(rejected, fallback)

    def test_empty_tfidf_similarity_does_not_raise(self):
        with patch("src.embeddings._model", return_value=None):
            self.assertEqual(semantic_similarity("!!!", "???"), 0.0)

    def test_prompt_scores_depend_on_actual_output(self):
        table = prompt_comparison("Python SQL dashboard project", "Weather forecast tomorrow", "Python SQL dashboard", self.resume["raw_text"])
        self.assertEqual(len(table), 2)
        self.assertNotEqual(table.iloc[0]["Overall score"], table.iloc[1]["Overall score"])

    def test_blueprint_headline_uses_only_resume_skills(self):
        output = "1. Career positioning: Asha is a candidate.\n2. Resume headline and ATS keywords: Python, Excel Proficiency\n- Excel\n3. 4-week action sprint:\n- Learn Excel."
        clean = enforce_blueprint_resume_keywords(output, "Data Analyst", self.resume)
        section = clean.split("3. 4-week action sprint:", 1)[0]
        self.assertIn("python", section.lower())
        self.assertNotIn("excel", section.lower())
        self.assertIn("Learn Excel", clean)

    def test_generation_pages_persist_and_render_model_output(self):
        from streamlit.testing.v1 import AppTest

        cases = [
            ("Career Studio ✨", "✳  Generate my career blueprint", "blueprint"),
            ("Resume Improvement", "Generate recommendations", "recommendations"),
            ("Interview Preparation", "Create interview set", "interview_set"),
            ("Prompt Evaluation", "Compare prompts", "prompt_evaluation"),
        ]
        with patch("src.llm.generate", return_value=("Generated from the supplied candidate profile.", True)):
            for page, button_label, result_key in cases:
                app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
                app.session_state["resume"] = self.resume
                app.session_state["job"] = self.job
                app.session_state["page"] = page
                app.run(timeout=60)
                next(button for button in app.button if button.label == button_label).click().run(timeout=60)
                self.assertIn(result_key, app.session_state, page)
                self.assertTrue(any("Generated from the supplied candidate profile." in element.value for element in app.markdown), page)
                self.assertFalse(app.exception, page)

    def test_resume_sections_expand_and_keep_content_visible(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
        app.session_state["resume"] = self.resume
        app.session_state["job"] = self.job
        app.session_state["page"] = "Resume Analysis"
        app.run(timeout=60)
        labels = {item.label for item in app.expander}
        self.assertTrue({"Education", "Experience", "Projects"}.issubset(labels))
        section_content = {item.label: " ".join(str(child.value) for child in item.children.values()) for item in app.expander}
        self.assertIn("BSc Data Science", section_content["Education"])
        self.assertIn("Analyst intern at Acme", section_content["Experience"])
        self.assertIn("Sales dashboard", section_content["Projects"])
        self.assertFalse(app.exception)

    def test_job_matching_warning_uses_scoped_dark_text_style(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
        app.session_state["resume"] = self.resume
        app.session_state["job"] = self.job
        app.session_state["page"] = "Job Matching"
        app.run(timeout=60)
        self.assertTrue(any("match-warning" in str(item.value) and "Potential missing requirements" in str(item.value) for item in app.markdown))
        self.assertFalse(app.exception)

    def test_rag_form_passes_resume_context_and_persists_answer(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
        app.session_state["resume"] = self.resume
        app.session_state["job"] = self.job
        app.session_state["page"] = "RAG Assistant"
        with patch("src.llm.generate", return_value=("Your resume lists Python and SQL.", True)) as generate:
            app.run(timeout=60)
            app.text_input[0].set_value("Which skills are on my resume?").run(timeout=60)
            next(button for button in app.button if button.label == "Ask Career Foundry").click().run(timeout=60)
        self.assertIn("Source: Your resume", generate.call_args.args[0])
        self.assertIn("Python", generate.call_args.args[0])
        self.assertEqual(app.session_state["rag_history"][-1]["answer"], "Your resume lists Python and SQL.")
        self.assertFalse(app.exception)

    def test_rag_empty_retrieval_does_not_call_model(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
        app.session_state["resume"] = self.resume
        app.session_state["job"] = self.job
        app.session_state["page"] = "RAG Assistant"
        with patch("src.rag.retrieve", return_value=[]), patch("src.llm.generate") as generate:
            app.run(timeout=60)
            app.text_input[0].set_value("Find a nonexistent detail").run(timeout=60)
            next(button for button in app.button if button.label == "Ask Career Foundry").click().run(timeout=60)
        self.assertFalse(generate.called)
        self.assertIn("couldn't find relevant information", app.session_state["rag_history"][-1]["answer"])
        self.assertFalse(app.exception)

    def test_mock_interview_generates_submits_and_grades_mcq(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
        app.session_state["resume"] = self.resume
        app.session_state["job"] = self.job
        app.session_state["page"] = "Mock Interview"
        with patch("src.llm.generate", side_effect=lambda prompt, fallback, **kwargs: (fallback, False)):
            app.run(timeout=60)
            next(button for button in app.button if button.label == "Generate resume-based question set").click().run(timeout=60)
            question = app.session_state["mock_questions"][0]
            next(widget for widget in app.radio if widget.label == "Choose one answer").set_value(question["correct_answer"]).run(timeout=60)
            next(button for button in app.button if button.label == "Submit answer").click().run(timeout=60)
        self.assertEqual(app.session_state["mock_answers"][0], question["correct_answer"])
        self.assertTrue(any("Correct answer" in item.value for item in app.success))
        self.assertTrue(any(item.value == question["explanation"] for item in app.info))
        self.assertFalse(app.exception)

    def test_mock_interview_completes_short_model_set_from_profile(self):
        from streamlit.testing.v1 import AppTest

        model_response = json.dumps({"questions": [{
            "question": "Which Python structure maps unique keys to values?", "topic": "Python",
            "options": {"A": "List", "B": "Dictionary", "C": "Tuple", "D": "Set"},
            "correct_answer": "B", "explanation": "A dictionary stores values under unique keys."}]})
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
        app.session_state["resume"] = self.resume
        app.session_state["job"] = self.job
        app.session_state["page"] = "Mock Interview"
        with patch("src.llm.generate", return_value=(model_response, True)):
            app.run(timeout=60)
            next(button for button in app.button if button.label == "Generate resume-based question set").click().run(timeout=60)
        questions = app.session_state["mock_questions"]
        self.assertEqual(len(questions), 5)
        self.assertTrue(app.session_state["mock_questions_mixed"])
        self.assertFalse(app.exception)
