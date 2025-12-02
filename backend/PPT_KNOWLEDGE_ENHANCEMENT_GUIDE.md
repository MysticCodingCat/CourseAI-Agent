# PPT 知識增強功能使用指南

## 功能概述

這個新功能可以：

1. **解析 PPT**：提取投影片內容、結構、關鍵詞
2. **預先生成講義大綱**：Markdown 格式，結構清晰
3. **網路搜尋補充**：自動搜尋相關資料
4. **內容過濾**：挑選高品質內容，過濾廣告
5. **加入 RAG**：更新知識庫，支援即時檢索

---

## 完整流程

```
用戶上傳 PPT
  ↓
解析 PPT（python-pptx）
  ↓
預測結構（章節、投影片類型）
  ↓
生成 Markdown 講義大綱
  ↓
識別需要補充的主題
  ↓
網路搜尋（Google）
  ↓
抓取網頁內容（BeautifulSoup）
  ↓
過濾與挑選（ContentFilterAgent）
  ↓
加入 GraphRAG 知識庫
  ↓
生成增強版講義
```

---

## 快速開始

### 安裝依賴

```bash
pip install -r requirements.txt
```

新增的依賴：
- `python-pptx`：解析 PowerPoint
- `beautifulsoup4`：解析 HTML
- `lxml`：BeautifulSoup 的解析器

### 基本使用

```python
from knowledge_enhancement import KnowledgeEnhancementSystem

# 創建系統
system = KnowledgeEnhancementSystem()

# 處理 PPT
result = system.process_ppt(
    ppt_path="lecture.pptx",
    enable_web_enhancement=True,  # 啟用網路增強
    use_api=False  # 使用套件（不用 API key）
)

# 查看結果
print(f"投影片數: {result['slides_count']}")
print(f"章節數: {len(result['structure']['chapters'])}")
print(f"增強主題: {result['topics_enhanced']}")

# 加入 RAG 知識庫
system.add_to_rag(result['enhanced_topics'])

# 生成增強版講義
system.generate_enhanced_markdown(result, "enhanced_lecture.md")
```

### 使用 Google API（可選）

如果希望使用 Google Custom Search API：

```python
system = KnowledgeEnhancementSystem(
    google_api_key="YOUR_GOOGLE_API_KEY",
    google_cx="YOUR_CUSTOM_SEARCH_ENGINE_ID"
)

result = system.process_ppt(
    ppt_path="lecture.pptx",
    enable_web_enhancement=True,
    use_api=True  # 使用 API
)
```

**Google API 申請**：
1. 前往 https://developers.google.com/custom-search/v1/overview
2. 取得 API Key
3. 創建 Custom Search Engine，取得 CX ID

---

## 模組說明

### 1. PPTParser（`ppt_parser.py`）

**功能**：
- 解析 PPT 檔案
- 提取標題、內容、備註、圖片
- 識別投影片類型（標題頁、章節頁、內容頁、總結頁）
- 預測章節結構
- 提取關鍵詞
- 生成 Markdown 大綱

**使用**：

```python
from ppt_parser import PPTParser

parser = PPTParser()

# 解析 PPT
slides_data = parser.parse_ppt("lecture.pptx")

# 預測結構
structure = parser.predict_structure()

# 生成 Markdown 大綱
markdown = parser.generate_outline_markdown()

# 識別需要補充的主題
topics = parser.identify_topics_for_enhancement()
```

**投影片類型識別**：
- `title`：標題頁（課程標題）
- `section`：章節頁（例如："第一章"）
- `content`：內容頁（主要內容）
- `summary`：總結頁（例如："總結"、"回顧"）
- `blank`：空白頁

### 2. WebSearchAgent（`agents/web_search.py`）

**功能**：
- Google 搜尋（支援兩種方式）
  - 套件爬蟲（免費，無需 API key）
  - Google Custom Search API（需要 API key，更穩定）
- 抓取網頁內容
- 清理 HTML，提取主要內容

**使用**：

