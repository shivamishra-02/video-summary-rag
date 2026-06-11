<div align="center">

# 🎥 Video Transcript RAG Assistant

**Ask questions about any YouTube video using its transcript as a knowledge base.**

Powered by **Google Gemini 2.0 Flash** · **FAISS** · **Sentence Transformers** · **FastAPI** · **Streamlit**

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Streamlit-FF4B4B?style=for-the-badge)](https://video-summary-rag-v9sak4juxoznuwfwjxyyh7.streamlit.app)
[![API Docs](https://img.shields.io/badge/📡_API_Docs-Railway-0B0D0E?style=for-the-badge)](https://web-production-39b1e.up.railway.app/docs)
[![Backend](https://img.shields.io/badge/🔧_Backend-Health-22c55e?style=for-the-badge)](https://web-production-39b1e.up.railway.app/health)

</div>

---

## ✨ Features

- 🔗 **Any YouTube URL** — watch, shorts, youtu.be links all supported
- 📝 **Auto transcript fetch** — no YouTube Data API key needed
- 🧠 **Local embeddings** — `all-MiniLM-L6-v2` via Sentence Transformers
- ⚡ **FAISS vector search** — millisecond similarity search
- 🤖 **Gemini 2.0 Flash** — free-tier LLM, grounded strictly in transcript
- 🛡️ **Two-layer out-of-scope detection** — FAISS distance threshold + LLM prompt guard
- 🎨 **Dark-themed Streamlit UI** — chat interface with source chunk viewer
- 📡 **REST API** — FastAPI backend with full OpenAPI/Swagger docs

---

## 🏗️ Architecture

```
YouTube URL
    │
    ▼
transcript_service.py   ←  youtube-transcript-api  (no API key needed)
    │
    ▼
chunking_service.py     ←  RecursiveCharacterTextSplitter (500 chars, 50 overlap)
    │
    ▼
embedding_service.py    ←  SentenceTransformer: all-MiniLM-L6-v2  (runs locally)
    │
    ▼
vector_store.py         ←  FAISS IndexFlatL2  (in-memory, per-video)
    │
    ▼  query embedding + similarity search (top-k chunks)
gemini_service.py       ←  Gemini 2.0 Flash  (grounded prompt)
    │
    ▼
Answer ✅   or   "Not in this video" ❌
```

---

## 📁 Folder Structure

```
video-summary-rag/
│
├── backend/
│   ├── main.py                    # FastAPI app + all endpoints
│   ├── config.py                  # Environment variables & constants
│   ├── models/
│   │   └── schemas.py             # Pydantic request/response models
│   ├── services/
│   │   ├── transcript_service.py  # YouTube URL → raw transcript text
│   │   ├── chunking_service.py    # Text → overlapping chunks
│   │   ├── embedding_service.py   # Chunks → float32 vectors
│   │   ├── vector_store.py        # FAISS index (add / search / delete)
│   │   ├── gemini_service.py      # Gemini 2.0 Flash API wrapper
│   │   └── rag_service.py         # End-to-end pipeline orchestrator
│   └── utils/
│       └── youtube_utils.py       # URL parsing & video ID extraction
│
├── frontend/
│   └── app.py                     # Streamlit chat UI
│
├── tests/
│   ├── test_transcript.py
│   ├── test_rag.py
│   └── test_api.py
│
├── .streamlit/
│   └── config.toml                # Streamlit dark theme config
│
├── requirements.txt               # Streamlit Cloud dependencies
├── requirements-backend.txt       # Railway backend dependencies
├── railway.json                   # Railway deploy config
├── .env.example                   # Environment variable template
└── README.md
```

---

## 🚀 Quick Start (Local)

### 1. Clone & setup

```bash
git clone https://github.com/shivamishra-02/video-summary-rag
cd video-summary-rag

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements-backend.txt
```

### 2. Add environment variables

```bash
cp .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=your_key_here   # Get free key: https://aistudio.google.com
```

### 3. Run backend

```bash
uvicorn backend.main:app --reload --port 8000
# API docs → http://localhost:8000/docs
```

### 4. Run frontend (new terminal)

```bash
streamlit run frontend/app.py
# UI → http://localhost:8501
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server health + loaded video count |
| `POST` | `/api/load-video` | Fetch transcript & build FAISS index |
| `POST` | `/api/query` | Ask a question about an indexed video |
| `GET` | `/api/videos` | List all currently indexed videos |
| `DELETE` | `/api/videos/{id}` | Remove a video index from memory |

### Example — Load a video
```bash
curl -X POST https://web-production-39b1e.up.railway.app/api/load-video \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Example — Ask a question
```bash
curl -X POST https://web-production-39b1e.up.railway.app/api/query \
  -H "Content-Type: application/json" \
  -d '{"video_id": "dQw4w9WgXcQ", "query": "What is this song about?"}'
```

---

## ☁️ Deployment

| Service | Platform | URL |
|---------|----------|-----|
| 🔧 FastAPI Backend | Railway | https://web-production-39b1e.up.railway.app |
| 🎨 Streamlit Frontend | Streamlit Cloud | https://video-summary-rag-v9sak4juxoznuwfwjxyyh7.streamlit.app |

### Deploy your own

**Backend → Railway:**
1. Push repo to GitHub
2. New project on [railway.app](https://railway.app) → Deploy from GitHub
3. Add env var: `GEMINI_API_KEY`
4. Railway auto-detects `railway.json` and deploys

**Frontend → Streamlit Cloud:**
1. Go to [share.streamlit.io](https://share.streamlit.io) → New app
2. Set main file: `frontend/app.py`, Python: `3.11`
3. Add secrets:
```toml
GEMINI_API_KEY = "your_key"
BACKEND_URL = "https://your-railway-url.up.railway.app"
```

---

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | **Required.** Get free from [aistudio.google.com](https://aistudio.google.com) |
| `BACKEND_URL` | `http://localhost:8000` | FastAPI backend URL (set on Streamlit Cloud) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence Transformers model |
| `CHUNK_SIZE` | `500` | Characters per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `TOP_K_RESULTS` | `4` | Chunks retrieved per query |
| `SIMILARITY_THRESHOLD` | `1.2` | L2 distance cutoff for out-of-scope detection |

---

## 🧪 Running Tests

```bash
pytest tests/ -v

# Individual suites
pytest tests/test_transcript.py -v   # URL parsing & transcript fetch
pytest tests/test_rag.py -v          # Chunking, embeddings, vector store
pytest tests/test_api.py -v          # FastAPI endpoints (no real API calls)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Google Gemini 2.0 Flash (`google-generativeai`) |
| Embeddings | `sentence-transformers` — all-MiniLM-L6-v2 |
| Vector Store | `faiss-cpu` — IndexFlatL2 |
| Transcript | `youtube-transcript-api` |
| Backend | `FastAPI` + `uvicorn` |
| Frontend | `Streamlit` |
| Text Splitting | `langchain-text-splitters` |
| Deployment | Railway (backend) + Streamlit Cloud (frontend) |

---

## 👨‍💻 Developer

**Shivam Mishra**

[![GitHub](https://img.shields.io/badge/GitHub-shivamishra--02-181717?style=flat&logo=github)](https://github.com/shivamishra-02)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Shivam%20Mishra-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/shivam-mishra-3a741b253/)

---

## 📝 License

MIT