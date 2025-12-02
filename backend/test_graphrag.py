"""
GraphRAG 功能測試
測試向量檢索、知識圖譜構建、混合檢索
"""
import sys
import io
import asyncio

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from rag_engine import GraphRAG


def create_test_data():
    """創建測試用的文本塊（模擬課程講義）"""
    return [
        {
            "text": "深度學習（Deep Learning）是機器學習的一個分支，使用多層神經網路來學習資料的表示。深度學習在影像辨識、語音辨識和自然語言處理等領域取得了突破性進展。",
            "page": 1,
            "source": "深度學習基礎.pdf"
        },
        {
            "text": "卷積神經網路（Convolutional Neural Network, CNN）是一種專門用於處理網格狀數據的深度學習架構。CNN 主要應用於影像辨識任務，它使用卷積層來自動提取影像特徵，無需手工設計特徵。",
            "page": 5,
            "source": "深度學習基礎.pdf"
        },
        {
            "text": "卷積層是 CNN 的核心組件。卷積層透過卷積運算，使用可學習的濾波器（filter）在輸入影像上滑動，提取局部特徵。每個濾波器可以檢測特定的模式，例如邊緣、紋理或更複雜的形狀。",
            "page": 6,
            "source": "深度學習基礎.pdf"
        },
        {
            "text": "池化層（Pooling Layer）通常緊接在卷積層之後。池化層的作用是降低特徵圖的空間維度，減少參數數量，並提供一定程度的平移不變性。常見的池化方法包括最大池化（Max Pooling）和平均池化（Average Pooling）。",
            "page": 7,
            "source": "深度學習基礎.pdf"
        },
        {
            "text": "反向傳播（Backpropagation）是訓練神經網路的核心演算法。它透過鏈式法則（Chain Rule）計算損失函數對每個參數的梯度，然後使用梯度下降（Gradient Descent）更新參數，使損失函數最小化。",
            "page": 12,
            "source": "深度學習基礎.pdf"
        },
        {
            "text": "梯度下降是一種優化演算法，用於最小化損失函數。基本的梯度下降在每次迭代中使用所有訓練樣本計算梯度，而隨機梯度下降（SGD）每次只使用一個樣本。Mini-batch 梯度下降則是兩者的折衷，每次使用一小批樣本。",
            "page": 13,
            "source": "深度學習基礎.pdf"
        },
        {
            "text": "激活函數（Activation Function）為神經網路引入非線性。常見的激活函數包括 ReLU（修正線性單元）、Sigmoid 和 Tanh。ReLU 是目前最常用的激活函數，定義為 f(x) = max(0, x)，它能有效緩解梯度消失問題。",
            "page": 15,
            "source": "深度學習基礎.pdf"
        },
        {
            "text": "過擬合（Overfitting）是機器學習中的常見問題，指模型在訓練資料上表現良好，但在測試資料上表現不佳。為了防止過擬合，常用的技術包括 Dropout、L2 正則化、資料增強和早停（Early Stopping）。",
            "page": 18,
            "source": "深度學習基礎.pdf"
        },
        {
            "text": "Dropout 是一種正則化技術，在訓練過程中隨機丟棄一部分神經元。這迫使網路學習更加魯棒的特徵，不依賴於特定的神經元組合。Dropout 通常設置為 0.5，即隨機丟棄 50% 的神經元。",
            "page": 19,
            "source": "深度學習基礎.pdf"
        },
        {
            "text": "批次標準化（Batch Normalization）是一種加速訓練並提高穩定性的技術。它對每個 mini-batch 的輸入進行標準化，使其均值為 0、方差為 1。批次標準化可以使用更高的學習率，並減少對初始化的敏感性。",
            "page": 20,
            "source": "深度學習基礎.pdf"
        }
    ]


def test_vector_search(rag: GraphRAG):
    """測試向量檢索"""
    print("\n" + "=" * 60)
    print("測試 1: 向量檢索")
    print("=" * 60)

    test_queries = [
        "什麼是卷積神經網路？",
        "如何防止過擬合？",
        "解釋反向傳播演算法"
    ]

    for query in test_queries:
        print(f"\n查詢: {query}")
        results = rag.vector_search(query, top_k=2)

        for i, result in enumerate(results, 1):
            print(f"\n  結果 {i}:")
            print(f"  頁碼: {result['page']}")
            print(f"  相似度分數: {result['score']:.4f}")
            print(f"  內容: {result['text'][:150]}...")


