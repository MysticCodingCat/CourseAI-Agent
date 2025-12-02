# GPT-OSS-120B vs 旗艦商業模型對比

**比較對象**：Gemini 2.5 Pro（2025年3月發布）

---

## 規格對比表

| 項目 | GPT-OSS-120B | Gemini 2.5 Pro |
|------|-------------|----------------|
| **Context Window** | 128K tokens | 1M tokens（計劃2M） |
| **參數量** | 117B（5.1B active） | 未公開（預估>1T） |
| **多模態** | 僅文字 | 文字+圖片+音訊+影片 |
| **工具使用** | 需透過prompt模擬 | 原生支援（code execution, search） |
| **API成本** | $0（本地部署） | $4 input / $20 output per M tokens |
| **推理速度** | 0.75-1.5秒 | 類似（雲端延遲） |
| **繁體中文** | 支援良好 | 支援優秀 |
| **授權** | Apache 2.0（開源） | 商業閉源 |
| **部署方式** | 本地/自建 | 雲端API only |

---

## 實際成本分析

### 場景：學生使用2小時課程

**假設**：
- 課程逐字稿：30K tokens
- 講義PDF：20K tokens
- 即時分析請求：100次
- 生成筆記：1次（輸出5K tokens）

**使用 Gemini 2.5 Pro**：
```
Input: (30K + 20K) × 100 次 = 5M tokens
Output: 5K tokens

成本 = (5M × $4/M) + (5K × $20/M)
     = $20 + $0.1
     = $20.1 / 2小時課程
```

**使用 GPT-OSS-120B**：
```
成本 = $0
```

**結論**：
- 單次使用差異不大（$20）
- 但如果是：
  - 100個學生 → Gemini: $2,010 vs GPT-OSS: $0
  - 一學期（16週） → Gemini: $321 vs GPT-OSS: $0

---

## 性能對比（推理能力）

### Gemini 2.5 Pro 的優勢

1. **更強的推理能力**
   - 複雜問題分解
   - 多步驟邏輯推理
   - 數學證明

2. **超長上下文（1M tokens）**
   - 可以處理整本教科書（GPT-OSS只能處理1章）
   - 更好的全局理解

3. **原生多模態**
   - 可以直接理解圖片、音訊
   - 不需要額外的圖片描述步驟

4. **工具使用**
   - 可以執行代碼
   - 可以搜尋網路
   - 可以呼叫API

### GPT-OSS-120B 的優勢

1. **零成本**
   - 適合大規模部署
   - 無API限制

2. **隱私保護**
   - 資料不離開本地
   - 符合教育資料法規

3. **可控性**
   - 可以微調（fine-tune）
   - 可以調整參數
   - 不受API變動影響

4. **展示AMD硬體**
   - 比賽要求使用AMD平台
   - 展示MI300X的能力

---

## 針對您的比賽：應該選哪個？

### 建議：混合策略

**主力使用 GPT-OSS-120B**（展示重點）：
- 所有核心功能都用GPT-OSS-120B
- 強調：
  - 零成本
  - 本地部署
  - AMD MI300X優化
  - 開源優勢

**Gemini 作為對比/備用**（可選）：
```python
# 在簡報中展示對比
"我們的系統使用開源的GPT-OSS-120B，
相比商業API（如Gemini 2.5 Pro），
在教育場景中具有明顯優勢：
- 成本：$0 vs $20/課程
- 隱私：本地 vs 雲端
- 可控：開源 vs 黑盒"
```

---

## 實際測試結果（我們的觀察）

### GPT-OSS-120B 的表現

**優點**：
- 繁體中文品質好
- NoteTaker生成的講義結構清晰
- 速度快（0.75-1.5秒）
- JSON格式需要調整prompt，但可用

**缺點**：
- 有時會輸出怪異內容（驚嘆號問題）
- 對prompt格式敏感
- 推理深度不如旗艦模型

### Gemini 2.5 Flash 的表現（我們之前用的）

**優點**：
- prompt容忍度高
- JSON格式穩定
- 繁體中文優秀

**缺點**：
- 需要付費API key
- 有rate limit
- 不符合比賽「使用AMD平台」的精神

---

## 最終建議

### 對於比賽（AMD AI Agent Hackathon）

**必須用 GPT-OSS-120B**：
- 比賽主題是「AMD Instinct MI300X」
- 評審期待看到開源模型的應用
- 展示本地部署的優勢

**評審會看的點**：
1. 是否真的用到AMD提供的120B模型
2. 是否發揮了MI300X的硬體優勢
3. 技術創新（GraphRAG、多Agent協作）
4. 實際應用價值

### 對於實際產品

**如果要商業化**，可以考慮：
- 提供兩種方案：
  - 免費版：GPT-OSS-120B
  - 進階版：Gemini 2.5 Pro（付費功能）

---

## 結論

### GPT-OSS-120B 相比 Gemini 2.5 Pro：

**推理能力**：略遜（但對教育場景夠用）
**上下文長度**：劣勢（128K vs 1M）
**成本**：絕對優勢（$0 vs $20+/課程）
**隱私**：絕對優勢（本地 vs 雲端）
**比賽適配**：完美（符合AMD主題）

### 對您的建議：

**堅持使用 GPT-OSS-120B**，因為：
1. 符合比賽主題（AMD平台）
2. 成本優勢明顯（可規模化）
3. 隱私保護（教育場景重要）
4. 實測表現可接受（特別是NoteTaker）

**如果評審問「為何不用更強的商業模型」**，回答：
> "我們的目標是打造一個可規模化、成本可控的教育工具。
> GPT-OSS-120B在AMD MI300X上的表現已經能滿足教育需求，
> 且零成本意味著可以讓更多學生免費使用，
> 這才是教育科技的真正價值。"

---

## 參考資料

- [Gemini 2.5 Pro Benchmarks & Pricing](https://futureagi.com/blogs/gemini-2-5-pro-2025)
- [Google Gemini Cost Guide 2025](https://www.cloudzero.com/blog/gemini-pricing/)
- [GPT-OSS-120B Specifications](https://platform.openai.com/docs/models/gpt-oss-120b)
- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
