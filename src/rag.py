from pathlib import Path
from src.embeddings import semantic_similarity

def load_knowledge(base="data/knowledge_base"):
    docs=[]
    folder=Path(base)
    if not folder.exists():
        return docs
    for path in sorted(folder.glob("*.txt")):
        text=path.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            docs.append({"source":path.name,"text":text})
    return docs

def chunk_documents(documents, chunk_size=1000, overlap=120):
    chunks=[]
    for document in documents:
        text=" ".join(str(document.get("text", "")).split())
        source=document.get("source", "document")
        start=0
        while start < len(text):
            end=min(start + chunk_size, len(text))
            if end < len(text):
                boundary=text.rfind(" ", start + chunk_size // 2, end)
                if boundary > start:
                    end=boundary
            chunk=text[start:end].strip()
            if chunk:
                chunks.append({"source":source, "text":chunk, "chunk":len(chunks)})
            if end >= len(text):
                break
            start=max(start + 1, end - overlap)
    return chunks

def retrieve(query, limit=3, documents=None, base="data/knowledge_base", min_score=0.05):
    query=(query or "").strip()
    if not query or limit <= 0:
        return []
    docs=load_knowledge(base)
    if documents:
        docs.extend(documents)
    ranked=[]
    for chunk in chunk_documents(docs):
        score=semantic_similarity(query, chunk["text"])
        if score >= min_score:
            ranked.append({**chunk, "score":score})
    return sorted(ranked, key=lambda item:item["score"], reverse=True)[:limit]
