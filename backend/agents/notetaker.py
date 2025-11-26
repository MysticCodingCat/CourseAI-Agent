from .base import BaseAgent
from .prompts import NOTETAKER_PROMPT
from typing import Dict, Any
import google.generativeai as genai

class NoteTakerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="NoteTaker")
        # Use a model with larger context window if available, but Flash is good for speed
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')

    async def process(self, full_transcript: str) -> str:
        """
        Generates structured notes from the full lecture transcript.
        """
        if not full_transcript or len(full_transcript) < 10:
            return "# 課程內容不足\n請錄製更多內容以生成筆記。"

        print(f"[NoteTaker] Generating notes for transcript length: {len(full_transcript)}")
        
        try:
            # We don't need JSON here, just pure Markdown text
            response = await self.call_llm(full_transcript, system_prompt=NOTETAKER_PROMPT)
            return response
        except Exception as e:
            print(f"[NoteTaker] Error: {e}")
            return f"# 錯誤\n生成筆記時發生錯誤: {e}"