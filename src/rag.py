from pathlib import Path
from src.embeddings import semantic_similarity

def load_knowledge(base="data/knowledge_base"):
    docs=[]
    for p in Path(base).glob("*.txt"):
        docs.append({"source":p.name,"text":p.read_text(encoding="utf-8")})
    return docs

def retrieve(query, limit=3):
    ranked=sorted(({**d,"score":semantic_similarity(query,d["text"])} for d in load_knowledge()), key=lambda d:d["score"], reverse=True)
    return ranked[:limit]
