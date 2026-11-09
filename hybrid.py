import os
from okf import query_okf
from rag import query_rag

def _exact_match(question, bundle_dir):
    """True only when a bundle's filename concept appears literally in the question."""
    q = question.lower()
    for fname in os.listdir(bundle_dir):
        if fname.endswith(".md"):
            concept = fname.replace(".md", "").replace("_", " ")
            if concept in q:
                return True
    return False

def query_hybrid(question, bundle_dir):
    # Only trust OKF when the concept name (filename) is explicitly in the question.
    # Keyword-only matches are too weak — fall through to RAG for those.
    if _exact_match(question, bundle_dir):
        content, verified = query_okf(question, bundle_dir)
        if content:
            return content, "OKF", verified
    content = query_rag(question)
    return content, "RAG", None
