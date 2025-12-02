"""
GraphRAG Engine - 知識圖譜增強檢索
結合向量檢索與知識圖譜，實現多跳推理能力
"""
import fitz  # PyMuPDF
import numpy as np
import networkx as nx
from typing import List, Dict, Tuple, Any
from sentence_transformers import SentenceTransformer
import faiss
import json
import re
from openai import OpenAI
import os


class GraphRAG:
    """
    GraphRAG: 結合向量檢索與知識圖譜的檢索增強生成系統

    核心功能：
    1. 向量檢索：找到語意相似的文本段落
    2. 圖譜檢索：透過實體關係進行多跳推理
    """

    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        初始化 GraphRAG

        Args:
            embedding_model: 輕量嵌入模型（公開可用，支援多語言）
        """
        print("[GraphRAG] 初始化中...")

        # 向量嵌入模型（支援繁體中文）
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()

        # FAISS 向量索引
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.chunks = []  # 儲存原始文本塊
        self.chunk_metadata = []  # 儲存元數據（頁碼、章節等）

        # 知識圖譜（NetworkX）
        self.knowledge_graph = nx.DiGraph()

        # GPT-OSS-120B 客戶端（用於三元組提取）
        vllm_url = os.getenv("VLLM_BASE_URL", "http://210.61.209.139:45014/v1/")
        self.llm_client = OpenAI(base_url=vllm_url, api_key="NA")
        self.llm_model = "openai/gpt-oss-120b"

        print(f"[GraphRAG] 初始化完成 - 嵌入維度: {self.embedding_dim}")

    def parse_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        解析 PDF 文件，提取文本與元數據

        Args:
            pdf_path: PDF 檔案路徑

        Returns:
            List of chunks with metadata
        """
        print(f"[GraphRAG] 解析 PDF: {pdf_path}")

        doc = fitz.open(pdf_path)
        chunks = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            # 基本清理
            text = text.strip()
            if len(text) < 50:  # 跳過過短的頁面
                continue

            # 按段落切分
            paragraphs = text.split('\n\n')

            for para in paragraphs:
                para = para.strip()
                if len(para) > 100:  # 只保留有意義的段落
                    chunks.append({
                        "text": para,
                        "page": page_num + 1,
                        "source": pdf_path
                    })

        print(f"[GraphRAG] 提取了 {len(chunks)} 個文本塊")
        return chunks

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        將長文本切分為固定長度的塊（帶重疊）

        Args:
            text: 輸入文本
            chunk_size: 每塊字符數
            overlap: 重疊字符數

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += (chunk_size - overlap)

        return chunks

    def build_vector_index(self, chunks: List[Dict[str, Any]]):
        """
        建立向量索引（FAISS）

        Args:
            chunks: 文本塊列表
        """
        print("[GraphRAG] 建立向量索引...")

        self.chunks = chunks
        texts = [chunk["text"] for chunk in chunks]

        # 生成嵌入
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        embeddings = np.array(embeddings).astype('float32')

        # 加入 FAISS 索引
        self.index.add(embeddings)

        print(f"[GraphRAG] 向量索引建立完成 - 共 {len(chunks)} 個向量")

    def extract_triplets(self, text: str) -> List[Tuple[str, str, str]]:
        """
        使用 LLM 從文本中提取（實體-關係-實體）三元組

        Args:
            text: 輸入文本

        Returns:
            List of (head, relation, tail) tuples
        """
        prompt = f"""Extract knowledge triplets from the following text in Traditional Chinese.

Text: {text}

Output ONLY valid JSON array in this format:
[
  {{"head": "實體1", "relation": "關係", "tail": "實體2"}},
  {{"head": "實體3", "relation": "關係", "tail": "實體4"}}
]

Example:
Text: "卷積神經網路使用卷積層進行特徵提取"
Output: [{{"head": "卷積神經網路", "relation": "使用", "tail": "卷積層"}}, {{"head": "卷積層", "relation": "用於", "tail": "特徵提取"}}]"""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are a knowledge extraction expert. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1024,
            )

            content = response.choices[0].message.content

            # 清理回應
            content = re.sub(r"^.*?assistantfinal", "", content, flags=re.DOTALL)
            content = re.sub(r"```json\s*", "", content)
            content = re.sub(r"```", "", content)
            content = content.strip()

            # 解析 JSON
            triplets_data = json.loads(content)

            triplets = []
            for item in triplets_data:
                triplets.append((item["head"], item["relation"], item["tail"]))

            return triplets

        except Exception as e:
            print(f"[GraphRAG] 三元組提取失敗: {e}")
            return []

    def build_knowledge_graph(self, chunks: List[Dict[str, Any]], sample_rate: float = 0.3):
        """
        從文本塊構建知識圖譜

        Args:
            chunks: 文本塊列表
            sample_rate: 採樣率（避免處理過多文本）
        """
        print("[GraphRAG] 構建知識圖譜...")

        # 採樣（處理部分文本以節省時間）
        import random
        sampled_chunks = random.sample(chunks, min(int(len(chunks) * sample_rate), len(chunks)))

        total_triplets = 0

        for i, chunk in enumerate(sampled_chunks):
            print(f"[GraphRAG] 處理 {i+1}/{len(sampled_chunks)}...", end='\r')

            text = chunk["text"]
            triplets = self.extract_triplets(text)

            # 加入圖譜
            for head, relation, tail in triplets:
                self.knowledge_graph.add_edge(
                    head, tail,
                    relation=relation,
                    source_page=chunk.get("page", "unknown")
                )
                total_triplets += 1

        print(f"\n[GraphRAG] 知識圖譜構建完成")
        print(f"  - 節點數: {self.knowledge_graph.number_of_nodes()}")
        print(f"  - 邊數: {self.knowledge_graph.number_of_edges()}")
        print(f"  - 三元組數: {total_triplets}")

    def vector_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        向量檢索：找到語意最相似的文本塊

        Args:
            query: 查詢字串
            top_k: 返回前 k 個結果

        Returns:
            List of matching chunks with scores
        """
        # 生成查詢嵌入
        query_embedding = self.embedding_model.encode([query])
        query_embedding = np.array(query_embedding).astype('float32')

        # FAISS 搜尋
        distances, indices = self.index.search(query_embedding, top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.chunks):
                results.append({
                    "text": self.chunks[idx]["text"],
                    "page": self.chunks[idx].get("page", "unknown"),
                    "score": float(distances[0][i]),
                    "source": self.chunks[idx].get("source", "unknown")
                })

        return results

    def graph_search(self, entity: str, max_hops: int = 2) -> List[Dict[str, Any]]:
        """
        圖譜檢索：透過關係進行多跳推理

        Args:
            entity: 起始實體
            max_hops: 最大跳數

        Returns:
            List of related entities with paths
        """
        if entity not in self.knowledge_graph:
            return []

        results = []

        # 找出所有可達節點（限制跳數）
        for target in self.knowledge_graph.nodes():
            if target == entity:
                continue

            try:
                # 找最短路徑
                path = nx.shortest_path(self.knowledge_graph, entity, target)

                if len(path) <= max_hops + 1:  # +1 因為包含起點
                    # 提取路徑上的關係
                    relations = []
                    for i in range(len(path) - 1):
                        edge_data = self.knowledge_graph[path[i]][path[i+1]]
                        relations.append(edge_data.get("relation", "related_to"))

                    results.append({
                        "entity": target,
                        "path": path,
                        "relations": relations,
                        "hops": len(path) - 1
                    })
            except nx.NetworkXNoPath:
                continue

        # 按跳數排序
        results.sort(key=lambda x: x["hops"])

        return results[:10]  # 返回前 10 個

    def hybrid_search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        混合檢索：結合向量檢索與圖譜檢索

        Args:
            query: 查詢字串
            top_k: 返回數量

        Returns:
            Combined search results
        """
        print(f"[GraphRAG] 混合檢索: {query}")

        # 1. 向量檢索
        vector_results = self.vector_search(query, top_k=top_k)

        # 2. 提取查詢中的實體（簡化版：取最相似文本中的名詞）
        if vector_results:
            top_text = vector_results[0]["text"]
            # 簡單的實體抽取：找圖譜中存在的詞
            entities_in_query = []
            for node in self.knowledge_graph.nodes():
                if node in query or node in top_text:
                    entities_in_query.append(node)
        else:
            entities_in_query = []

        # 3. 圖譜檢索
        graph_results = []
        for entity in entities_in_query[:3]:  # 最多處理 3 個實體
            related = self.graph_search(entity, max_hops=2)
            graph_results.extend(related)

        return {
            "vector_results": vector_results,
            "graph_results": graph_results[:10],  # 限制數量
            "query": query
        }

    def ingest_pdf(self, pdf_path: str):
        """
        完整流程：解析 PDF → 建立索引 → 構建圖譜

        Args:
            pdf_path: PDF 檔案路徑
        """
        # 1. 解析 PDF
        chunks = self.parse_pdf(pdf_path)

        # 2. 建立向量索引
        self.build_vector_index(chunks)

        # 3. 構建知識圖譜
        self.build_knowledge_graph(chunks, sample_rate=0.3)

        print("[GraphRAG] PDF 處理完成！")


