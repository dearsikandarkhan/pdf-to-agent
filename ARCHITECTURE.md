# PDF-to-Agent: Scalable Multi-Document Architecture

## Overview

A production-ready, scalable RAG (Retrieval-Augmented Generation) system that transforms PDFs into intelligent AI assistants. Built with FastAPI, supports multiple LLM providers (OpenAI & Ollama), and handles 10-100+ documents per session.

---

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (React)                            │
│  - File Upload UI                                               │
│  - Chat Interface                                               │
│  - Multi-document Selection                                     │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTP/REST
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND (Python)                       │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Document   │  │    Query     │  │   Vector     │         │
│  │   Service    │  │   Service    │  │   Service    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│  ┌──────▼──────────────────▼──────────────────▼───────┐         │
│  │            Service Layer (Business Logic)           │         │
│  │  - PDF Parser  - Chunking  - Embeddings  - Search │         │
│  └──────────────────────┬───────────────────────────┘         │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────────┐         │
│  │         Multi-Provider LLM/Embedding Layer        │         │
│  │  ┌──────────┐      ┌──────────┐                  │         │
│  │  │  OpenAI  │      │  Ollama  │                  │         │
│  │  │  (Cloud) │      │ (Local)  │                  │         │
│  │  └──────────┘      └──────────┘                  │         │
│  └──────────────────────────────────────────────────┘         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PERSISTENT STORAGE                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   FAISS     │  │  Documents  │  │  Metadata   │            │
│  │  (Vectors)  │  │   (PDFs)    │  │   (JSON)    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
backend/
├── app.py                          # FastAPI routes & endpoints
├── config.py                       # Configuration management
├── models.py                       # Pydantic data models
│
├── services/                       # Business logic layer
│   ├── __init__.py
│   ├── llm_service.py             # Multi-provider LLM (OpenAI/Ollama)
│   ├── embedding_service.py       # Multi-provider embeddings
│   ├── document_service.py        # Document lifecycle management
│   ├── vector_service.py          # FAISS vector operations
│   └── query_service.py           # Multi-doc RAG queries
│
├── utils/                          # Helper utilities
│   ├── __init__.py
│   ├── chunking.py                # Advanced chunking strategies
│   └── pdf_parser.py              # PDF parsing with error handling
│
├── storage/                        # Persistent data (gitignored)
│   ├── vector_store/              # FAISS indices (.pkl files)
│   ├── documents/                 # Original PDFs
│   ├── metadata/                  # Document metadata (.json)
│   └── memory/                    # Conversation history
│
├── requirements.txt               # Python dependencies
├── .env                           # Environment variables (create from .env.example)
└── .env.example                   # Configuration template
```

---

## 🔑 Key Features

### 1. Multi-Document Support
- Upload and manage 10-100+ PDFs per session
- Cross-document search and comparison
- Session-based document isolation
- Document deletion and management

### 2. Multi-Provider LLM Support
- **OpenAI**: GPT-4, GPT-3.5 (cloud-based)
- **Ollama**: Llama 3.2, Mistral, etc. (local/private)
- Switchable per-request via API parameter
- Privacy-first: Use Ollama for sensitive documents

### 3. Advanced Chunking Strategies
- **Fixed**: Simple fixed-size chunks with overlap
- **Recursive**: Respects document structure (paragraphs → sentences → words)
- **Semantic**: Topic-aware chunking (paragraph-based)
- Configurable chunk size and overlap

### 4. Scalable Vector Storage
- FAISS for efficient similarity search
- In-memory caching for performance
- Disk persistence for scalability
- Multi-document search with score aggregation

### 5. Comprehensive Error Handling
- PDF validation before processing
- File size limits
- Graceful error responses
- Detailed logging

---

## 🚀 API Endpoints

### Document Management

#### `POST /upload`
Upload and process a PDF document.

**Parameters:**
- `file`: PDF file (multipart/form-data)
- `session_id`: Optional session ID (auto-generated if not provided)
- `embedding_provider`: `openai` or `ollama` (default from config)

**Response:**
```json
{
  "doc_id": "uuid",
  "filename": "document.pdf",
  "file_size": 1024000,
  "num_pages": 50,
  "num_chunks": 120,
  "message": "Document uploaded and processed successfully",
  "upload_timestamp": "2025-10-24T12:00:00"
}
```

#### `GET /documents/{session_id}`
List all documents in a session.

**Response:**
```json
{
  "session_id": "uuid",
  "documents": [
    {
      "doc_id": "uuid",
      "filename": "doc1.pdf",
      "file_size": 1024000,
      "num_pages": 50,
      "chunk_count": 120,
      "upload_timestamp": "2025-10-24T12:00:00",
      "embedding_provider": "ollama"
    }
  ],
  "total_count": 5
}
```

#### `DELETE /documents/{doc_id}`
Delete a document.

**Parameters:**
- `session_id`: Session ID (form data)

---

### Query & Search

#### `POST /query`
Query one or multiple documents.

**Parameters:**
- `question`: User's question
- `session_id`: Session ID
- `doc_ids`: Optional comma-separated doc IDs (queries all if omitted)
- `llm_provider`: `openai` or `ollama` (default: ollama)
- `top_k`: Number of chunks to retrieve (default: 5)

**Response:**
```json
{
  "answer": "Based on the documents...",
  "sources": [
    {
      "doc_id": "uuid",
      "filename": "document.pdf",
      "chunk_id": "uuid_chunk_0",
      "text": "Relevant excerpt...",
      "page_num": 5,
      "score": 0.89
    }
  ],
  "doc_ids_used": ["uuid1", "uuid2"],
  "processing_time_ms": 1234.56,
  "metadata": {
    "num_results": 5,
    "llm_provider": "ollama"
  }
}
```

#### `POST /compare`
Compare how different documents answer the same question.

**Parameters:**
- `question`: Question to ask each document
- `doc_ids`: Comma-separated list of doc IDs (2-10 documents)
- `session_id`: Session ID
- `llm_provider`: `openai` or `ollama`

**Response:**
```json
{
  "question": "What is the main topic?",
  "comparisons": [
    {
      "doc_id": "uuid1",
      "filename": "doc1.pdf",
      "answer": "According to doc1...",
      "sources": [...]
    },
    {
      "doc_id": "uuid2",
      "filename": "doc2.pdf",
      "answer": "According to doc2...",
      "sources": [...]
    }
  ],
  "summary": "Common themes: ... Key differences: ...",
  "processing_time_ms": 2345.67
}
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# LLM Provider
DEFAULT_LLM_PROVIDER="ollama"          # or "openai"
DEFAULT_EMBEDDING_PROVIDER="ollama"    # or "openai"