```python
from agents.web_search import WebSearchAgent

# 創建代理
agent = WebSearchAgent()

# 搜尋
results = agent.search("深度學習 CNN", num_results=5)

# 抓取網頁
content = agent.fetch_webpage_content(results[0]["url"])

# 搜尋並抓取（一步完成）
contents = agent.search_and_fetch("卷積神經網路 教學", num_results=3)
```

**跳過的網站**：
- 社交媒體（YouTube、Facebook、Twitter 等）
- PDF 檔案（需要特殊處理）

### 3. ContentFilterAgent（`agents/web_search.py`）

**功能**：
- 分析網頁內容品質
- 計算段落與關鍵詞的相關性
- 過濾廣告、無關內容
- 選擇最佳內容

**使用**：

```python
from agents.web_search import ContentFilterAgent

filter_agent = ContentFilterAgent()

# 過濾內容
filtered = filter_agent.filter_content(
    content=webpage_content,
    target_keyword="卷積神經網路"
)

# 選擇最佳內容
best_contents = filter_agent.select_best_content(
    filtered_contents=[filtered1, filtered2, filtered3],
    top_k=2
)
```

**過濾規則**：
- 長度檢查（50-1000 字）
- 過濾廣告詞（點擊、購買、優惠等）
- 過濾過多連結的段落
- 過濾特殊字符過多的段落

### 4. KnowledgeEnhancementSystem（`knowledge_enhancement.py`）

**功能**：
- 整合所有模組
- 完整的 PPT 處理流程
- 生成增強版 Markdown 講義

**使用**：見「快速開始」

---

## 生成的 Markdown 格式

### 初步大綱（`_outline.md`）

```markdown
# 深度學習基礎

---

## 第一章：卷積神經網路

### 什麼是 CNN？
*投影片 5*

**重點：**
- CNN 是用於處理影像的深度學習架構
- 使用卷積層自動提取特徵

**關鍵詞：** CNN, 卷積層, 特徵提取

**講義補充：**
*（此區域將在課程進行時自動填充）*

---
```

### 增強版講義（`enhanced_lecture.md`）

```markdown
# 深度學習基礎
*由 CourseAI 自動生成*

---

## 第一章：卷積神經網路

### 什麼是 CNN？
*投影片 5*

**投影片內容：**
- CNN 是用於處理影像的深度學習架構
- 使用卷積層自動提取特徵

**關鍵詞：** CNN, 卷積層, 特徵提取

#### 補充資料：CNN

**來源：** [深度學習教學 - 卷積神經網路詳解](https://example.com/cnn-tutorial)

卷積神經網路（CNN）是一種專門設計用於處理網格狀數據的深度學習架構。相較於傳統的全連接神經網路，CNN 的主要優勢在於能夠自動學習和提取影像的空間特徵。

CNN 的核心組件是卷積層，它使用可學習的濾波器（filter）在輸入影像上滑動，檢測局部特徵如邊緣、紋理和形狀。這種設計靈感來自生物視覺系統中的感受野概念。

---
```

---

## 常見問題

### Q1: 需要 Google API key 嗎？

**A**: 不一定。系統支援兩種模式：

1. **套件爬蟲模式**（預設）：
   - 不需要 API key
   - 免費
   - 可能會被 Google 偵測（加入延遲可避免）

2. **API 模式**：
   - 需要 API key
   - 更穩定
   - 有免費額度（每天 100 次查詢）

### Q2: 哪些內容會被過濾？

**A**: ContentFilterAgent 會過濾：
- 廣告段落（包含"點擊"、"購買"、"優惠"等）
- 過短的段落（<50 字）
- 過長的段落（>1000 字）
- 過多連結的段落
- 特殊字符過多的段落

### Q3: 支援哪些網站？

**A**: 支援大部分教育、技術網站：
- 維基百科
- 技術部落格
- 教育網站
- 學術網站

**不支援**：
- 社交媒體（YouTube、Facebook 等）
- PDF 檔案（需要特殊處理）

### Q4: 如何提高搜尋品質？

