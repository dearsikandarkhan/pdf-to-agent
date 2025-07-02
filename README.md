# 🧠 PDF to Agent

Turn any PDF (manual, policy, SOP, etc.) into a smart, chat-based AI assistant — in seconds.


## ✨ Features

- 📑 Upload PDFs — get an instant AI agent
- 🧠 Chat with memory and follow-ups
- 🔍 Built-in RAG using Langchain + FAISS
- 📎 Shows citations from original documents
- 🔗 Embeddable on websites

## 🧰 Tech Stack

- 🐍 FastAPI backend
- 🤖 OpenAI / Mistral LLMs
- 📚 Langchain for RAG pipeline
- 🧠 FAISS for vector search
- 🌐 Next.js frontend with TailwindCSS

## 🚀 Getting Started

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app:app --reload

# Frontend
cd frontend
npm install
npm run dev
