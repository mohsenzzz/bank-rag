
import json
import os
import dotenv

from file_manager import download_pdfs
from settings import BASE_DIR
from text_manager import load_documents
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

PDF_DIR = os.getenv("PDF_DIR","pdfs")
CACHE_DIR = os.getenv("CACHE_DIR","cache")
PDF_DIR = BASE_DIR / PDF_DIR
CACHE_DIR = BASE_DIR / "cache"
CACHE_TEXT = CACHE_DIR / "documents.json"
VECTOR_DIR = CACHE_DIR / "faiss_index"

pdf_paths = sorted(PDF_DIR.glob("*.pdf"))
print(pdf_paths)
if not pdf_paths:
    pdf_paths = download_pdfs()


if CACHE_TEXT.exists():
    raw = json.loads(CACHE_TEXT.read_text("utf-8"))
    documents = [Document(page_content=x["page_content"], metadata=x["metadata"]) for x in raw]
else:
    documents =load_documents(pdf_paths)
    CACHE_TEXT.write_text(
        json.dumps(
            [{"page_content": d.page_content, "metadata": d.metadata} for d in documents],
            ensure_ascii=False, indent=2
        ),
        encoding="utf-8"
    )

text_splitter= RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    add_start_index=True
)
chunks = text_splitter.split_documents(documents=documents)

embeddings = HuggingFaceEmbeddings(
    model_name = "google/embeddinggemma-300m",
    model_kwargs = {"device":"cpu"},
)

if VECTOR_DIR.exists():
    vector_store = FAISS.load_local(
        str(VECTOR_DIR),
        embeddings=embeddings,
        allow_dangerous_deserialization=True,
    )
else:
    vector_store = FAISS.from_documents(documents, embeddings)
    vector_store.save_local(str(VECTOR_DIR))

retriever = vector_store.as_retriever(kwargs={"k":3})