# 測試函數
def test_graphrag():
    """測試 GraphRAG 功能"""
    print("=" * 60)
    print("GraphRAG 測試")
    print("=" * 60)

    # 創建實例
    rag = GraphRAG()

    # 模擬文本塊（如果沒有 PDF）
    test_chunks = [
        {
            "text": "卷積神經網路（CNN）是一種深度學習架構，主要用於影像辨識。CNN 使用卷積層來自動提取影像特徵。",
            "page": 1,
            "source": "test.pdf"
        },
        {
            "text": "反向傳播演算法是訓練神經網路的核心方法。它透過鏈式法則計算梯度，並使用梯度下降更新權重。",
            "page": 2,
            "source": "test.pdf"
        },
        {
            "text": "激活函數如 ReLU、Sigmoid 和 Tanh 為神經網路引入非線性。ReLU 是最常用的激活函數，因為它能緩解梯度消失問題。",
            "page": 3,
            "source": "test.pdf"
        }
    ]

    # 建立向量索引
    rag.build_vector_index(test_chunks)

    # 建立知識圖譜
    rag.build_knowledge_graph(test_chunks, sample_rate=1.0)

    # 測試檢索
    query = "什麼是卷積神經網路？"
    results = rag.hybrid_search(query, top_k=3)

    print("\n查詢結果：")
    print(f"查詢: {query}")
    print("\n向量檢索結果:")
    for i, r in enumerate(results["vector_results"], 1):
        print(f"{i}. [頁{r['page']}] {r['text'][:100]}...")

    print("\n圖譜檢索結果:")
    for i, r in enumerate(results["graph_results"][:5], 1):
        path_str = " -> ".join(r["path"])
        print(f"{i}. {path_str} (跳數: {r['hops']})")


if __name__ == "__main__":
    test_graphrag()
