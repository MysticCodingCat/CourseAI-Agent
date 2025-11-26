from .base import BaseAgent
from typing import Dict, Any

class TutorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Tutor")

    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a Socratic question based on the concept being discussed.
        """
        concept = context.get("retrieval_results", [{}])[0].get("keyword", "unknown topic")
        
        # Real implementation: Prompt LLM to generate a question
        question = f"Why do you think {concept} is important in this context?"
        
        return {
            "type": "socratic_question",
            "content": question,
            "options": ["Option A", "Option B"] # Optional for quiz mode
        }
