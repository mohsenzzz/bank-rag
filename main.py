
import json
from operator import itemgetter
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from file_manager import download_pdfs
from settings import BASE_DIR
from text_manager import load_documents
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

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


prompt = ChatPromptTemplate.from_template( """تو دستیار پرسش‌وپاسخ درباره اسناد ارائه‌شده هستی.
فقط بر اساس متن داخل بخش «متن‌های بازیابی‌شده» پاسخ بده.
اگر پاسخ در متن‌ها وجود ندارد، شفاف بگو: «در اسناد بازیابی‌شده پاسخ کافی پیدا نکردم.»
پاسخ را به زبان فارسی، دقیق و خلاصه بده و در صورت امکان شماره صفحه/منبع را ذکر کن.

متن‌های بازیابی‌شده:
{context}

سؤال کاربر: {question}

پاسخ:""")

llm =  ChatOpenAI(
    model="nvidia/nemotron-3-ultra-550b-a55b:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("API_KEY"),
)

RAG = RunnableParallel({
    "context":itemgetter("question")|retriever,
    "question":itemgetter("question"),
}
    
)

chain = RAG | prompt | llm |  StrOutputParser()

def ask(question):
    result = chain.invoke({"question": question})
    print(result)
questions = [
    "موضوع اصلی این سند چیست؟",
    "چه اشخاص یا نهادهایی مشمول این آیین‌نامه هستند؟",
    "مهلت یا شرایط مهمی که در سند ذکر شده چیست؟",
]
for question in questions:
    print("\n" + "=" * 80)
    print("سؤال:", question)
    print("پاسخ:")
    print(chain.invoke({"question": question}))