from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import json

# Import Agents
from agents.listener import ListenerAgent
from agents.knowledge import KnowledgeAgent
from agents.tutor import TutorAgent
from agents.notetaker import NoteTakerAgent

app = FastAPI(title="CourseAI Backend", version="0.3.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agents
listener_agent = ListenerAgent()
knowledge_agent = KnowledgeAgent()
tutor_agent = TutorAgent()
notetaker_agent = NoteTakerAgent()

# In-memory storage for the current session's transcript
# In a real app, this should be a database or session-based storage
transcript_history: List[str] = []

@app.get("/")
def read_root():
    return {"message": "CourseAI Agent Backend is running!"}

@app.post("/reset_session")
def reset_session():
    global transcript_history
    transcript_history = []
    return {"message": "Session reset", "transcript_count": 0}

@app.post("/generate_notes")
async def generate_notes():
    global transcript_history
    full_text = "\n".join(transcript_history)
    
    if not full_text:
        return {"notes": "# 尚無內容\n請先開始錄音。"}

    print(f"Generating notes for {len(transcript_history)} segments...")
    markdown_notes = await notetaker_agent.process(full_text)
    
    return {"notes": markdown_notes}

@app.websocket("/ws/transcription")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected to WebSocket")
    
    try:
        while True:
            data = await websocket.receive_text()
            transcript_data = json.loads(data)
            text_segment = transcript_data.get("text", "")
            
            if text_segment:
                print(f"Received: {text_segment}")
                # Store in history
                transcript_history.append(text_segment)

                # Real-time Analysis Pipeline
                listener_result = await listener_agent.process(text_segment)
                
                if listener_result["status"] == "active":
                    keywords = listener_result["keywords"]
                    knowledge_result = await knowledge_agent.process(keywords)
                    tutor_result = await tutor_agent.process(knowledge_result)
                    
                    response = {
                        "type": "insight",
                        "timestamp": transcript_data.get("timestamp"),
                        "knowledge": knowledge_result,
                        "tutor": tutor_result
                    }
                    await websocket.send_json(response)
                else:
                    await websocket.send_json({"type": "ack", "status": "ignored"})
                
    except WebSocketDisconnect:
        print("Client disconnected")
