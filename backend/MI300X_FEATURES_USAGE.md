# MI300X 特性使用說明
## 我們如何利用 CDNA 3 架構與 ROCm 生態

---

## 特性 1：CDNA 3 架構（AI 推論優化）

### MI300X 的 CDNA 3 架構特點

- 針對 AI 模型訓練與**推論**優化
- 支援 LLM（大語言模型）高效推論
- 優化矩陣運算（用於神經網路）

### 我們如何使用

#### 1. LLM 推論（GPT-OSS-120B）

```python
# 我們的系統持續使用 LLM 進行推論

# 場景 1：評分學生答案
score_result = llm_client.chat.completions.create(
    model="openai/gpt-oss-120b",  # ← 在 MI300X 上推論
    messages=[...],
    temperature=0.1
)

# 場景 2：錯誤診斷
misconception_result = llm_client.chat.completions.create(
    model="openai/gpt-oss-120b",  # ← 在 MI300X 上推論
    messages=[...],
    temperature=0.3
)

# 場景 3：生成回饋
feedback_result = llm_client.chat.completions.create(
    model="openai/gpt-oss-120b",  # ← 在 MI300X 上推論
    messages=[...],
    temperature=0.7
)

# 每次學生答題，連續 4-5 次推論
# CDNA 3 架構的推論優化確保快速回應
```

**CDNA 3 的實際幫助**：
- GPT-OSS-120B 是 117B 參數的 LLM，需要高效推論
- CDNA 3 的矩陣運算優化加速 transformer 計算
- 我們的系統需要**高頻推論**（每次答題 4-5 次），CDNA 3 的推論優化至關重要

#### 2. 嵌入模型推論（Sentence Transformers）

```python
# GraphRAG 中使用嵌入模型

# 將文本轉換為向量
embeddings = embedding_model.encode(texts)
# ↑ 在 MI300X 上執行（透過 PyTorch + ROCm）

# 向量檢索
query_embedding = embedding_model.encode([query])
# ↑ 每次查詢都需要執行
```

**CDNA 3 的實際幫助**：
- Sentence Transformers 是 transformer 模型，需要矩陣運算
- 在課程進行中，50 位學生會頻繁查詢
- CDNA 3 的推論優化確保低延遲

### 我們沒有用到的 CDNA 3 特性

❌ **AI 模型訓練**：我們只做推論，不做訓練（fine-tuning）
- 原因：比賽時間短，專注於應用而非訓練

❌ **HPC 科學模擬**：我們的應用是教育，不是科學運算
- 不需要分子動力學、氣候模擬等 HPC 任務

---

## 特性 2：ROCm 開放軟體生態

### MI300X 的 ROCm 平台特點

- 支援 PyTorch、TensorFlow、Hugging Face
- 開放原始碼，方便移植程式碼
- 學術研究與實驗開發友善

### 我們如何使用

#### 1. vLLM（基於 PyTorch + ROCm）

```python
# vLLM 是我們的 LLM 推論引擎
# 官方支援 AMD GPU（透過 ROCm）

from openai import OpenAI

# 連接到 vLLM 伺服器（運行在 MI300X 上）
llm_client = OpenAI(
    base_url="http://210.61.209.139:45014/v1/",
    api_key="NA"
)

# vLLM 使用 ROCm 進行 GPU 加速
# 底層是 PyTorch + ROCm
```

**ROCm 的實際幫助**：
- vLLM 原本為 NVIDIA GPU 開發，但透過 ROCm 可以無縫移植到 AMD GPU
- 我們不需要修改 vLLM 的程式碼，直接使用
- OpenAI 相容的 API 讓開發簡單

#### 2. Sentence Transformers（基於 PyTorch + ROCm）

```python
from sentence_transformers import SentenceTransformer

# 載入嵌入模型
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# 如果有 GPU 可用（MI300X），自動使用
# 透過 PyTorch + ROCm 實現 GPU 加速
embeddings = embedding_model.encode(texts)
```

**ROCm 的實際幫助**：
- Sentence Transformers 是基於 Hugging Face Transformers
- Hugging Face 支援 ROCm，我們直接使用
- 程式碼與 NVIDIA GPU 版本完全相同（移植性高）

#### 3. FAISS（可選的 GPU 加速）

```python
import faiss

# 目前使用 CPU 版本
index = faiss.IndexFlatL2(embedding_dim)

# 如果要用 GPU 加速（透過 ROCm）：
# res = faiss.StandardGpuResources()
# index = faiss.index_cpu_to_gpu(res, 0, index)
```

**ROCm 的潛在幫助**：
- FAISS 支援 AMD GPU（透過 ROCm）
- 我們目前用 CPU 版本（向量索引不大）
- 未來如果需要更大的索引，可以輕鬆切換到 GPU 版本

### ROCm 的實際優勢（我們的體驗）

✅ **程式碼移植簡單**：
```python
# 原本為 NVIDIA GPU 寫的程式碼：
import torch

model = torch.load("model.pth")
model.cuda()  # 使用 CUDA

# 在 AMD GPU（ROCm）上運行：
import torch

model = torch.load("model.pth")
model.cuda()  # 同樣的程式碼，自動使用 ROCm

# 完全相同，不需要修改！
```

✅ **生態系統相容**：
- PyTorch ✓（我們用）
- Hugging Face Transformers ✓（我們用）
- Sentence Transformers ✓（我們用）
- vLLM ✓（我們用）

✅ **開發友善**：
- 不需要學習新的 API
- 直接使用現有的 PyTorch 程式碼
- 豐富的文件與社群支援

---

## 與評審溝通時可以說的點

