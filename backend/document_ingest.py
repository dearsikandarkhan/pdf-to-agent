from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from vector_store import store_chunks

def process_pdf(content: bytes, doc_id: str):
    reader = PdfReader.from_bytes(content)
    raw_text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_text(raw_text)

    embeddings = OpenAIEmbeddings()
    embedded_chunks = embeddings.embed_documents(chunks)

    store_chunks(doc_id, chunks, embedded_chunks)