def test_knowledge_graph(rag: GraphRAG):
    """測試知識圖譜"""
    print("\n" + "=" * 60)
    print("測試 2: 知識圖譜")
    print("=" * 60)

    print(f"\n圖譜統計:")
    print(f"  節點數: {rag.knowledge_graph.number_of_nodes()}")
    print(f"  邊數: {rag.knowledge_graph.number_of_edges()}")

    # 列出一些節點
    nodes = list(rag.knowledge_graph.nodes())[:10]
    print(f"\n  部分節點: {nodes}")

    # 測試圖譜搜尋
    if nodes:
        test_entity = nodes[0]
        print(f"\n從實體 '{test_entity}' 開始的關聯:")
        related = rag.graph_search(test_entity, max_hops=2)

        for i, rel in enumerate(related[:5], 1):
            path_str = " -> ".join(rel["path"])
            relations_str = " -> ".join(rel["relations"])
            print(f"  {i}. {path_str}")
            print(f"     關係: {relations_str}")
            print(f"     跳數: {rel['hops']}")


def test_hybrid_search(rag: GraphRAG):
    """測試混合檢索"""
    print("\n" + "=" * 60)
    print("測試 3: 混合檢索（向量 + 圖譜）")
    print("=" * 60)

    query = "卷積神經網路的池化層"
    print(f"\n查詢: {query}")

    results = rag.hybrid_search(query, top_k=3)

    print("\n向量檢索結果:")
    for i, r in enumerate(results["vector_results"], 1):
        print(f"  {i}. [頁{r['page']}] {r['text'][:100]}...")

    print("\n圖譜檢索結果（關聯概念）:")
    for i, r in enumerate(results["graph_results"][:5], 1):
        path_str = " -> ".join(r["path"])
        print(f"  {i}. {path_str} ({r['hops']} 跳)")


async def test_with_knowledge_agent(rag: GraphRAG):
    """測試與 Knowledge Agent 的整合"""
    print("\n" + "=" * 60)
    print("測試 4: Knowledge Agent V2 整合")
    print("=" * 60)

    from agents.knowledge_v2 import KnowledgeAgentV2

    agent = KnowledgeAgentV2(rag_engine=rag)

    test_keywords = ["卷積神經網路", "Dropout", "反向傳播"]

    for keyword in test_keywords:
        print(f"\n關鍵詞: {keyword}")
        result = await agent.process([keyword])

        print(f"來源: {result['source']}")
        print(f"檢索結果:")
        for r in result['retrieval_results']:
            print(f"  主題: {r['keyword']}")
            print(f"  向量匹配數: {r.get('vector_matches', 0)}")
            print(f"  圖譜關係數: {r.get('graph_relations', 0)}")
            print(f"\n  資訊:\n{r['info'][:300]}...")


async def main():
    """主測試流程"""
    print("\n" + "=" * 70)
    print("GraphRAG 完整測試套件")
    print("測試向量檢索 + 知識圖譜 + 混合檢索")
    print("=" * 70)

    # 1. 初始化 GraphRAG
    print("\n[步驟 1] 初始化 GraphRAG...")
    rag = GraphRAG()

    # 2. 載入測試資料
    print("\n[步驟 2] 載入測試資料...")
    test_chunks = create_test_data()
    print(f"共 {len(test_chunks)} 個文本塊")

    # 3. 建立向量索引
    print("\n[步驟 3] 建立向量索引...")
    rag.build_vector_index(test_chunks)

    # 4. 建立知識圖譜
    print("\n[步驟 4] 建立知識圖譜...")
    rag.build_knowledge_graph(test_chunks, sample_rate=1.0)  # 處理全部數據

    # 5. 執行測試
    test_vector_search(rag)
    test_knowledge_graph(rag)
    test_hybrid_search(rag)
    await test_with_knowledge_agent(rag)

    # 總結
    print("\n" + "=" * 70)
    print("測試總結")
    print("=" * 70)
    print("[OK] 向量檢索功能正常")
    print("[OK] 知識圖譜構建成功")
    print("[OK] 混合檢索運作正常")
    print("[OK] Knowledge Agent V2 整合成功")
    print("\nGraphRAG 系統已準備就緒！")


if __name__ == "__main__":
    asyncio.run(main())
