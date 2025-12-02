"""
Knowledge Agent V2 - 整合 GraphRAG
使用真實的 RAG 檢索取代模擬檢索
"""
from .base import BaseAgent
from .prompts import KNOWLEDGE_RAG_PROMPT
from typing import Dict, Any, List
import json


class KnowledgeAgentV2(BaseAgent):
    """
    Knowledge Agent V2 - 整合 GraphRAG 的知識檢索代理

    功能：
    1. 接收關鍵詞
    2. 使用 GraphRAG 進行混合檢索
    3. 返回結構化知識
    """

    def __init__(self, rag_engine=None):
        super().__init__(name="Knowledge_V2")
        self.rag_engine = rag_engine  # GraphRAG 實例

    async def process(self, keywords: List[str]) -> Dict[str, Any]:
        """
        處理知識檢索請求

        Args:
            keywords: 關鍵詞列表

        Returns:
            檢索結果
        """
        topic = keywords[0] if keywords else "Unknown Topic"

        if self.rag_engine is None:
            # 如果沒有 RAG 引擎，返回提示
            return {
                "source": "No RAG engine loaded",
                "retrieval_results": [
                    {
                        "keyword": topic,
                        "info": "請先上傳課程講義以啟用 RAG 檢索功能。"
                    }
                ]
            }

        # 使用 GraphRAG 進行檢索
        print(f"[Knowledge V2] 檢索: {topic}")
        search_results = self.rag_engine.hybrid_search(topic, top_k=3)

        # 整合檢索結果
        vector_results = search_results.get("vector_results", [])
        graph_results = search_results.get("graph_results", [])

        # 構建上下文
        context = ""
        if vector_results:
            context += "相關段落:\n"
            for i, r in enumerate(vector_results[:2], 1):
                context += f"{i}. [頁{r['page']}] {r['text']}\n\n"

        if graph_results:
            context += "關聯概念:\n"
            for i, r in enumerate(graph_results[:3], 1):
                path_str = " -> ".join(r["path"])
                context += f"{i}. {path_str}\n"

        # 使用 LLM 整合資訊
        prompt = f"""主題: {topic}

從課程講義中檢索到以下資訊：

{context}

請根據以上資訊，用繁體中文提供：
1. 該主題的清晰定義
2. 講義來源頁碼
3. 關鍵要點

格式：
**定義：** ...
**講義出處：** 第 X 頁
**關鍵要點：**
- ...
- ..."""

        llm_response = await self.call_llm(prompt, system_prompt=KNOWLEDGE_RAG_PROMPT)

        # 返回結構化結果
        return {
            "source": f"課程講義（共 {len(vector_results)} 個相關段落）",
            "retrieval_results": [
                {
                    "keyword": topic,
                    "info": llm_response,
                    "vector_matches": len(vector_results),
                    "graph_relations": len(graph_results)
                }
            ]
        }

    def set_rag_engine(self, rag_engine):
        """設置 RAG 引擎"""
        self.rag_engine = rag_engine
        print(f"[Knowledge V2] RAG 引擎已連接")
