from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import os
import glob

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
_vectorstore = None

def build_index(docs_dir):
    global _vectorstore
    docs = []
    for filepath in glob.glob(os.path.join(docs_dir, "**/*.md"), recursive=True):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            docs.append(Document(page_content=content, metadata={"source": filepath}))

    if not docs:
        return 0
    chunks = RecursiveCharacterTextSplitter(
                chunk_size=400, chunk_overlap=50
             ).split_documents(docs)
    _vectorstore = Chroma.from_documents(
        chunks,
        embeddings,
        collection_name="documents",
        persist_directory=".chroma"
    )
    return len(chunks)

def query_rag(question, k=3):
    if not _vectorstore:
        return None
    results = _vectorstore.similarity_search(question, k=k)
    return "\n\n".join(r.page_content for r in results)
