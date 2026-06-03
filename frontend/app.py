"""
frontend/app.py — Streamlit UI for Video Transcript RAG Assistant.

Run with:  streamlit run frontend/app.py
Requires the FastAPI backend to be running at http://localhost:8000
"""

import streamlit as st
import requests
from urllib.parse import urlparse, parse_qs
import re

BACKEND_URL = "http://localhost:8000"


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Video RAG Assistant",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0f0f0f; color: #e0e0e0; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1a1a1a;
        border-right: 1px solid #2a2a2a;
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #1e1e1e !important;
        color: #e0e0e0 !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #ff0000, #cc0000);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #ff3333, #ff0000);
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(255, 0, 0, 0.3);
    }

    /* Chat messages */
    .chat-user {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-left: 3px solid #4f8ef7;
        padding: 12px 16px;
        border-radius: 0 12px 12px 0;
        margin: 8px 0;
    }
    .chat-assistant {
        background: linear-gradient(135deg, #1a2e1a, #162116);
        border-left: 3px solid #4caf50;
        padding: 12px 16px;
        border-radius: 0 12px 12px 0;
        margin: 8px 0;
    }
    .chat-error {
        background: linear-gradient(135deg, #2e1a1a, #211616);
        border-left: 3px solid #f44336;
        padding: 12px 16px;
        border-radius: 0 12px 12px 0;
        margin: 8px 0;
    }

    /* Source chunks expander */
    .streamlit-expanderHeader {
        background-color: #1e1e1e !important;
        border-radius: 8px !important;
    }

    /* Video card */
    .video-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }

    /* Badge */
    .badge-green {
        background: #1b3a1b;
        color: #4caf50;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-red {
        background: #3a1b1b;
        color: #f44336;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-blue {
        background: #1b2a3a;
        color: #4f8ef7;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    hr { border-color: #2a2a2a; }
    h1, h2, h3 { color: #ffffff; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def extract_video_id(url: str) -> str | None:
    """Client-side video ID extraction for thumbnail display."""
    if "youtu.be" in url:
        m = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
        return m.group(1) if m else None
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    return qs.get("v", [None])[0]


def api_load_video(url: str) -> dict:
    resp = requests.post(f"{BACKEND_URL}/api/load-video", json={"url": url}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def api_query(video_id: str, query: str) -> dict:
    resp = requests.post(
        f"{BACKEND_URL}/api/query",
        json={"video_id": video_id, "query": query},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def api_list_videos() -> list[dict]:
    try:
        resp = requests.get(f"{BACKEND_URL}/api/videos", timeout=5)
        return resp.json().get("videos", [])
    except Exception:
        return []


def api_delete_video(video_id: str) -> bool:
    try:
        resp = requests.delete(f"{BACKEND_URL}/api/videos/{video_id}", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def check_backend() -> bool:
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


# ── Session state init ─────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []     # list of {role, content, from_video, chunks}

if "active_video" not in st.session_state:
    st.session_state.active_video = None   # {video_id, title, chunk_count, language}


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎥 Video RAG Assistant")
    st.markdown("---")

    # Backend status
    backend_ok = check_backend()
    if backend_ok:
        st.markdown('<span class="badge-green">● Backend Online</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-red">● Backend Offline</span>', unsafe_allow_html=True)
        st.warning("Start the backend:\n```\nuvicorn backend.main:app --reload\n```")

    st.markdown("---")
    st.markdown("### Load a Video")

    url_input = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        label_visibility="collapsed",
    )

    load_btn = st.button("🚀 Load & Index Video", use_container_width=True, disabled=not backend_ok)

    if load_btn and url_input:
        vid_id_preview = extract_video_id(url_input)
        if vid_id_preview:
            st.image(
                f"https://img.youtube.com/vi/{vid_id_preview}/mqdefault.jpg",
                use_column_width=True,
            )

        with st.spinner("Fetching transcript & building index..."):
            try:
                data = api_load_video(url_input)
                st.session_state.active_video = {
                    "video_id": data["video_id"],
                    "title": data["title"],
                    "chunk_count": data["chunk_count"],
                    "language": data["language"],
                }
                st.session_state.chat_history = []
                st.success(f"✅ Indexed {data['chunk_count']} chunks")
            except requests.HTTPError as e:
                detail = e.response.json().get("detail", str(e))
                st.error(f"❌ {detail}")
            except Exception as e:
                st.error(f"❌ {e}")

    # Active video info
    if st.session_state.active_video:
        v = st.session_state.active_video
        st.markdown("---")
        st.markdown("### Active Video")
        st.markdown(f"""
<div class="video-card">
    <b>📹 {v['title']}</b><br/>
    <small style="color:#888">ID: {v['video_id']}</small><br/><br/>
    <span class="badge-blue">🌐 {v['language']}</span>&nbsp;
    <span class="badge-blue">📄 {v['chunk_count']} chunks</span>
</div>
""", unsafe_allow_html=True)
        if st.button("🗑️ Remove Video", use_container_width=True):
            api_delete_video(v["video_id"])
            st.session_state.active_video = None
            st.session_state.chat_history = []
            st.rerun()

    # Loaded videos list
    all_videos = api_list_videos()
    if len(all_videos) > 1:
        st.markdown("---")
        st.markdown("### Switch Video")
        for v in all_videos:
            if st.button(f"📹 {v['title'][:30]}...", key=f"switch_{v['video_id']}"):
                st.session_state.active_video = v
                st.session_state.chat_history = []
                st.rerun()

    st.markdown("---")
    st.markdown("""
<small style="color:#555">
Built with FastAPI + FAISS + Gemini<br/>
Embeddings: all-MiniLM-L6-v2
</small>
""", unsafe_allow_html=True)


# ── Main area ──────────────────────────────────────────────────────────────────
st.markdown("# 🎥 Video Transcript RAG Assistant")
st.markdown("Ask anything about the video — answers come only from its transcript.")
st.markdown("---")

if not st.session_state.active_video:
    # Empty state
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
<div style="text-align:center; padding: 60px 0; color: #555;">
    <div style="font-size: 4rem;">🎬</div>
    <h3 style="color: #777; margin-top: 16px;">No video loaded yet</h3>
    <p>Paste a YouTube URL in the sidebar and click <b>Load & Index Video</b></p>
    <br/>
    <b style="color:#444">Supported formats:</b><br/>
    <code style="color:#666">youtube.com/watch?v=...</code><br/>
    <code style="color:#666">youtu.be/...</code><br/>
    <code style="color:#666">youtube.com/shorts/...</code>
</div>
""", unsafe_allow_html=True)
else:
    active = st.session_state.active_video

    # Show thumbnail + title
    vid_id = active["video_id"]
    col_thumb, col_info = st.columns([1, 3])
    with col_thumb:
        st.image(f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg", use_column_width=True)
    with col_info:
        st.markdown(f"### {active['title']}")
        st.markdown(
            f'<span class="badge-blue">🌐 {active["language"]}</span>&nbsp;'
            f'<span class="badge-blue">📄 {active["chunk_count"]} chunks</span>&nbsp;'
            f'<a href="https://www.youtube.com/watch?v={vid_id}" target="_blank" '
            f'style="color:#ff4444; text-decoration:none;">▶ Watch on YouTube</a>',
            unsafe_allow_html=True,
        )
        st.markdown(f"<small style='color:#555'>Video ID: {vid_id}</small>", unsafe_allow_html=True)

    st.markdown("---")

    # ── Chat history ───────────────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
<div style="text-align:center; padding: 40px 0; color: #444;">
    <div style="font-size: 2rem;">💬</div>
    <p>Video is indexed! Start asking questions below.</p>
</div>
""", unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div class="chat-user">👤 <b>You:</b> {msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    badge = (
                        '<span class="badge-green">✓ From Video</span>'
                        if msg.get("from_video", True)
                        else '<span class="badge-red">✗ Not in Video</span>'
                    )
                    st.markdown(
                        f'<div class="chat-assistant">🤖 <b>Assistant:</b> {badge}<br/><br/>{msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )

                    # Source chunks
                    if msg.get("chunks"):
                        with st.expander(f"📄 View {len(msg['chunks'])} source chunks", expanded=False):
                            for i, chunk in enumerate(msg["chunks"], 1):
                                dist = chunk.get("distance", 0)
                                st.markdown(f"**Chunk {i}** — distance: `{dist:.4f}`")
                                st.markdown(
                                    f"<div style='background:#111; padding:10px; border-radius:6px; "
                                    f"font-size:0.85rem; color:#aaa;'>{chunk['text']}</div>",
                                    unsafe_allow_html=True,
                                )
                                if i < len(msg["chunks"]):
                                    st.markdown("---")

    # ── Query input ────────────────────────────────────────────────────────────
    st.markdown("---")
    query_col, btn_col = st.columns([5, 1])
    with query_col:
        query = st.text_input(
            "Ask a question",
            placeholder="What is this video about? / What does the speaker say about...?",
            key="query_input",
            label_visibility="collapsed",
        )
    with btn_col:
        ask_btn = st.button("Ask ➤", use_container_width=True)

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", use_container_width=False):
            st.session_state.chat_history = []
            st.rerun()

    # ── Handle query ───────────────────────────────────────────────────────────
    if ask_btn and query.strip():
        st.session_state.chat_history.append({"role": "user", "content": query.strip()})

        with st.spinner("Searching transcript & generating answer..."):
            try:
                result = api_query(active["video_id"], query.strip())
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "from_video": result["from_video"],
                    "chunks": result.get("source_chunks", []),
                })
            except requests.HTTPError as e:
                detail = e.response.json().get("detail", str(e))
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"⚠️ Error: {detail}",
                    "from_video": False,
                    "chunks": [],
                })
            except Exception as e:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"⚠️ Could not reach backend: {e}",
                    "from_video": False,
                    "chunks": [],
                })

        st.rerun()