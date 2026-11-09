from okf import query_okf
from rag import query_rag

def query_hybrid(question, bundle_dir):
    okf_content, verified = query_okf(question, bundle_dir)
    rag_content = query_rag(question)
    if okf_content and rag_content:
        combined = f"[Additional context]\n{rag_content}\n\n[Curated source]\n{okf_content}"
        return combined, "OKF+RAG", verified
    if okf_content:
        return okf_content, "OKF", verified
    return rag_content, "RAG" if rag_content else "None", None
