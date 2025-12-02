# Project Status & Handoff Guide

**Last Updated:** 2025-11-26
**Current Phase:** Phase 1 - Core Development (Mid-stage)
**Team:** Team1 (CourseAI)

## 🟢 1. Completed Features (已完成)

### Backend (Python / FastAPI)
*   **Multi-Agent Architecture:** Implemented `Listener`, `Knowledge`, `Tutor`, and `NoteTaker` agents.
*   **LLM Integration:** Successfully connected to **Gemini 2.5 Flash** for logic and generation.
*   **Prompt Engineering:** Hybrid strategy (English instructions for logic, Traditional Chinese for user-facing output).
*   **Real-time Streaming:** WebSocket endpoint (`/ws/transcription`) for low-latency audio text processing.
*   **Session Memory:** In-memory storage of full lecture transcripts for summarization.

### Frontend (Chrome Extension / Manifest V3)
*   **Full Page UI:** Switched from Popup to Side Panel/Tab interface for stable recording.
*   **Speech-to-Text:** Integrated **Web Speech API** with `cmn-Hant-TW` (Taiwanese Mandarin) support.
*   **Real-time Interaction:** Displays "Insight Cards" (Concept + Socratic Question) dynamically.
*   **Lecture Notes Generation:** Implemented a "Stop & Generate" workflow that produces structured Markdown notes.
*   **Local Rendering:** Custom lightweight Markdown parser (`simple-markdown.js`) to comply with CSP security rules.

## 🟡 2. In Progress / Next Priority (待辦事項)

### 核心技術補完 (Must-Haves)
1.  **RAG (Retrieval-Augmented Generation) Implementation:**
    *   [ ] Endpoint: `/upload_pdf`
    *   [ ] Logic: Parse PDF -> Chunking -> Vector Embedding -> Retrieval.
    *   [ ] Goal: Stop the agents from hallucinating; ground them in the uploaded slides.
2.  **Critic Agent (Fact Checking):**
    *   [ ] Logic: Detect controversial statements and cross-reference with knowledge base.

## 🚀 3. Technical Innovations (The "Winning" Features)
*See `TECHNICAL_HIGHLIGHTS.md` for details.*
1.  **GraphRAG (Dynamic Knowledge Graph Construction)** - *Beyond simple vector search.*
2.  **Multimodal Late Fusion (Visual-Audio Alignment)** - *Agent "sees" the slides.*
3.  **Hierarchical Context Compression** - *Handling 2-hour lectures efficiently.*

## 🛠️ Environment Setup
*   **Root:** `C:\Users\aano5\Desktop\claude_api\AMD AI Agent Online Hackathon\CourseAI-Agent`
*   **Backend:**
    ```powershell
    cd backend
    venv\Scripts\activate
    uvicorn app.main:app --reload
    ```
*   **Frontend:** Load unpacked from `extension/` directory in `chrome://extensions`.