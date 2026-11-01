import re
import pandas as pd

_STOP_WORDS={"the", "and", "for", "with", "from", "that", "this", "you", "your", "are", "was", "were", "what", "how", "why", "use", "using", "only", "into", "about", "have", "has", "had", "can", "could", "should", "would", "will", "not", "but", "our", "their", "they", "them", "then", "than", "when", "where", "who", "which", "while", "its", "it", "a", "an", "of", "to", "in", "on", "is", "be", "as", "at", "by", "or"}

def _terms(text):
    return {term.lower() for term in re.findall(r"[A-Za-z][A-Za-z0-9+#.-]*", text or "") if len(term)>1 and term.lower() not in _STOP_WORDS}

def _evaluate_output(output, task, evidence):
    output_terms=_terms(output)
    task_terms=_terms(task)
    evidence_terms=_terms(evidence)
    relevance=round(100 * len(output_terms & task_terms) / len(task_terms)) if task_terms else 0
    evidence_alignment=round(100 * len(output_terms & evidence_terms) / len(output_terms)) if evidence_terms and output_terms else None
    detail=min(100, round(100 * len((output or "").split()) / 70))
    dimensions=[(relevance, .55), (detail, .2)]
    if evidence_alignment is not None:
        dimensions.append((evidence_alignment, .25))
    score=round(sum(value*weight for value, weight in dimensions) / sum(weight for _, weight in dimensions))
    return {"Overall score":score, "Task relevance":relevance, "Evidence alignment":evidence_alignment, "Response detail":detail}

def prompt_comparison(zero, few, task="", evidence=""):
    rows=[]
    for prompt_type, output in (("Zero-shot", zero), ("Few-shot", few)):
        rows.append({"Prompt type":prompt_type, **_evaluate_output(output, task, evidence), "Output":output})
    return pd.DataFrame(rows)
