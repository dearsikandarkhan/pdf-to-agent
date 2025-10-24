# Quick Start Guide - PDF-to-Agent

Get up and running in 5 minutes!

---

## Option 1: Using Ollama (Local, Free, Private)

### Step 1: Install Ollama
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from https://ollama.com
```

### Step 2: Pull Models
```bash
ollama pull llama3.2:3b           # LLM (1.7GB)
ollama pull nomic-embed-text      # Embeddings (274MB)
```

### Step 3: Setup Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env - set DEFAULT_LLM_PROVIDER="ollama"
nano .env
```

### Step 4: Run Server
```bash
uvicorn app:app --reload
```

### Step 5: Test It!
```bash
# Upload a PDF
curl -X POST http://localhost:8000/upload \
  -F "file=@your-document.pdf" \
  -F "session_id=my-session"

# Ask a question
curl -X POST http://localhost:8000/query \
  -F "question=What is this document about?" \
  -F "session_id=my-session" \
  -F "llm_provider=ollama"
```

**Advantages:**
- ✅ 100% Free
- ✅ Runs offline
- ✅ Privacy (data never leaves your machine)
- ✅ No API keys needed

---

## Option 2: Using OpenAI (Cloud, Paid)

### Step 1: Get OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-...`)

### Step 2: Setup Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env - add your OpenAI API key
nano .env
```

**In `.env`, set:**
```bash
DEFAULT_LLM_PROVIDER="openai"
DEFAULT_EMBEDDING_PROVIDER="openai"
OPENAI_API_KEY="sk-your-actual-key-here"
```

### Step 3: Run Server
```bash
uvicorn app:app --reload
```

### Step 4: Test It!
```bash
# Upload a PDF
curl -X POST http://localhost:8000/upload \
  -F "file=@your-document.pdf" \
  -F "session_id=my-session" \
  -F "embedding_provider=openai"

# Ask a question
curl -X POST http://localhost:8000/query \
  -F "question=What is this document about?" \
  -F "session_id=my-session" \
  -F "llm_provider=openai"
```

**Advantages:**
- ✅ Better quality (GPT-4)
- ✅ Faster responses
- ✅ No local resources needed

**Costs:** ~$0.01-0.10 per document (depending on size)

---

## 🌐 Use the Web Interface

### Start Frontend (React)
```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm start
```

Navigate to: http://localhost:3000

---

## 🧪 Test Multi-Document Features

### Upload Multiple Documents
```bash
# Upload first document
curl -X POST http://localhost:8000/upload \
  -F "file=@doc1.pdf" \
  -F "session_id=multi-doc-session"

# Upload second document
curl -X POST http://localhost:8000/upload \
  -F "file=@doc2.pdf" \
  -F "session_id=multi-doc-session"

# Upload third document
curl -X POST http://localhost:8000/upload \
  -F "file=@doc3.pdf" \
  -F "session_id=multi-doc-session"
```

### Query Across All Documents
```bash
curl -X POST http://localhost:8000/query \
  -F "question=What are the common themes across all documents?" \
  -F "session_id=multi-doc-session"
```

### Compare Documents
```bash
# First, get doc IDs
curl http://localhost:8000/documents/multi-doc-session

# Then compare (replace with actual doc IDs)
curl -X POST http://localhost:8000/compare \
  -F "question=What are the key differences?" \
  -F "doc_ids=doc-id-1,doc-id-2" \
  -F "session_id=multi-doc-session"
```

---

## 🎛️ Common Configuration

### `.env` Settings

#### For Privacy (Ollama)
```bash
DEFAULT_LLM_PROVIDER="ollama"
DEFAULT_EMBEDDING_PROVIDER="ollama"
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="llama3.2:3b"
OLLAMA_EMBEDDING_MODEL="nomic-embed-text"
```

#### For Quality (OpenAI)
```bash
DEFAULT_LLM_PROVIDER="openai"
DEFAULT_EMBEDDING_PROVIDER="openai"
OPENAI_API_KEY="sk-your-key-here"
OPENAI_MODEL="gpt-4o-mini"
OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
```

#### For Speed (Smaller Chunks)
```bash
CHUNK_SIZE=500
CHUNK_OVERLAP=100
```

#### For Quality (Larger Chunks)
```bash
CHUNK_SIZE=1500
CHUNK_OVERLAP=300
```

---

## 🐛 Troubleshooting

### "Cannot connect to Ollama"
```bash
# Make sure Ollama is running
ollama serve

# Test it
curl http://localhost:11434/api/tags
```

### "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### "OpenAI API error"
- Check your API key in `.env`
- Verify you have credits: https://platform.openai.com/usage
- Check rate limits

### "PDF parsing failed"
- Ensure the PDF is not encrypted
- Try a different PDF
- Check file size (default max: 50MB)

---

## 📊 Performance Tips

### For Large Documents (50+ pages)
```bash
# In .env
CHUNK_SIZE=1500
CHUNK_OVERLAP=300
TOP_K_PER_DOCUMENT=5
```

### For Many Documents (50+)
```bash
# In .env
MAX_CHUNKS_PER_QUERY=15
TOP_K_PER_DOCUMENT=2
```

### For Fast Responses (Ollama)
```bash
# Use smaller model
OLLAMA_MODEL="llama3.2:1b"  # Faster but less accurate
```

---

## 🔄 Switching Providers

You can switch providers **per request** without changing `.env`:

```bash
# Use Ollama for this request
curl -X POST http://localhost:8000/query \
  -F "question=..." \
  -F "session_id=..." \
  -F "llm_provider=ollama"

# Use OpenAI for this request
curl -X POST http://localhost:8000/query \
  -F "question=..." \
  -F "session_id=..." \
  -F "llm_provider=openai"
```

**Use case:** Use Ollama for testing, OpenAI for production.

---

## 📚 Next Steps

1. ✅ Read [ARCHITECTURE.md](ARCHITECTURE.md) for full details
2. ✅ Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for what's new
3. ✅ Explore the API at http://localhost:8000/docs (Swagger UI)
4. ✅ Update the frontend to use new endpoints
5. ✅ Deploy to production

---

## 🆘 Need Help?

- **API Docs**: http://localhost:8000/docs (auto-generated)
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Configuration**: See [.env.example](backend/.env.example)

---

Enjoy your multi-document RAG system! 🚀
