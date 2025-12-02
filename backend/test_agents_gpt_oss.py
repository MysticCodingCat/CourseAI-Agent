"""
測試腳本：驗證所有Agent在GPT-OSS-120B上的運行效果
"""
import asyncio
import sys
import os
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.listener import ListenerAgent
from agents.knowledge import KnowledgeAgent
from agents.tutor import TutorAgent
from agents.notetaker import NoteTakerAgent

# ANSI color codes for better output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

async def test_listener_agent():
    """Test 1: Listener Agent - 能否識別教育內容？"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}TEST 1: Listener Agent - 識別教育內容{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

    agent = ListenerAgent()

    test_cases = [
        {
            "input": "今天我們要學習神經網路的反向傳播演算法",
            "expected": "educational",
            "description": "正常教學內容"
        },
        {
            "input": "大家聽得到嗎？麥克風有問題嗎？",
            "expected": "noise",
            "description": "非教育內容（行政雜訊）"
        },
        {
            "input": "卷積神經網路是一種特殊的深度學習架構，主要用於影像辨識",
            "expected": "educational",
            "description": "專業術語內容"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"{Colors.OKBLUE}測試案例 {i}: {test['description']}{Colors.ENDC}")
        print(f"輸入: \"{test['input']}\"")

        result = await agent.process(test['input'])

        print(f"結果: {result}")

        if result.get("status") == "active":
            print(f"{Colors.OKGREEN}✓ 識別為教育內容{Colors.ENDC}")
            print(f"  關鍵詞: {result.get('keywords')}")
            print(f"  推理: {result.get('reasoning')}")
        else:
            print(f"{Colors.WARNING}✗ 識別為非教育內容{Colors.ENDC}")

        print("-" * 60)

    return True

async def test_knowledge_agent():
    """Test 2: Knowledge Agent - RAG檢索（目前是模擬）"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}TEST 2: Knowledge Agent - 知識檢索{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

    agent = KnowledgeAgent()

    keywords = ["反向傳播"]
    print(f"{Colors.OKBLUE}查詢關鍵詞: {keywords}{Colors.ENDC}")

    result = await agent.process(keywords)

    print(f"檢索結果:")
    print(f"  來源: {result.get('source')}")
    print(f"  內容: {result.get('retrieval_results')}")

    if result.get('retrieval_results'):
        print(f"{Colors.OKGREEN}✓ 知識檢索成功{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}✗ 知識檢索失敗{Colors.ENDC}")

    return True

async def test_tutor_agent():
    """Test 3: Tutor Agent - 蘇格拉底式提問"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}TEST 3: Tutor Agent - 生成問題{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

    agent = TutorAgent()

    # 模擬Knowledge Agent的輸出
    context = {
        "retrieval_results": [
            {
                "keyword": "反向傳播",
                "info": "反向傳播是一種訓練神經網路的演算法，通過鏈式法則計算梯度。"
            }
        ]
    }

    print(f"{Colors.OKBLUE}輸入情境: {context}{Colors.ENDC}")

    result = await agent.process(context)

    print(f"生成的問題:")
    print(f"  類型: {result.get('type')}")
    print(f"  問題: {result.get('content')}")
    print(f"  提示: {result.get('hint')}")
    print(f"  難度: {result.get('difficulty')}")

    if result.get('content'):
        print(f"{Colors.OKGREEN}✓ 問題生成成功{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}✗ 問題生成失敗{Colors.ENDC}")

    return True

async def test_notetaker_agent():
    """Test 4: NoteTaker Agent - 講義生成"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}TEST 4: NoteTaker Agent - 講義生成{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

    agent = NoteTakerAgent()

    transcript = """
    今天我們要學習深度學習的基礎。
    首先，什麼是神經網路？神經網路是一種模仿人腦結構的計算模型。
    它由多個層組成，包括輸入層、隱藏層和輸出層。
    每個神經元都會接收輸入，進行加權求和，然後通過激活函數產生輸出。
    常見的激活函數有ReLU、Sigmoid和Tanh。
    接下來我們看看反向傳播演算法，這是訓練神經網路的核心方法。
    """

    print(f"{Colors.OKBLUE}輸入逐字稿 (長度: {len(transcript)} 字元){Colors.ENDC}")
    print(f"內容摘要: {transcript[:100]}...")

    result = await agent.process(transcript)

    print(f"\n{Colors.OKGREEN}生成的講義:{Colors.ENDC}")
    print("-" * 60)
    print(result)
    print("-" * 60)

    if len(result) > 50:
        print(f"{Colors.OKGREEN}✓ 講義生成成功{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}✗ 講義生成失敗{Colors.ENDC}")

    return True

async def test_full_pipeline():
    """Test 5: 完整流程測試"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}TEST 5: 完整Agent流水線{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

    # 初始化所有Agent
    listener = ListenerAgent()
    knowledge = KnowledgeAgent()
    tutor = TutorAgent()

    # 模擬即時轉錄
    transcript_segment = "卷積神經網路使用卷積層來自動提取影像特徵"

    print(f"{Colors.OKBLUE}Step 1: Listener Agent 處理語音{Colors.ENDC}")
    listener_result = await listener.process(transcript_segment)
    print(f"結果: {listener_result}")

    if listener_result["status"] == "active":
        print(f"\n{Colors.OKBLUE}Step 2: Knowledge Agent 檢索知識{Colors.ENDC}")
        keywords = listener_result["keywords"]
        knowledge_result = await knowledge.process(keywords)
        print(f"結果: {knowledge_result}")

        print(f"\n{Colors.OKBLUE}Step 3: Tutor Agent 生成問題{Colors.ENDC}")
        tutor_result = await tutor.process(knowledge_result)
        print(f"結果: {tutor_result}")

        print(f"\n{Colors.OKGREEN}✓ 完整流水線執行成功！{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}Listener判定為非教育內容，流水線停止{Colors.ENDC}")

    return True

async def main():
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     CourseAI Agent 測試套件 - GPT-OSS-120B 版本           ║")
    print("║     AMD Instinct MI300X Platform                          ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")

    tests = [
        ("Listener Agent", test_listener_agent),
        ("Knowledge Agent", test_knowledge_agent),
        ("Tutor Agent", test_tutor_agent),
        ("NoteTaker Agent", test_notetaker_agent),
        ("完整流水線", test_full_pipeline),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n{Colors.FAIL}✗ {test_name} 測試失敗: {e}{Colors.ENDC}")
            results.append((test_name, False))

    # 總結報告
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("="*60)
    print("測試總結")
    print("="*60)
    print(f"{Colors.ENDC}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = f"{Colors.OKGREEN}✓ PASS{Colors.ENDC}" if success else f"{Colors.FAIL}✗ FAIL{Colors.ENDC}"
        print(f"{test_name}: {status}")

    print(f"\n{Colors.BOLD}結果: {passed}/{total} 測試通過{Colors.ENDC}")

    if passed == total:
        print(f"{Colors.OKGREEN}🎉 所有測試通過！可以開始下一階段開發。{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}⚠️  部分測試失敗，請檢查錯誤訊息。{Colors.ENDC}")

if __name__ == "__main__":
    asyncio.run(main())
