from .base import BaseAgent
from typing import Dict, Any

class ListenerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Listener")
        
    async def process(self, transcript_segment: str) -> Dict[str, Any]:
        """
        Analyzes the live transcript to identify if it contains key concepts
        that require explanation or retrieval.
        """
        system_prompt = """
        You are the Listener Agent. Your job is to monitor the live transcript of a lecture.
        Analyze the incoming text segment.
        1. Identify if there are any complex technical terms, key concepts, or formulas.
        2. If the content is chit-chat or administrative (e.g., "Can you hear me?"), ignore it.
        3. Return a JSON indicating if 'intervention' is needed.
        """
        
        # Mock logic for prototype
        is_important = len(transcript_segment) > 10 and "concept" in transcript_segment.lower()
        
        if is_important:
            # In real implementation, LLM determines the keywords
            keywords = ["Sample Keyword"] 
            return {
                "status": "active",
                "action": "notify_knowledge_agent",
                "keywords": keywords,
                "segment": transcript_segment
            }
        else:
            return {
                "status": "passive",
                "action": "ignore"
            }
