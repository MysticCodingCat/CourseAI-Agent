from typing import Dict, Any, Optional
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class BaseAgent:
    def __init__(self, name: str):
        self.name = name
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')
    
    async def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Base method to process input. Should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement process method")

    async def call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """
        Calls the Gemini Pro API.
        """
        if not GEMINI_API_KEY:
            print(f"[{self.name}] Warning: No API Key found. Returning mock data.")
            return "Error: No API Key"

        print(f"[{self.name}] Calling Gemini Pro...")
        
        try:
            # Gemini Pro doesn't support 'system_prompt' parameter directly in the same way as OpenAI 'system' role in some versions,
            # but we can prepend it or use the system instruction if using newer beta API.
            # For stability, we'll prepend the context.
            
            full_prompt = f"{system_prompt}\n\nUser Input:\n{prompt}"
            
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"[{self.name}] Error calling Gemini: {e}")
            return str(e)