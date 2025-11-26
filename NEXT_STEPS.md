# Project Status & Handoff Guide

**Last Updated:** 2025-11-26
**Current Phase:** Phase 1 - Core Development (Mid-stage)

## ✅ Completed Features
1.  **Backend (FastAPI):**
    *   Multi-Agent Architecture (Listener, Knowledge, Tutor, NoteTaker).
    *   WebSocket streaming for real-time transcription.
    *   Integration with **Gemini 2.5 Flash API** (via `google-generativeai`).
    *   Prompt Engineering: English logic + Traditional Chinese output.
    *   Session memory (`transcript_history`) for lecture summarization.
2.  **Frontend (Chrome Extension):**
    *   **Manifest V3** compliant (Side Panel / Full Page style).
    *   **Web Speech API** for real-time Chinese speech-to-text.
    *   **UI/UX:** Recording controls, Real-time Insight Cards, Markdown-rendered Lecture Notes Modal.
    *   **Local Markdown Parsing:** Removed CDN dependency for CSP compliance.

## 🚧 Current Focus: RAG Implementation
The next immediate task is to implement **PDF Upload & Retrieval Augmented Generation (RAG)**.

## 📋 Next Steps (To-Do)
1.  **Backend:** Implement `/upload_pdf` endpoint.
    *   Library: `PyPDF2` or `pdfminer`.
    *   Logic: Extract text, chunk it, and store in a simple vector store (or in-memory list for MVP).
2.  **Agent Logic:** Update `KnowledgeAgent` and `NoteTakerAgent` to query the uploaded PDF content instead of hallucinating/using internal knowledge.
3.  **Frontend:** Add a "Upload PDF" button in the UI.

## 🛠️ Environment Setup
*   **Root:** `C:\Users\aano5\Desktop\claude_api\AMD AI Agent Online Hackathon\CourseAI-Agent`
*   **Backend:** `cd backend` -> `venv\Scripts\activate` -> `uvicorn app.main:app --reload`
*   **Frontend:** Load unpacked from `extension/` directory.