# OpenAI (if using)
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-4o-mini"
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"

# Ollama (if using)
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="llama3.2:3b"
OLLAMA_EMBEDDING_MODEL="nomic-embed-text"

# Document Processing
CHUNKING_STRATEGY="recursive"          # fixed, recursive, semantic
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_FILE_SIZE_MB=50

# Multi-Document Settings
MAX_DOCUMENTS_PER_SESSION=100
TOP_K_PER_DOCUMENT=3
ENABLE_CROSS_DOC_SEARCH=true
```

See [`.env.example`](backend/.env.example) for all options.

---

## 🔧 Setup & Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 3. Install Ollama (for local LLM)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 4. Run Server

```bash
# Development
uvicorn app:app --reload --port 8000

# Production
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🧪 Testing the API

### Upload a document:
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf" \
  -F "session_id=test-session" \
  -F "embedding_provider=ollama"
```

### Query documents:
```bash
curl -X POST http://localhost:8000/query \
  -F "question=What is this document about?" \
  -F "session_id=test-session" \
  -F "llm_provider=ollama"
```

### List documents:
```bash
curl http://localhost:8000/documents/test-session
```

---

## 📊 Performance Considerations

### Scalability

| Metric | Recommended | Maximum |
|--------|-------------|---------|
| Documents per session | 10-50 | 100 |
| File size | < 10 MB | 50 MB |
| Concurrent users | 10-20 | 50+ (with multiple workers) |
| Chunk size | 1000 chars | 2000 chars |

### Optimization Tips

1. **Use Ollama for high-volume**: No API costs, fully local
2. **Cache frequently accessed docs**: Already implemented via in-memory cache
3. **Batch processing**: Upload multiple docs in parallel (client-side)
4. **Index optimization**: FAISS IndexIVFFlat for 100K+ chunks (future)
5. **Database migration**: Move metadata to PostgreSQL for 1000+ docs (future)

---

## 🔒 Security Considerations

1. **API Keys**: Never commit `.env` to version control
2. **CORS**: Configure `allow_origins` properly in production
3. **File validation**: Validates file type and size before processing
4. **Session isolation**: Documents are isolated per session
5. **Rate limiting**: Consider adding rate limits in production (not implemented)

---

## 🛣️ Migration from Old Architecture

### Key Changes

| Old | New |
|-----|-----|
| Single document only | Multi-document support |
| OpenAI only | OpenAI + Ollama |
| No metadata tracking | Full metadata system |
| File-based memory | Structured JSON storage |
| Fixed chunking | Multiple strategies |
| No error handling | Comprehensive validation |
| Hardcoded config | Environment-based config |

### Breaking Changes

- `/ask` endpoint → `/query` (different parameters)
- `doc_id` required → Optional (queries all docs in session)
- Returns structured JSON with sources
- Session-based instead of doc-based memory

---

## 📈 Future Enhancements

- [ ] PostgreSQL for metadata (scalability)
- [ ] Redis for session management
- [ ] Streaming responses (SSE)
- [ ] Multi-modal support (images, tables)
- [ ] Document comparison UI
- [ ] Rate limiting & authentication
- [ ] Semantic caching for queries
- [ ] Support for more file types (DOCX, TXT, HTML)

---

## 🐛 Troubleshooting

### Ollama connection failed
```bash
# Start Ollama service
ollama serve

# Verify models are pulled
ollama list
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### FAISS errors
```bash
# Install FAISS CPU version
pip install faiss-cpu==1.7.4
```

---

## 📝 License

MIT License - See LICENSE file for details.
