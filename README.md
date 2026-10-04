# AI-Powered Generative Career Assistant

A modular Streamlit academic project for resume–job matching, skill gaps, RAG career guidance and placement preparation. It uses sentence-transformer embeddings when available, with a TF-IDF fallback, and optional OpenAI-compatible LLM recommendations.

## Install and run

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

Add `OPENAI_API_KEY` and optionally `OPENAI_MODEL` to `.env`; never commit `.env`. The application remains usable without a key through deterministic offline guidance.

## Test

```bash
pytest tests/test_basic.py
```

Upload a fictional PDF resume and paste `data/job_descriptions/data_analyst.txt` as a sample job. The dashboard shows a 0–100 blended semantic/skill score, evidence-based skill categories, and recommendations. Matching is heuristic and must not be treated as a hiring decision.

## Data

Place public, non-sensitive `.txt` career resources in `data/knowledge_base/` and job descriptions in `data/job_descriptions/`. The RAG module automatically loads knowledge-base text files. For larger datasets, add document chunking and a persisted FAISS/Chroma index.

## Limitations and next steps

PDF extraction and skill detection are imperfect; semantic scores are not ground truth. LLM output can fail or be inaccurate and requires review. Future work: authenticated storage, richer parsers, curated evaluation labels, persisted vector indexes, and role-specific rubrics.
