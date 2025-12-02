from typing import Dict, Any, Optional
import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
# import google.generativeai as genai  # GEMINI FALLBACK - Keep commented unless needed

# Load environment variables
load_dotenv()

# GPU-OSS-120B Configuration (AMD Instinct MI300X)
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://210.61.209.139:45014/v1/")
VLLM_MODEL_NAME = "openai/gpt-oss-120b"

# Gemini Fallback (commented out by default)
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if GEMINI_API_KEY:
#     genai.configure(api_key=GEMINI_API_KEY)

class BaseAgent:
    def __init__(self, name: str):
        self.name = name
        self.llm_mode = os.getenv("LLM_MODE", "gpt-oss")  # "gpt-oss" or "gemini"

        if self.llm_mode == "gpt-oss":
            # Initialize vLLM client for GPT-OSS-120B
            self.client = OpenAI(base_url=VLLM_BASE_URL, api_key="NA")
            self.model_name = VLLM_MODEL_NAME
            print(f"[{self.name}] Initialized with GPT-OSS-120B on AMD MI300X")
        # else:
        #     # Gemini fallback (keep commented)
        #     self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        #     print(f"[{self.name}] Initialized with Gemini 2.5 Flash (FALLBACK)")

    async def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Base method to process input. Should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement process method")

    async def call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """
        Calls the GPT-OSS-120B API via vLLM (OpenAI-compatible endpoint).
        """
        print(f"[{self.name}] Calling GPT-OSS-120B...")

        try:
            if self.llm_mode == "gpt-oss":
                # OpenAI-style chat completion
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,  # Lower temperature for more stable JSON output
                    max_tokens=2048,
                )
                return response.choices[0].message.content

            # else:
            #     # Gemini fallback (commented out)
            #     full_prompt = f"{system_prompt}\n\nUser Input:\n{prompt}"
            #     response = self.model.generate_content(full_prompt)
            #     return response.text

        except Exception as e:
            print(f"[{self.name}] Error calling GPT-OSS-120B: {e}")
            return f"Error: {str(e)}"