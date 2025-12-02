# CourseAI Agent 測試指南

## 🎯 Phase 1: 切換至 GPT-OSS-120B

已完成的修改：
- ✅ `agents/base.py` - 切換至 GPT-OSS-120B（Gemini已註解）
- ✅ `.env` - 環境變數配置
- ✅ `requirements.txt` - 依賴套件更新
- ✅ 測試腳本建立

---

## 📋 測試步驟

### Step 1: 安裝依賴

```powershell
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: 快速連接測試

這個測試會驗證 GPT-OSS-120B 的基本連接：

```powershell
python test_gpt_oss_connection.py
```

**預期輸出**：
```
====================================================
GPT-OSS-120B 連接測試
AMD Instinct MI300X Platform
====================================================

[Step 1] 正在獲取可用模型...
✓ 找到模型: openai/gpt-oss-120b

[Step 2] 初始化 OpenAI 客戶端...
✓ 客戶端初始化成功

[Step 3] 測試 Chat Completion API...
✓ API 呼叫成功！
  回應時間: X.XX 秒
  回應內容:
  --------------------------------------------------------
  神經網路是一種模仿人腦神經元結構的計算模型...
  --------------------------------------------------------

[Step 4] 測試 JSON 格式輸出...
✓ API 呼叫成功
✓ JSON 解析成功！
```

### Step 3: 完整 Agent 測試

這個測試會運行所有四個 Agent（Listener、Knowledge、Tutor、NoteTaker）：

```powershell
python test_agents_gpt_oss.py
```

**測試項目**：
1. **Listener Agent** - 識別教育內容 vs 雜訊
2. **Knowledge Agent** - RAG 知識檢索（目前模擬）
3. **Tutor Agent** - 蘇格拉底式提問生成
4. **NoteTaker Agent** - 講義生成
5. **完整流水線** - 端到端測試

---

## 🔧 常見問題排查

### 問題 1: 連接超時
```
Error: Connection timeout
```
**解決方案**：
- 確認 AMD GPU 伺服器是否在線
- 檢查 `.env` 中的 `VLLM_BASE_URL` 是否正確
- 測試網路連接：`curl http://210.61.209.139:45014/v1/models`

### 問題 2: JSON 解析失敗
```
⚠ JSON 解析失敗: Expecting value
```
**解決方案**：
- GPT-OSS-120B 可能對 JSON prompt 格式敏感
- 需要調整 `agents/prompts.py` 中的 prompt
- 嘗試降低 temperature（例如從 0.7 → 0.3）

### 問題 3: 繁體中文輸出亂碼
```
回應：ç¥\x9e經網路...
```
**解決方案**：
- 在 prompt 中明確指定：`Output in Traditional Chinese (繁體中文 - Taiwan)`
- 檢查終端機編碼：`chcp 65001` (Windows)

### 問題 4: 回應速度慢
```
回應時間: 30+ 秒
```
**可能原因**：
- 120B 模型很大，推理需要時間
- 伺服器負載高

**優化方案**（Phase 2 再做）：
- 調整 `max_tokens`（從 2048 → 512）
- 實作 streaming 模式
- 考慮使用 Speculative Decoding

---

## 📊 測試結果記錄

### 日期: ___________

| 測試項目 | 狀態 | 回應時間 | 備註 |
|---------|------|---------|------|
| 基本連接 | ⬜ PASS / ⬜ FAIL | ___秒 | |
| Listener Agent | ⬜ PASS / ⬜ FAIL | ___秒 | |
| Knowledge Agent | ⬜ PASS / ⬜ FAIL | ___秒 | |
| Tutor Agent | ⬜ PASS / ⬜ FAIL | ___秒 | |
| NoteTaker Agent | ⬜ PASS / ⬜ FAIL | ___秒 | |
| 完整流水線 | ⬜ PASS / ⬜ FAIL | ___秒 | |

### 觀察到的問題：
-

### 需要優化的 Prompt：
-

---

## 🚀 下一步

測試全部通過後，進入 **Phase 2: GraphRAG 實作**
- [ ] PDF 解析器
- [ ] 三元組提取
- [ ] 向量檢索 + 圖譜檢索

---

## 💡 快速切換回 Gemini (緊急情況)

如果 GPT-OSS-120B 出現問題，可以快速切換回 Gemini：

1. 修改 `.env`:
```
LLM_MODE=gemini
```

2. 取消註解 `agents/base.py` 中的 Gemini 代碼:
```python
# 在 base.py 中找到這些行並取消註解：
import google.generativeai as genai
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# ... (其他 Gemini 相關代碼)
```

3. 重新執行測試
