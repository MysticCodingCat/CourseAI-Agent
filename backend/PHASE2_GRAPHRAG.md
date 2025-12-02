# Phase 2: GraphRAG 實作說明

**開始日期**：2025-12-03
**狀態**：進行中

---

## GraphRAG 是什麼？

GraphRAG (Graph-based Retrieval Augmented Generation) 是一種進階的 RAG 技術，結合了：

1. **向量檢索**：找到語意相似的文本段落（傳統 RAG）
2. **知識圖譜**：透過實體關係進行多跳推理（創新功能）

### 為什麼需要 GraphRAG？

**傳統 RAG 的局限**：
```
查詢："什麼是dropout？"
→ 只會找到包含 "dropout" 的段落
→ 無法自動補充相關概念（如"過擬合"、"正則化"）
```

**GraphRAG 的優勢**：
```
查詢："什麼是dropout？"
→ 向量檢索：找到 dropout 的定義
→ 圖譜檢索：自動找到相關概念
   - Dropout → 用於防止 → 過擬合
   - Dropout → 是一種 → 正則化技術
   - 正則化技術 → 還包含 → L2正則化、早停
```

---

## 已完成的實作

### 1. 核心引擎 (`rag_engine.py`)

**主要類別**：`GraphRAG`

**核心功能**：

#### A. PDF 解析
```python
def parse_pdf(pdf_path) -> List[Dict]:
    # 使用 PyMuPDF 提取文本
    # 按段落切分
    # 保留頁碼元數據
```

#### B. 向量索引構建
```python
def build_vector_index(chunks):
    # 使用 Sentence Transformers 生成嵌入
    # 使用 FAISS 建立向量索引
    # 支援高效相似度搜尋
```

#### C. 知識圖譜構建
```python
def build_knowledge_graph(chunks):
    # 使用 GPT-OSS-120B 提取三元組
    # (實體1, 關係, 實體2)
    # 使用 NetworkX 構建圖譜
```

**三元組提取範例**：
```
輸入: "卷積神經網路使用卷積層進行特徵提取"
輸出: [
  {head: "卷積神經網路", relation: "使用", tail: "卷積層"},
  {head: "卷積層", relation: "用於", tail: "特徵提取"}
]
```

#### D. 混合檢索
```python
def hybrid_search(query, top_k=5):
    # 1. 向量檢索 → 找相似段落
    # 2. 提取實體
    # 3. 圖譜檢索 → 找關聯概念（多跳推理）
    # 4. 整合結果
```

---

### 2. Knowledge Agent V2 (`agents/knowledge_v2.py`)

**功能**：
- 整合 GraphRAG 引擎
- 接收關鍵詞查詢
- 返回結構化知識（包含向量匹配 + 圖譜關係）

**使用方式**：
```python
agent = KnowledgeAgentV2(rag_engine=rag)
result = await agent.process(["反向傳播"])

# 返回：
{
  "source": "課程講義（共3個相關段落）",
  "retrieval_results": [{
    "keyword": "反向傳播",
    "info": "定義+講義出處+關鍵要點...",
    "vector_matches": 3,
    "graph_relations": 5
  }]
}
```

---

## 技術棧

| 組件 | 技術 | 用途 |
|------|------|------|
| PDF解析 | PyMuPDF | 提取文本與元數據 |
| 文本嵌入 | Sentence Transformers | 生成向量表示 |
| 向量檢索 | FAISS | 高效相似度搜尋 |
| 三元組提取 | GPT-OSS-120B | LLM提取實體關係 |
| 知識圖譜 | NetworkX | 圖結構與路徑搜尋 |

---

## 當前進度

- [x] `rag_engine.py` - 核心引擎完成
- [x] `knowledge_v2.py` - Agent整合完成
- [x] `test_graphrag.py` - 測試腳本完成
- [ ] 依賴安裝與模型下載（進行中）
- [ ] 完整測試驗證
- [ ] 與主系統整合

---

## 測試計畫

### 測試資料
使用模擬的課程講義文本（深度學習主題）：
- 10個文本塊
- 涵蓋：CNN、反向傳播、激活函數、過擬合等概念

### 測試項目
1. **向量檢索測試**
   - 查詢："什麼是卷積神經網路？"
   - 預期：返回相關段落+頁碼

2. **知識圖譜測試**
   - 檢查節點數、邊數
   - 測試多跳推理

3. **混合檢索測試**
   - 結合向量+圖譜
   - 驗證關聯概念發現

4. **Knowledge Agent 整合測試**
   - 透過 Agent 查詢
   - 驗證繁體中文輸出品質

---

## 與舊版 Knowledge Agent 的差異

### 舊版（knowledge.py）
```python
# 模擬檢索
async def process(keywords):
    return {"info": "模擬的知識內容"}
```

### 新版（knowledge_v2.py）
```python
# 真實檢索
async def process(keywords):
    # 1. 向量檢索
    vector_results = rag.vector_search(keyword)

    # 2. 圖譜檢索
    graph_results = rag.graph_search(entity)

    # 3. LLM 整合
    integrated_info = llm.process(vector + graph)

    return {"info": integrated_info}
```

---

## 後續計畫

### Phase 2 剩餘任務
1. 完成測試驗證
2. 效能優化（採樣率調整、快取機制）
3. API 端點整合（`/upload_pdf`, `/search`）

### Phase 3 預告（PPT 解析器）
- 解析 PowerPoint 檔案
- 提取章節結構
- 與 RAG 整合

---

## Demo 亮點

當展示 GraphRAG 時，重點強調：

1. **技術創新**：
   > "一般的 RAG 只能找到『匹配的段落』，但 CourseAI 的 GraphRAG 能理解『概念之間的關聯』。"

2. **實際效果**：
   > "當老師提到『梯度消失』時，AI 不只回答定義，還會主動補充『可以用 ReLU 激活函數緩解』，即使老師沒說，因為圖譜知道它們有關聯。"

3. **AMD 優勢**：
   > "GPT-OSS-120B 在 AMD Instinct MI300X 上運行，大記憶體讓我們能同時處理向量檢索與圖譜推理，無需擔心 OOM。"

---

## 常見問題

**Q: 為什麼不直接用 LangChain 的 Graph RAG？**
A: 我們針對教育場景客製化，使用繁體中文優化的 prompt，並整合 GPT-OSS-120B。

**Q: 建立圖譜會不會很慢？**
A: 我們使用採樣機制（sample_rate），只處理 30% 的文本，在速度與品質間取得平衡。

**Q: 如果沒有 PDF 怎麼辦？**
A: Knowledge Agent V2 會優雅降級，提示使用者上傳講義，同時使用 LLM 的內建知識回答。

---

## 參考資料

- [Microsoft GraphRAG Paper](https://www.microsoft.com/en-us/research/publication/from-local-to-global/)
- [NetworkX Documentation](https://networkx.org/)
- [FAISS Documentation](https://faiss.ai/)
- [Sentence Transformers](https://www.sbert.net/)
