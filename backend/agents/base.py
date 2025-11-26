from typing import List, Dict, Any, Optional
import time

class BaseAgent:
    def __init__(self, name: str, model_endpoint: str = "mock_endpoint"):
        self.name = name
        self.model_endpoint = model_endpoint
    
    async def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Base method to process input. Should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement process method")

    async def call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """
        Wrapper to call the LLM API. 
        Currently a MOCK implementation until 12/1.
        """
        # TODO: Replace with actual HTTP request to AMD MI300X endpoint
        print(f"[{self.name}] Calling LLM with prompt length: {len(prompt)}")
        
        # Simulate network delay
        import asyncio
        await asyncio.sleep(0.5)
        
        return f"Mock response from {self.name}: Processed '{prompt[:20]}...'"
