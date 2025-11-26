from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import json

# Import Agents
from agents.listener import ListenerAgent
from agents.knowledge import KnowledgeAgent
from agents.tutor import TutorAgent

app = FastAPI(title="CourseAI Backend", version="0.2.0")

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

@app.get("/")
def read_root():
    return {"message": "CourseAI Agent Backend (Mock Mode) is running!"}

@app.websocket("/ws/transcription")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected to WebSocket")
    
    try:
        while True:
            # 1. Receive transcript segment from Frontend (Chrome Extension)
            data = await websocket.receive_text()
            transcript_data = json.loads(data)
            text_segment = transcript_data.get("text", "")
            
            print(f"Received: {text_segment}")

            # 2. Listener Agent analyzes the segment
            listener_result = await listener_agent.process(text_segment)
            
            if listener_result["status"] == "active":
                # 3. If interesting, trigger Knowledge Agent
                keywords = listener_result["keywords"]
                knowledge_result = await knowledge_agent.process(keywords)
                
                # 4. Trigger Tutor Agent to generate a question
                tutor_result = await tutor_agent.process(knowledge_result)
                
                # 5. Send everything back to frontend
                response = {
                    "type": "insight",
                    "timestamp": transcript_data.get("timestamp"),
                    "knowledge": knowledge_result,
                    "tutor": tutor_result
                }
                await websocket.send_json(response)
            
            else:
                # Acknowledge receipt but do nothing
                await websocket.send_json({"type": "ack", "status": "ignored"})
                
    except WebSocketDisconnect:
        print("Client disconnected")