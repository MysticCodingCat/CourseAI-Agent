from .base import BaseAgent
from .prompts import TUTOR_SOCRATIC_PROMPT
from typing import Dict, Any
import json
import re

class TutorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Tutor")

    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        results = context.get("retrieval_results", [])
        if not results:
            return {"error": "No context"}

        knowledge_info = results[0].get("info", "")
        topic = results[0].get("keyword", "")
        
        prompt = f"Current Topic: {topic}\nContext: {knowledge_info}"
        
        llm_response = await self.call_llm(prompt, system_prompt=TUTOR_SOCRATIC_PROMPT)
        
        try:
            cleaned_response = self._clean_json_string(llm_response)
            data = json.loads(cleaned_response)
            
            return {
                "type": "socratic_question",
                "content": data.get("question"),
                "hint": data.get("hint"),
                "difficulty": data.get("difficulty")
            }
        except Exception as e:
             print(f"[Tutor] JSON Parse Error: {e}. Raw: {llm_response}")
             # Fallback if JSON fails
             return {
                 "type": "socratic_question",
                 "content": f"Could you explain {topic} in your own words?",
                 "hint": "Think about its definition."
             }

    def _clean_json_string(self, s: str) -> str:
        """Removes markdown code blocks and GPT-OSS prefixes to extract raw JSON string."""
        # Remove GPT-OSS-120B's analysis/assistantfinal prefixes
        s = re.sub(r"^.*?assistantfinal", "", s, flags=re.DOTALL)
        # Remove markdown code blocks
        s = re.sub(r"```json\s*", "", s)
        s = re.sub(r"```", "", s)
        return s.strip()