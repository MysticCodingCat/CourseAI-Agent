from .base import BaseAgent
from typing import Dict, Any, List

class KnowledgeAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Knowledge")
        # In future: Load Vector DB or PDF text here
        self.mock_knowledge_base = {
            "transformer": "Transformers are a type of deep learning model introduced in 2017...",
            "attention": "Attention mechanism allows the model to focus on different parts of the input..."
        }

    async def process(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Retrieves information based on keywords provided by the Listener Agent.
        """
        results = []
        for kw in keywords:
            # Mock Retrieval (RAG)
            info = self.mock_knowledge_base.get(kw.lower(), f"General information about {kw}")
            results.append({"keyword": kw, "info": info})
            
        return {
            "source": "lecture_notes_p15.pdf", # Mock source
            "retrieval_results": results
        }
