
import json
import os
import dotenv

from file_manager import download_pdfs
from settings import BASE_DIR
from text_manager import load_documents
from langchain_core.documents import Document


PDF_DIR = os.getenv("PDF_DIR","pdfs")
CACHE_DIR = os.getenv("CACHE_DIR","cache")
PDF_DIR = BASE_DIR / PDF_DIR
CACHE_DIR = BASE_DIR / "cache"
CACHE_TEXT = CACHE_DIR / "documents.json"

pdf_paths = sorted(PDF_DIR.glob("*.pdf"))

if not pdf_paths:
    pdf_paths = download_pdfs()



if CACHE_TEXT.exists():
    raw = json.load(CACHE_TEXT.read_text("utf-8"))
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