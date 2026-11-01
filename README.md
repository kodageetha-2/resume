# AI-Powered Generative Career Assistant

A modular Streamlit academic project for resume–job matching, skill gaps, RAG career guidance and placement preparation. It uses sentence-transformer embeddings when available, with a TF-IDF fallback, and runs the open-weight Qwen 2.5 3B model locally through Ollama for generated recommendations.

## Install and run

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
ollama pull qwen2.5:3b
streamlit run app.py
```

Install Ollama before running the app, then download the model with `ollama pull qwen2.5:3b`. Ollama must be running locally; the app connects to its OpenAI-compatible endpoint at `http://localhost:11434/v1`. Set `OLLAMA_MODEL` or `OLLAMA_BASE_URL` in `.env` to use a different local model or endpoint. `OLLAMA_KEEP_ALIVE` controls how long Ollama keeps the model loaded after each request (default `30m`, using about 2.2 GB for Qwen 2.5 3B on this machine). Model requests now use a 15-second timeout instead of 120 seconds and fall back to profile-based guidance if the local model is slow.

## Test

```bash
pytest tests/test_basic.py
```

Upload a fictional PDF resume and paste `data/job_descriptions/data_analyst.txt` as a sample job. The dashboard shows a 0–100 blended semantic/skill score, evidence-based skill categories, and recommendations. Matching is heuristic and must not be treated as a hiring decision.

## Data

Place public, non-sensitive `.txt` career resources in `data/knowledge_base/` and job descriptions in `data/job_descriptions/`. The RAG module automatically loads knowledge-base text files. For larger datasets, add document chunking and a persisted FAISS/Chroma index.

## Limitations and next steps

PDF extraction and skill detection are imperfect; semantic scores are not ground truth. LLM output can fail or be inaccurate and requires review. Future work: authenticated storage, richer parsers, curated evaluation labels, persisted vector indexes, and role-specific rubrics.
