# CourseAI Agent (AgentX Challenge)

**Team:** Team1  
**Event:** AMD AI Agent Online Hackathon  
**Theme:** AgentX: The Instinct MI300X LLM Mission

##  Project Overview

**CourseAI** is a Multi-Agent System designed to revolutionize online learning on Google Meet. By leveraging the massive memory and computing power of the **AMD Instinct MI300X**, CourseAI provides real-time, context-aware assistance that goes beyond simple transcription.

It features a **"Socratic Tutor"** architecture where multiple AI agents collaborate to listen, understand, and teach.

##  Agentic Architecture (CourseAI 2.0)

The system is driven by three specialized agents running on **GPT OSS 120B**:

1.  ** The Listener Agent:** 
    *   Monitors real-time audio streams from Google Meet.
    *   Filters noise and identifies key concepts dynamically.
2.  ** The Knowledge Agent:** 
    *   Performs RAG (Retrieval-Augmented Generation) on course materials (PDFs).
    *   Cross-references spoken words with lecture slides in real-time.
3.  ** The Socratic Tutor Agent:** 
    *   Pedagogical engine that generates probing questions instead of direct answers.
    *   Guides the student's thought process based on the current context.

## 🛠️ Tech Stack

*   **Compute:** AMD Instinct MI300X (ROCm Platform)
*   **Model:** GPT OSS 120B (OpenAI API Compatible Endpoint)
*   **Backend:** Python, FastAPI
*   **Frontend:** Chrome Extension (React, TypeScript)
*   **Vector Store:** FAISS / ChromaDB (for RAG)

##  Project Structure

```bash
CourseAI-Agent/
├── backend/          # FastAPI backend & Agent Logic
│   ├── app/          # API Endpoints
│   └── agents/       # Agent Prompts & Chains
├── extension/        # Chrome Extension Source Code
├── docs/             # Documentation & Assets
└── README.md         # This file
```

##  Getting Started

(Instructions on how to deploy and run the agent will be added here)

---
*This project is submitted for the AMD AI Agent Online Hackathon 2025.*
