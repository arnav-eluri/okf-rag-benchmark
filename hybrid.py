from okf import query_okf
from rag import query_rag

def query_hybrid(question, bundle_dir):
    content, verified = query_okf(question, bundle_dir)
    if content:
        return content, "OKF", verified
    content = query_rag(question)
    return content, "RAG", None