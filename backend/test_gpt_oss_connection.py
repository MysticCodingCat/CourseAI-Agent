"""
快速測試：驗證GPT-OSS-120B連接是否正常
參考 link_to_gpu.py 的成功模板
"""
import sys
import io
import time
from openai import OpenAI

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# GPU連接配置（與 link_to_gpu.py 相同）
vllm_gpt_oss_120b_url = 'http://210.61.209.139:45014/v1/'

print("=" * 60)
print("GPT-OSS-120B 連接測試")
print("AMD Instinct MI300X Platform")
print("=" * 60)

# Step 1: 獲取模型名稱
print("\n[Step 1] 正在獲取可用模型...")
try:
    import requests
    response = requests.get(vllm_gpt_oss_120b_url + "models")
    response.raise_for_status()
    models_data = response.json()

    if models_data.get("data"):
        model_name = models_data["data"][0]["id"]
        print(f"✓ 找到模型: {model_name}")
    else:
        model_name = "openai/gpt-oss-120b"
        print(f"⚠ 使用預設模型: {model_name}")
except Exception as e:
    print(f"✗ 獲取模型失敗: {e}")
    model_name = "openai/gpt-oss-120b"
    print(f"使用預設模型: {model_name}")

# Step 2: 初始化客戶端
print("\n[Step 2] 初始化 OpenAI 客戶端...")
client = OpenAI(base_url=vllm_gpt_oss_120b_url, api_key="NA")
print("✓ 客戶端初始化成功")

# Step 3: 測試 Chat Completion (Agent 使用的模式)
print("\n[Step 3] 測試 Chat Completion API...")
print("-" * 60)

test_messages = [
    {
        "role": "system",
        "content": "You are a helpful teaching assistant. Respond in Traditional Chinese (繁體中文)."
    },
    {
        "role": "user",
        "content": "請用一句話解釋什麼是神經網路？"
    }
]

print("發送測試訊息:")
print(f"  系統提示: {test_messages[0]['content']}")
print(f"  使用者輸入: {test_messages[1]['content']}")

try:
    start_time = time.time()

    completion = client.chat.completions.create(
        model=model_name,
        messages=test_messages,
        temperature=0.7,
        max_tokens=512,
    )

    end_time = time.time()
    elapsed_time = end_time - start_time

    response_text = completion.choices[0].message.content

    print("\n✓ API 呼叫成功！")
    print(f"  回應時間: {elapsed_time:.2f} 秒")
    print(f"  回應內容:\n")
    print("  " + "-" * 56)
    print(f"  {response_text}")
    print("  " + "-" * 56)

except Exception as e:
    print(f"\n✗ API 呼叫失敗: {e}")
    import traceback
    traceback.print_exc()

# Step 4: 測試繁體中文 JSON 輸出能力
print("\n[Step 4] 測試 JSON 格式輸出 (Agent關鍵能力)...")
print("-" * 60)

json_test_messages = [
    {
        "role": "system",
        "content": """You are a JSON generator.
Output Format (JSON only):
{
    "is_educational": true/false,
    "topic": "Topic Name (in Traditional Chinese)",
    "reasoning": "Why you think this is important"
}"""
    },
    {
        "role": "user",
        "content": '請分析這段話："今天我們要學習卷積神經網路的基本原理"'
    }
]

try:
    start_time = time.time()

    completion = client.chat.completions.create(
        model=model_name,
        messages=json_test_messages,
        temperature=0.3,  # 降低溫度以獲得更穩定的JSON
        max_tokens=256,
    )

    end_time = time.time()
    elapsed_time = end_time - start_time

    response_text = completion.choices[0].message.content

    print(f"✓ API 呼叫成功 (耗時: {elapsed_time:.2f}秒)")
    print(f"  原始回應:\n")
    print("  " + "-" * 56)
    print(f"  {response_text}")
    print("  " + "-" * 56)

    # 嘗試解析JSON
    import json
    import re

    # 清理markdown code blocks
    cleaned = re.sub(r"```json\s*", "", response_text)
    cleaned = re.sub(r"```", "", cleaned)
    cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
        print("\n✓ JSON 解析成功！")
        print(f"  解析結果: {parsed}")
    except json.JSONDecodeError as e:
        print(f"\n⚠ JSON 解析失敗: {e}")
        print("  這可能需要調整 prompt 格式")

except Exception as e:
    print(f"\n✗ API 呼叫失敗: {e}")

# 總結
print("\n" + "=" * 60)
print("測試總結")
print("=" * 60)
print("✓ 如果以上測試都成功，代表 GPT-OSS-120B 連接正常")
print("✓ 現在可以運行完整的 Agent 測試：")
print("  python test_agents_gpt_oss.py")
print("=" * 60)
