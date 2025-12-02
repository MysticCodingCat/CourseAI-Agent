from .base import BaseAgent
from .prompts import LISTENER_PROMPT
from typing import Dict, Any
import json
import re

class ListenerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Listener")
        
    async def process(self, transcript_segment: str) -> Dict[str, Any]:
        # 1. Prepare Prompt
        prompt = f"Timestamp: [Current], text: \"{transcript_segment}\""
        
        # 2. Call LLM
        llm_response = await self.call_llm(prompt, system_prompt=LISTENER_PROMPT)
        print(f"[Listener] RAW LLM RESPONSE: {llm_response}")  # DEBUG PRINT
        
        # 3. Parse JSON (Clean up markdown code blocks if any)
        try:
            cleaned_response = self._clean_json_string(llm_response)
            print(f"[Listener] CLEANED JSON: {cleaned_response}") # DEBUG PRINT
            data = json.loads(cleaned_response)
            print(f"[Listener] PARSED DATA: {data}") # DEBUG PRINT
            
            if data.get("is_educational"):
                return {
                    "status": "active",
                    "action": "notify_knowledge_agent",
                    "keywords": [data.get("topic")],
                    "reasoning": data.get("reasoning"),
                    "segment": transcript_segment
                }
            else:
                return {
                    "status": "passive",
                    "action": "ignore"
                }
        except Exception as e:
            print(f"[Listener] JSON Parse Error: {e}. Raw: {llm_response}")
            return {"status": "passive", "action": "error"}

    def _clean_json_string(self, s: str) -> str:
        """Removes markdown code blocks and GPT-OSS prefixes to extract raw JSON string."""
        # Remove GPT-OSS-120B's analysis/assistantfinal prefixes
        s = re.sub(r"^.*?assistantfinal", "", s, flags=re.DOTALL)
        # Remove markdown code blocks
        s = re.sub(r"```json\s*", "", s)
        s = re.sub(r"```", "", s)
        return s.strip()