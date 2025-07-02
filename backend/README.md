# 📄 PDF to AI Agent — Backend

Turn any PDF into a smart AI assistant using Langchain, FAISS, and OpenAI.

> Upload a PDF, ask questions about it, and get instant answers from your own AI agent.

---

## 🛠 Features

- Upload PDF → Chunk → Vectorize → Ask questions
- Uses Langchain + FAISS for Retrieval-Augmented Generation (RAG)
- Memory layer (long-term) to maintain chat context
- REST API built with FastAPI
- Ready for deployment with Docker / Render / Railway

---

## 📁 Project Structure

backend/
├── app.py # FastAPI routes for upload & QA
├── document_ingest.py # PDF parsing & chunking
├── qa_chain.py # QA chain setup with Langchain
├── vector_store.py # FAISS-based vector DB
├── memory_store.py # Optional memory system
├── requirements.txt
├── .env # API keys
└── vector_store/ & memory/ (auto-created)

yaml
Copy
Edit

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/yourname/pdf-to-agent-backend.git
cd pdf-to-agent-backend
2. Set up environment
Create a .env file:

env
Copy
Edit
OPENAI_API_KEY=your_openai_key
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
3. Run the app
bash
Copy
Edit
uvicorn app:app --reload --host 0.0.0.0 --port 8000
📦 API Reference
POST /upload
Upload a PDF file.

Form Data:

file: PDF file

Response:

json
Copy
Edit
{ "doc_id": "abc123" }
POST /ask
Ask a question related to a previously uploaded PDF.

Form Data:

doc_id: ID returned from /upload

question: Your query

Response:

json
Copy
Edit
{ "answer": "Here is the answer from the document..." }
🐳 Docker
bash
Copy
Edit
docker build -t pdf-to-agent .
docker run -p 8000:8000 --env-file .env pdf-to-agent
🌐 Deployment Options
Render.com

Railway.app

DigitalOcean

Fly.io or self-hosted Docker

🧠 Tech Stack
FastAPI

Langchain

OpenAI / LLMs

FAISS

PyPDF2

dotenv

🙌 Contributing
Fork this repo

Create your feature branch (git checkout -b feature/awesome)

Commit your changes (git commit -am 'Add awesome')

Push to the branch (git push origin feature/awesome)

Create a new Pull Request

📃 License
MIT