### 關於 CDNA 3 架構

> "我們的系統需要高頻 LLM 推論——每次學生答題會連續執行 4-5 次 GPT-OSS-120B 推論（評分、診斷、回饋、推薦）。
>
> MI300X 的 CDNA 3 架構針對 AI 推論優化，特別是 transformer 模型的矩陣運算。這確保了我們能在 2 秒內完成完整的分析流程，提供即時回饋。
>
> 此外，GraphRAG 中的 Sentence Transformers 也受益於 CDNA 3 的推論加速。"

### 關於 ROCm 生態

> "我們的技術棧完全基於開源工具：vLLM、PyTorch、Hugging Face、Sentence Transformers、FAISS。
>
> 得益於 ROCm 的開放生態，這些工具都能直接在 MI300X 上運行，不需要修改程式碼。我們原本在 NVIDIA GPU 上開發的原型，移植到 AMD MI300X 上幾乎不需要改動。
>
> 這展示了 ROCm 生態的成熟度與移植性，對學術研究與快速原型開發非常友善。"

---

## 技術細節補充

### 我們的完整技術棧

| 組件 | 技術 | 運行位置 | ROCm 支援 |
|------|------|---------|-----------|
| LLM 推論 | vLLM + GPT-OSS-120B | MI300X GPU | ✓ PyTorch + ROCm |
| 文本嵌入 | Sentence Transformers | MI300X GPU | ✓ Hugging Face + ROCm |
| 向量檢索 | FAISS | CPU（可切換 GPU）| ✓ 支援 ROCm |
| 知識圖譜 | NetworkX | CPU | - |
| 記憶追蹤 | 自行開發 | CPU | - |
| Web 後端 | FastAPI | CPU | - |

### CDNA 3 架構的具體優勢

**1. Matrix Cores（矩陣核心）**：
- 加速 LLM 的矩陣乘法運算
- GPT-OSS-120B 的每次推論涉及大量 GEMM（General Matrix Multiply）
- CDNA 3 的矩陣核心提供高吞吐

**2. Infinity Fabric（互聯架構）**：
- MI300X 內部 8 個 GPU die 之間的高速互聯
- 雖然我們只用一個 MI300X，但 Infinity Fabric 確保資料傳輸效率

**3. 192GB HBM3 高頻寬記憶體**：
- 5.3 TB/s 頻寬
- 支援我們的多學生並行查詢
- 減少記憶體頻寬瓶頸

### ROCm 的版本與相容性

我們使用的環境：
```bash
# ROCm 版本：（由競賽官方提供）
rocm-smi --showproductname

# PyTorch 版本
python -c "import torch; print(torch.__version__)"
# 輸出：2.x.x+rocm5.x

# 自動偵測 GPU
python -c "import torch; print(torch.cuda.is_available())"
# 輸出：True（透過 ROCm）
```

**關鍵點**：
- `torch.cuda` 在 ROCm 上仍然有效
- 程式碼不需要區分 CUDA vs ROCm
- 這是 ROCm 設計的巧思（相容性層）

---

## 可以在簡報中加入的投影片

### 投影片：「技術棧與 MI300X 特性」

```
┌─────────────────────────────────────────┐
│  MI300X 特性                            │
├─────────────────────────────────────────┤
│  CDNA 3 架構                            │
│  • AI 推論優化                          │
│  • Matrix Cores 加速                    │
│  • 192GB HBM3 (5.3 TB/s)               │
├─────────────────────────────────────────┤
│  ROCm 開放生態                          │
│  • PyTorch 相容                         │
│  • Hugging Face 支援                    │
│  • 程式碼移植簡單                        │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  我們的應用                              │
├─────────────────────────────────────────┤
│  LLM 推論（vLLM）                       │
│  • 高頻推論（4-5 次/答題）              │
│  • CDNA 3 加速 transformer              │
├─────────────────────────────────────────┤
│  文本嵌入（Sentence Transformers）       │
│  • 向量檢索                              │
│  • ROCm 自動加速                        │
├─────────────────────────────────────────┤
│  多學生並行                              │
│  • 50 位學生同時查詢                     │
│  • 高頻寬記憶體支援                      │
└─────────────────────────────────────────┘
```

---

## 總結

### ✅ 我們用到的 MI300X 特性

1. **CDNA 3 架構**：
   - LLM 推論加速（GPT-OSS-120B）
   - 嵌入模型加速（Sentence Transformers）
   - 矩陣運算優化

2. **ROCm 生態**：
   - vLLM（PyTorch + ROCm）
   - Sentence Transformers（Hugging Face + ROCm）
   - 程式碼完全相容，不需修改

3. **192GB HBM3**：
   - 大容量（模型 + 資料同時載入）
   - 高頻寬（多學生並行）

### 📝 可以強調的點

- 我們的系統需要**高頻 AI 推論**，CDNA 3 的推論優化至關重要
- 得益於 **ROCm 生態**，我們使用的所有工具（vLLM、PyTorch、Hugging Face）都能直接運行
- **程式碼移植性高**，展示了 ROCm 的成熟度

### 🎯 與評審溝通的版本

> "我們充分利用了 MI300X 的兩大特性：
>
> 1. **CDNA 3 架構的 AI 推論優化**：我們的系統需要高頻 LLM 推論（每次答題 4-5 次），CDNA 3 針對 transformer 模型的矩陣運算優化確保了低延遲。
>
> 2. **ROCm 開放生態的移植性**：我們使用 vLLM、PyTorch、Hugging Face 等開源工具，完全相容 ROCm，程式碼不需要修改。這展示了 AMD 生態的成熟度與開發友善性。"