**A**: 幾個技巧：

1. **關鍵詞優化**：
   ```python
   # 不好
   agent.search("CNN")

   # 好
   agent.search("CNN 卷積神經網路 教學")
   ```

2. **增加結果數**：
   ```python
   results = agent.search_and_fetch(query, num_results=5)  # 多抓一些，過濾後留下最好的
   ```

3. **使用 API**（更穩定）：
   ```python
   system = KnowledgeEnhancementSystem(
       google_api_key="YOUR_KEY",
       google_cx="YOUR_CX"
   )
   result = system.process_ppt("lecture.pptx", use_api=True)
   ```

### Q5: 可以處理多大的 PPT？

**A**: 沒有嚴格限制，但建議：
- 投影片數：< 100 張
- 網路增強主題：< 20 個（系統會自動限制）

過多的主題會導致：
- 搜尋時間過長
- RAG 索引過大

### Q6: 生成的講義可以修改嗎？

**A**: 可以！生成的是標準 Markdown 檔案，可以用任何文字編輯器修改：
- VS Code
- Typora
- Obsidian
- 記事本

---

## 技術細節

### PPT 解析

使用 `python-pptx` 庫：

```python
from pptx import Presentation

prs = Presentation("lecture.pptx")

for slide in prs.slides:
    # 提取標題
    title = slide.shapes.title.text if slide.shapes.title else ""

    # 提取內容
    for shape in slide.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text
```

### 網頁抓取

使用 `requests` + `BeautifulSoup`：

```python
import requests
from bs4 import BeautifulSoup

response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# 移除不需要的元素
for element in soup(['script', 'style', 'nav', 'footer']):
    element.decompose()

# 提取段落
paragraphs = [p.get_text() for p in soup.find_all('p')]
```

### RAG 整合

將抓取的內容加入 GraphRAG：

```python
chunks = []

for content in enhanced_contents:
    for para in content['paragraphs']:
        chunks.append({
            "text": para,
            "source": content['url'],
            "keyword": keyword
        })

# 建立索引
rag_engine.build_vector_index(chunks)
rag_engine.build_knowledge_graph(chunks)
```

---

## 未來改進

### 短期

- [x] PPT 解析
- [x] 網路搜尋
- [x] 內容過濾
- [x] RAG 整合
- [ ] 圖片搜尋與下載
- [ ] 更智慧的關鍵詞提取（使用 LLM）
- [ ] 網頁內容的 LLM 摘要

### 長期

- [ ] 支援 PDF 檔案的網路搜尋
- [ ] 多語言支援（英文、日文等）
- [ ] 概念圖自動生成
- [ ] 影片內容搜尋與整合

---

## 示例輸出

見 `examples/` 目錄：
- `example_outline.md`：初步大綱
- `example_enhanced.md`：增強版講義
- `example_ppt_data.json`：解析結果

---

## 故障排除

### 問題：搜尋失敗

**可能原因**：
1. 網路問題
2. Google 偵測為機器人

**解決方法**：
- 增加延遲：`time.sleep(2)`
- 使用 API 模式
- 檢查網路連線

### 問題：抓取網頁失敗

**可能原因**：
1. 網站需要登入
2. 網站有反爬蟲機制
3. 網站結構特殊

**解決方法**：
- 跳過該網站
- 增加 User-Agent
- 手動補充內容

### 問題：過濾後沒有內容

**可能原因**：
1. 網頁品質差
2. 過濾規則太嚴格

**解決方法**：
- 調整 `_check_quality` 的規則
- 降低相關性閾值
- 增加搜尋結果數量

---

## 總結

這個功能讓 CourseAI 可以：

1. ✅ 自動解析 PPT，提取結構
2. ✅ 預先生成講義大綱（Markdown）
3. ✅ 自動搜尋並補充相關資料
4. ✅ 過濾高品質內容
5. ✅ 整合到 RAG 知識庫

**下一步**：
- 整合到主系統（FastAPI）
- 前端上傳介面
- 即時進度顯示
