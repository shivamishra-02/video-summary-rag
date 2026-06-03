# 🎥 Video Transcript RAG Assistant

Ask questions about **any YouTube video** using its transcript as a knowledge base — powered by **Google Gemini**, **FAISS**, and **Sentence Transformers**.

> If the answer isn't in the video, the assistant says so — no hallucinations.

---

## ✨ Features

- 🔗 **Any YouTube URL** — watch, shorts, youtu.be links all supported
- 📝 **Auto transcript** — no YouTube API key needed
- 🧠 **Local embeddings** — `all-MiniLM-L6-v2` runs on your machine
- ⚡ **FAISS vector search** — millisecond similarity search
- 🤖 **Gemini 2.0 Flash** — free-tier LLM, grounded strictly in transcript
- 🛡️ **Out-of-scope detection** — two-layer guard (distance threshold + LLM prompt)
- 🎨 **Streamlit UI** — dark-themed chat interface
- 📡 **REST API** — FastAPI backend with full OpenAPI docs

---

## 🏗️ Architecture

```
YouTube URL
    │
    ▼
transcript_service.py   ← youtube-transcript-api (no key needed)
    │
    ▼
chunking_service.py     ← RecursiveCharacterTextSplitter (500 chars, 50 overlap)
    │
    ▼
embedding_service.py    ← SentenceTransformer (all-MiniLM-L6-v2, local)
    │
    ▼
vector_store.py         ← FAISS IndexFlatL2 (in-memory, per-video)
    │
    ▼  ← query embedding + similarity search
gemini_service.py       ← Gemini 1.5 Flash (grounded prompt)
    │
    ▼
Answer ✅  or  "Not in this video" ❌
```

---

## 📁 Folder Structure

```
video-summary-rag/
├── backend/
│   ├── main.py                  # FastAPI app + all endpoints
│   ├── config.py                # Environment variables
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── services/
│   │   ├── transcript_service.py  # YouTube → raw transcript
│   │   ├── chunking_service.py    # Text → chunks
│   │   ├── embedding_service.py   # Chunks → vectors
│   │   ├── vector_store.py        # FAISS index management
│   │   ├── gemini_service.py      # Gemini API wrapper
│   │   └── rag_service.py         # Pipeline orchestrator
│   └── utils/
│       └── youtube_utils.py       # URL parsing helpers
├── frontend/
│   └── app.py                   # Streamlit UI
├── tests/
│   ├── test_transcript.py
│   ├── test_rag.py
│   └── test_api.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & setup

```bash
git clone https://github.com/shivamishra-02/video-summary-rag
cd video-summary-rag

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Add your Gemini API key

```bash
cp .env.example .env
```

Edit `.env` and set:
```
GEMINI_API_KEY=your_key_here
```

Get a free key at 👉 https://aistudio.google.com

### 3. Run the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 4. Run the frontend (new terminal)

```bash
streamlit run frontend/app.py
```

Opens at: http://localhost:8501

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server status |
| `POST` | `/api/load-video` | Index a YouTube video |
| `POST` | `/api/query` | Ask a question |
| `GET` | `/api/videos` | List indexed videos |
| `DELETE` | `/api/videos/{id}` | Remove a video |

### Load a video
```bash
curl -X POST http://localhost:8000/api/load-video \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Ask a question
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"video_id": "dQw4w9WgXcQ", "query": "What is this song about?"}'
```

---

## 🧪 Running Tests

```bash
# All tests (no API calls needed)
pytest tests/ -v

# Individual test files
pytest tests/test_transcript.py -v
pytest tests/test_rag.py -v
pytest tests/test_api.py -v
```

---

## ⚙️ Configuration

All settings are in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Required. Get from aistudio.google.com |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformer model |
| `CHUNK_SIZE` | `500` | Characters per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `TOP_K_RESULTS` | `4` | Chunks retrieved per query |
| `SIMILARITY_THRESHOLD` | `1.2` | L2 distance cutoff for out-of-scope |

---

## 🛠️ Tech Stack

| Component | Library |
|-----------|---------|
| LLM | `google-generativeai` (Gemini 1.5 Flash) |
| Embeddings | `sentence-transformers` |
| Vector DB | `faiss-cpu` |
| Transcript | `youtube-transcript-api` |
| Backend | `FastAPI` + `uvicorn` |
| Frontend | `Streamlit` |
| Text splitting | `langchain-text-splitters` |

---

## 📝 License

MIT