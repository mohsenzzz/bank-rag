import re

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from settings import BASE_DIR


CACHE_DIR = BASE_DIR / "cache"
CACHE_TEXT = CACHE_DIR / "documents.json"

def clean_text(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"(?im)^\s*page\s+\d+\s*$", "", text)
    return text.strip()

def load_documents(pdf_paths):
    docs=[]
    for pdf_path in pdf_paths:
        print(f"pdf path: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        for doc in loader.load():
            doc.page_content = clean_text(doc.page_content)
            if doc.page_content:
                doc.metadata["source_file"] = pdf_path.name
                docs.append(doc)
    return docs