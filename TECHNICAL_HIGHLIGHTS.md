# CourseAI Technical Highlights & Innovations
> "Cool Tech" features to distinguish CourseAI from standard wrappers.

## 1. GraphRAG (Dynamic Knowledge Graph Retrieval) 🕸️
**現狀問題：**
一般的 RAG (檢索增強生成) 只是把文字切塊 (Chunking) 然後比對相似度。缺點是它不懂「概念之間的關聯」。例如查「變形金剛」，傳統 RAG 找不到「柯博文」，因為這兩個詞向量不一定最近，但它們在知識圖譜上是父子節點。

**我們的創新 (The Cool Tech)：**
我們不只建立向量索引，還**即時構建知識圖譜 (Knowledge Graph)**。
*   **技術實作：** 當 PDF 上傳時，使用 LLM 提取 `(Entity) -> [Relation] -> (Entity)` 的三元組。
*   **檢索邏輯：** 當 Agent 聽到 "Backpropagation" 時，它不僅檢索該段落，還會沿著圖譜找到前置概念 "Chain Rule" (連鎖律)，即使老師沒提到連鎖律，Agent 也能主動補充：「這需要用到微積分的連鎖律喔！」
*   **Buzzword:** `GraphRAG`, `Knowledge Graph Construction`, `Multi-hop Reasoning`.

## 2. Multimodal Late Fusion (視聽覺延遲融合) 👁️👂
**現狀問題：**
現在的語音筆記軟體都由「聽」的。但老師上課常常說：「請看這張圖...」、「這個公式...」，AI 根本不知道在指哪裡。

**我們的創新 (The Cool Tech)：**
Agent 具備 **「視覺感知」**。
*   **技術實作：**
    1.  Chrome Extension 每 5 秒擷取一次 Meet 畫面的截圖 (Snapshot)。
    2.  後端使用 VLM (Vision-Language Model, 如 LLaVA 或 Gemini Vision) 分析投影片內容，提取文字與圖表描述。
    3.  **Late Fusion (晚期融合)：** 將「語音的 Embedding」與「畫面的 Embedding」結合。
*   **效果：** 老師說：「如圖所示」，Agent 的筆記會自動插入那張投影片的截圖，並標註：「老師正在講解 Slide 第 12 頁的架構圖」。
*   **Buzzword:** `Multimodal RAG`, `Visual Grounding`, `Late Fusion Strategy`.

## 3. Speculative Decoding with Small Model (投機取樣加速) ⚡
**現狀問題：**
使用 120B 這種超大模型，推理速度通常很慢，跟不上老師說話的速度，導致字幕延遲。

**我們的創新 (The Cool Tech)：**
利用 AMD MI300X 的特性，同時跑一個 **小模型 (7B)** 和一個 **大模型 (120B)**。
*   **技術實作：**
    *   **Drafting:** 小模型快速猜測接下來的幾個字 (速度極快)。
    *   **Verification:** 大模型平行驗證這些字對不對。如果不對就修正，對了就直接用。
*   **效果：** 讓 120B 模型的輸出速度提升 2-3 倍，達到即時對話的流暢度。
*   **為什麼適合 AMD：** MI300X 有超大記憶體，可以輕鬆把這兩個模型都塞進同一張卡裡，減少傳輸延遲。
*   **Buzzword:** `Speculative Decoding`, `Model Distillation`, `Low-Latency Inference`.

---

### 推薦實作優先級
1.  **GraphRAG:** 這是目前 AI 界的顯學 (Microsoft 最近才發布論文)，實作出來非常有學術價值。
2.  **Multimodal:** 視覺效果最強，Demo 最容易看懂。
3.  **Speculative Decoding:** 純效能優化，如果評審很在意延遲 (Latency) 再強調。
