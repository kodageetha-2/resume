# Project report notes

## Problem and motivation
Students often struggle to connect an existing resume to specific placement requirements. This project provides transparent matching and actionable, fact-constrained preparation guidance.

## Architecture and methodology
PDF/text is parsed into raw text and heuristic sections. A controlled skill catalog extracts explicit mentions. Resume/job semantic similarity uses `all-MiniLM-L6-v2` when installed, otherwise TF-IDF cosine similarity. The score blends 60% semantic relevance and 40% explicit skill coverage. RAG ranks local career documents by similarity. An optional LLM receives prompts that forbid invention; deterministic fallbacks maintain availability.

## Dataset and evaluation
Sample public-style job and career notes are in `data/`. Evaluate with labelled resumes/jobs: precision/recall/F1 for skills, correlation of match score with human ratings, RAG relevance, and human rubrics for relevance/completeness/hallucination. The Prompt Evaluation page records zero/few-shot qualitative comparison.

## Limitations
Skill catalog coverage, PDF parsing, embedding bias, and LLM reliability limit results. Scores must not determine hiring eligibility. Team members can document individual work across parser, UI, RAG/evaluation, and testing.
