import os, yaml, datetime

def _cosine_top(question, texts, embeddings):
    q_emb = embeddings.embed_query(question)
    c_embs = embeddings.embed_documents(texts)
    scores = [sum(a * b for a, b in zip(q_emb, ce)) for ce in c_embs]
    return texts[scores.index(max(scores))]

def query_okf(question, bundle_dir):
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from rag import _get_embeddings

    question_lower = question.lower()
    all_chunks, any_verified = [], False

    for fname in sorted(os.listdir(bundle_dir)):  # sorted for determinism
        if not fname.endswith(".md"):
            continue
        path = os.path.join(bundle_dir, fname)
        with open(path, encoding='utf-8') as f:
            content = f.read()

        parts = content.split("---")
        meta = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}
        body = "---".join(parts[2:]).strip() if len(parts) >= 3 else content

        stale = meta.get("stale_after")
        if stale and datetime.date.today() > stale:
            continue

        concept_name = fname.replace(".md", "").replace("_", " ")
        keywords = meta.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [keywords]

        if concept_name in question_lower or any(str(kw).lower() in question_lower for kw in keywords):
            chunks = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30).split_text(body)
            all_chunks.extend(chunks)
            if meta.get("verified", False):
                any_verified = True

    if not all_chunks:
        return None, None

    if len(all_chunks) == 1:
        return all_chunks[0], any_verified

    return _cosine_top(question, all_chunks, _get_embeddings()), any_verified
