import asyncio
import websockets
import json
from datetime import datetime

async def test_agent_pipeline():
    uri = "ws://localhost:8000/ws/transcription"
    
    print(f"🔌 Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")

            # 模擬一段 "高含金量" 的課程內容
            test_message = {
                "text": "So, the key innovation here is the Self-Attention mechanism. Unlike RNNs, it allows the model to look at all words in the sequence simultaneously to determine context.",
                "timestamp": datetime.now().isoformat()
            }

            print(f"\n📤 Sending Transcript: \"{test_message['text']}\"")
            await websocket.send(json.dumps(test_message))
            print("⏳ Waiting for Agents to process (Calling Gemini Pro)...")

            # 等待回應
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(response)
                    
                    if data.get("type") == "insight":
                        print("\n" + "="*50)
                        print("🎉 SUCCESS! Agent Pipeline Response Received:")
                        print("="*50)
                        
                        # 顯示 Knowledge Agent 的結果
                        k_result = data.get("knowledge", {}).get("retrieval_results", [{}])[0]
                        print(f"\n📘 [Knowledge Agent] Topic Identified: {k_result.get('keyword')}")
                        print(f"📄 Info: {k_result.get('info')[:200]}...") # 只印前200字
                        
                        # 顯示 Tutor Agent 的結果
                        t_result = data.get("tutor", {})
                        print(f"\n🎓 [Tutor Agent] Question Generated:")
                        print(f"❓ {t_result.get('content')}")
                        print(f"💡 Hint: {t_result.get('hint')}")
                        
                        print("\n" + "="*50)
                        break
                    elif data.get("type") == "ack":
                         print("...Server acknowledged receipt, waiting for processing...")
                    else:
                        print(f"Received unknown type: {data}")

                except asyncio.TimeoutError:
                    print("❌ Timeout: No response received within 30 seconds.")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("❌ Connection closed prematurely.")
                    break

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure your uvicorn server is running on port 8000!")

if __name__ == "__main__":
    asyncio.run(test_agent_pipeline())
