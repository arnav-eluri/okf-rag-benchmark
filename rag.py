from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import os, glob, shutil, config

def _make_embeddings():
    key = getattr(config, "GOOGLE_API_KEY", None)
    if key and key.startswith("AIza"):
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        print("Using Google text-embedding-004")
        return GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=key,
        )
    from langchain_huggingface import HuggingFaceEmbeddings
    print("Using HuggingFace all-MiniLM-L6-v2 (set GOOGLE_API_KEY=AIza... to use Google embeddings)")
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

_embeddings = None
_vectorstore = None

def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = _make_embeddings()
    return _embeddings

def _read_docx(filepath):
    import docx as _docx
    doc = _docx.Document(filepath)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def _read_pdf(filepath):
    import fitz
    doc = fitz.open(filepath)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text

def build_index(docs_dir):
    global _vectorstore
    docs = []
    for filepath in glob.glob(os.path.join(docs_dir, "**/*.md"), recursive=True):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            docs.append(Document(page_content=content, metadata={"source": filepath}))
    for filepath in glob.glob(os.path.join(docs_dir, "**/*.docx"), recursive=True):
        content = _read_docx(filepath)
        if content:
            docs.append(Document(page_content=content, metadata={"source": filepath}))
    for filepath in glob.glob(os.path.join(docs_dir, "**/*.pdf"), recursive=True):
        content = _read_pdf(filepath)
        if content:
            docs.append(Document(page_content=content, metadata={"source": filepath}))

    if not docs:
        return 0
    chunks = RecursiveCharacterTextSplitter(
                chunk_size=400, chunk_overlap=50
             ).split_documents(docs)
    # wipe stale index so re-runs don't accumulate duplicate chunks
    if os.path.exists(".chroma"):
        shutil.rmtree(".chroma")
    _vectorstore = Chroma.from_documents(
        chunks,
        _get_embeddings(),
        collection_name="documents",
        persist_directory=".chroma"
    )
    return len(chunks)

def query_rag(question, k=5):
    if not _vectorstore:
        return None
    results = _vectorstore.similarity_search(question, k=k)
    return "\n\n".join(r.page_content for r in results)
