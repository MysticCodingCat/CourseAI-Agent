"""
實時學習分析系統
利用 MI300X 的高頻處理能力進行即時答案分析
"""
import re
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from openai import OpenAI
import os

from student_memory import StudentMemoryTracker


class RealtimeLearningAnalytics:
    """
    實時學習分析系統

    功能：
    1. 即時評分學生答案（LLM 評分）
    2. 識別錯誤概念（錯誤診斷）
    3. 生成個性化回饋（蘇格拉底式引導）
    4. 推薦下一步行動（學習路徑）

    MI300X 優勢：
    - 高頻 API 請求（單次分析 4-5 次推理）
    - 無 rate limit 限制
    - 2 秒內完成完整分析
    """

    def __init__(self, student_tracker: StudentMemoryTracker):
        """
        初始化分析系統

        Args:
            student_tracker: 學生記憶追蹤器
        """
        self.student_tracker = student_tracker

        # GPT-OSS-120B 客戶端
        vllm_url = os.getenv("VLLM_BASE_URL", "http://210.61.209.139:45014/v1/")
        self.llm_client = OpenAI(base_url=vllm_url, api_key="NA")
        self.llm_model = "openai/gpt-oss-120b"

        # 統計資訊
        self.total_analyses = 0
        self.total_api_calls = 0

    async def analyze_answer(
        self,
        question: Dict[str, Any],
        student_answer: str
    ) -> Dict[str, Any]:
        """
        完整分析學生答案（高頻 API 請求）

        流程：
        1. 評分（API 請求 #1）
        2. 識別錯誤概念（API 請求 #2）
        3. 生成回饋（API 請求 #3）
        4. 更新記憶狀態
        5. 推薦下一步（API 請求 #4）

        Args:
            question: 題目字典
            student_answer: 學生答案

        Returns:
            完整分析結果
        """
        start_time = datetime.now()

        print(f"\n[RealTime] 開始分析答案...")
        print(f"  概念: {question['concept']}")
        print(f"  題型: {question['type']}")

        # 並行執行評分與錯誤診斷（節省時間）
        score_task = self._score_answer(question, student_answer)
        misconception_task = self._identify_misconceptions(question, student_answer)

        score, misconceptions = await asyncio.gather(score_task, misconception_task)

        # 生成回饋
        feedback = await self._generate_feedback(
            question=question,
            answer=student_answer,
            score=score,
            misconceptions=misconceptions
        )

        # 更新記憶追蹤
        memory_update = self.student_tracker.record_quiz_result(
            concept=question["concept"],
            score=score
        )

        # 推薦下一步
        next_action = await self._recommend_next_action(
            memory_update["new_strength"],
            question["concept"],
            score
        )

        # 計算分析時間
        elapsed = (datetime.now() - start_time).total_seconds()

        # 統計
        self.total_analyses += 1
        self.total_api_calls += 4  # 評分+錯誤診斷+回饋+推薦

        result = {
            "score": score,
            "feedback": feedback,
            "misconceptions": misconceptions,
            "memory_update": memory_update,
            "next_action": next_action,
            "analysis_time_seconds": elapsed,
            "timestamp": datetime.now().isoformat()
        }

        print(f"\n[RealTime] 分析完成")
        print(f"  評分: {score}/5")
        print(f"  記憶強度: {memory_update['new_strength']:.2f}")
        print(f"  耗時: {elapsed:.2f} 秒")
        print(f"  API 呼叫: 4 次")

        return result

    async def _score_answer(
        self,
        question: Dict[str, Any],
        answer: str
    ) -> int:
        """
        使用 LLM 評分（0-5）

        評分標準：
        5 = 完美回答
        4 = 良好
        3 = 及格
        2 = 不足
        1 = 差
        0 = 完全錯誤或未作答
        """
        rubric = question.get("rubric", {})

        prompt = f"""評分學生答案（0-5分）。

問題：{question['question']}

標準答案：
{question.get('answer', '請參考課程講義')}

評分標準：
- 5分（優秀）：{rubric.get('excellent', '完整且深入')}
- 4分（良好）：{rubric.get('good', '正確且清楚')}
- 3分（及格）：{rubric.get('pass', '基本正確')}
- 0-2分（不足/錯誤）：{rubric.get('fail', '錯誤或遺漏')}

學生答案：
{answer}

請輸出JSON格式（不要其他內容）：
{{"score": 分數(0-5的整數), "reasoning": "簡短評分理由"}}"""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是嚴格但公正的評分者。根據標準客觀評分。只輸出JSON，不要其他內容。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 低溫度確保評分一致性
                max_tokens=256
            )

            content = response.choices[0].message.content.strip()

            # 清理回應
            content = re.sub(r"^.*?assistantfinal", "", content, flags=re.DOTALL)
            content = re.sub(r"```json\s*", "", content)
            content = re.sub(r"```", "", content)
            content = content.strip()

            # 解析 JSON
            result = json.loads(content)
            score = int(result.get("score", 0))

            # 限制在 0-5 範圍
            score = max(0, min(5, score))

            return score

        except Exception as e:
            print(f"[RealTime] 評分失敗: {e}")
            # 簡單啟發式評分（備用）
            if len(answer.strip()) < 10:
                return 0
            elif len(answer.strip()) < 50:
                return 2
            else:
                return 3

    async def _identify_misconceptions(
        self,
        question: Dict[str, Any],
        answer: str
    ) -> List[str]:
        """
        識別學生答案中的錯誤概念
        """
        if len(answer.strip()) < 10:
            return ["答案過於簡短"]

        prompt = f"""分析學生答案中的錯誤理解或遺漏。

問題：{question['question']}

標準答案：
{question.get('answer', '請參考課程講義')}

學生答案：
{answer}

請找出學生的錯誤或不足之處（如果有）。

輸出JSON數組格式（不要其他內容）：
["錯誤1", "錯誤2", ...]

如果答案完全正確，返回空數組：[]"""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是教育診斷專家。識別學生的錯誤理解與知識盲點。只輸出JSON數組。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=512
            )

            content = response.choices[0].message.content.strip()

            # 清理回應
            content = re.sub(r"^.*?assistantfinal", "", content, flags=re.DOTALL)
            content = re.sub(r"```json\s*", "", content)
            content = re.sub(r"```", "", content)
            content = content.strip()

            # 解析 JSON
            result = json.loads(content)

            if isinstance(result, list):
                return result[:3]  # 最多返回 3 個錯誤
            else:
                return []

        except Exception as e:
            print(f"[RealTime] 錯誤診斷失敗: {e}")
            return []

    async def _generate_feedback(
        self,
        question: Dict[str, Any],
        answer: str,
        score: int,
        misconceptions: List[str]
    ) -> str:
        """
        生成個性化學習回饋

        原則：
        1. 先肯定對的部分（正向強化）
        2. 使用蘇格拉底式提問（引導思考，不直接給答案）
        3. 提供具體改進建議
        4. 語氣友善且鼓勵
        """
        # 根據評分決定回饋類型
        if score >= 4:
            feedback_type = "positive_reinforcement"
            instruction = "肯定學生的理解，並提出可以深入探索的方向。"
        elif score >= 3:
            feedback_type = "encouraging_with_hints"
            instruction = "先肯定正確的部分，然後用提問方式引導學生思考不足之處。"
        elif misconceptions:
            feedback_type = "corrective_guidance"
            instruction = "溫和地指出錯誤，用問題引導學生重新思考，而不是直接給答案。"
        else:
            feedback_type = "supportive_redirection"
            instruction = "鼓勵學生，建議複習相關內容後再嘗試。"

        misconceptions_text = "\n".join([f"- {m}" for m in misconceptions]) if misconceptions else "無明顯錯誤"

        prompt = f"""生成個性化學習回饋。

問題：{question['question']}

學生答案：
{answer}

評分：{score}/5

識別到的問題：
{misconceptions_text}

回饋類型：{feedback_type}

要求：
{instruction}

回饋原則：
1. **先肯定**：指出學生答案中正確的部分
2. **蘇格拉底式提問**：用問題引導思考（例如："你有想過...嗎？"、"如果...會怎麼樣？"）
3. **具體建議**：提供明確的改進方向
4. **語氣友善**：像導師而非批評者
5. **長度**：100-150字
6. **繁體中文**

回饋："""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是有耐心的導師，善於用提問引導學生思考，而不是直接告訴答案。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # 較高溫度讓回饋更自然
                max_tokens=512
            )

            content = response.choices[0].message.content.strip()

            # 清理回應
            content = re.sub(r"^.*?assistantfinal", "", content, flags=re.DOTALL)
            content = content.replace("回饋：", "").strip()

            return content

        except Exception as e:
            print(f"[RealTime] 回饋生成失敗: {e}")
            # 備用回饋
            if score >= 4:
                return "你的回答很好！繼續保持這樣的學習態度。"
            elif score >= 3:
                return "你已經掌握了基本概念，試著再深入思考一下應用場景。"
            else:
                return "建議複習一下課程內容，再嘗試回答這個問題。"

    async def _recommend_next_action(
        self,
        memory_strength: float,
        concept: str,
        recent_score: int
    ) -> Dict[str, Any]:
        """
        推薦下一步學習行動

        基於：
        1. 記憶強度
        2. 最近表現
        3. 遺忘曲線預測
        """
        # 根據記憶強度決定行動
        if memory_strength < 0.3:
            action = "review"
            message = f"你對「{concept}」的記憶較弱，建議立即複習課程內容。"
            next_review_in = "立即"
            urgency = "high"

        elif memory_strength < 0.5:
            action = "practice"
            message = f"繼續練習「{concept}」相關題目，加深理解。"
            next_review_in = "1天後"
            urgency = "medium"

        elif memory_strength < 0.7:
            action = "reinforce"
            message = f"你已經基本掌握「{concept}」，試著做一些應用題來鞏固。"
            next_review_in = "3天後"
            urgency = "low"

        else:
            action = "advance"
            message = f"你已經很好地掌握「{concept}」，可以學習更進階的內容。"
            next_review_in = "7天後"
            urgency = "none"

        # 根據最近表現調整
        if recent_score <= 2 and action != "review":
            action = "review"
            message = f"雖然記憶強度不錯，但最近表現不理想，建議複習「{concept}」。"
            urgency = "medium"

        # 獲取相關概念（進階學習方向）
        related_concepts = await self._get_related_concepts(concept)

        return {
            "action": action,
            "message": message,
            "next_review_in": next_review_in,
            "urgency": urgency,
            "memory_strength": memory_strength,
            "related_concepts": related_concepts,
            "recommended_at": datetime.now().isoformat()
        }

    async def _get_related_concepts(self, concept: str) -> List[str]:
        """
        獲取相關概念（用於推薦進階學習）
        """
        # 這裡可以整合 GraphRAG 來找相關概念
        # 簡化版：使用 LLM 生成
        prompt = f"""列出與「{concept}」相關的 3 個深度學習概念（繁體中文）。

只輸出JSON數組：["概念1", "概念2", "概念3"]"""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "你是課程規劃專家。只輸出JSON數組。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=128
            )

            content = response.choices[0].message.content.strip()
            content = re.sub(r"^.*?assistantfinal", "", content, flags=re.DOTALL)
            content = re.sub(r"```json\s*", "", content)
            content = re.sub(r"```", "", content)

            result = json.loads(content)
            return result if isinstance(result, list) else []

        except Exception as e:
            print(f"[RealTime] 相關概念獲取失敗: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        獲取分析統計
        """
        return {
            "total_analyses": self.total_analyses,
            "total_api_calls": self.total_api_calls,
            "average_calls_per_analysis": self.total_api_calls / max(1, self.total_analyses)
        }


# 測試函數
async def test_realtime_analytics():
    """測試實時學習分析系統"""
    print("=== 測試實時學習分析系統 ===\n")

    # 創建學生追蹤器
    from student_memory import StudentMemoryTracker
    tracker = StudentMemoryTracker(student_id="test_student")

    # 創建分析系統
    analytics = RealtimeLearningAnalytics(student_tracker=tracker)

    # 模擬題目
    test_question = {
        "question": "請解釋什麼是卷積神經網路（CNN）？",
        "concept": "卷積神經網路",
        "type": "recall",
        "difficulty": "medium",
        "answer": "卷積神經網路（CNN）是一種專門用於處理網格狀資料的深度學習架構，主要應用於影像辨識。它使用卷積層來自動提取特徵，無需手工設計。",
        "rubric": {
            "excellent": "完整說明定義、架構、應用",
            "good": "正確定義並說明用途",
            "pass": "基本定義正確",
            "fail": "定義錯誤"
        }
    }

    # 測試案例
    test_answers = [
        {
            "name": "優秀答案",
            "answer": "卷積神經網路（CNN）是一種深度學習架構，專門用於處理影像等網格資料。它的核心是卷積層，能自動學習和提取影像特徵，例如邊緣、紋理等。CNN 廣泛應用於影像辨識、物體檢測等任務。"
        },
        {
            "name": "中等答案",
            "answer": "CNN 是用來處理影像的神經網路，使用卷積層來提取特徵。"
        },
        {
            "name": "不足答案",
            "answer": "CNN 就是一種神經網路。"
        }
    ]

    for i, test_case in enumerate(test_answers, 1):
        print(f"\n{'='*60}")
        print(f"測試案例 {i}: {test_case['name']}")
        print(f"{'='*60}")
        print(f"學生答案: {test_case['answer']}\n")

        # 分析答案
        result = await analytics.analyze_answer(test_question, test_case["answer"])

        print(f"\n結果：")
        print(f"  評分: {result['score']}/5")
        print(f"  錯誤概念: {result['misconceptions']}")
        print(f"\n  回饋:")
        print(f"  {result['feedback']}")
        print(f"\n  記憶更新:")
        print(f"    新記憶強度: {result['memory_update']['new_strength']:.2f}")
        print(f"    下次複習: {result['memory_update']['next_review']}")
        print(f"\n  下一步建議:")
        print(f"    行動: {result['next_action']['action']}")
        print(f"    訊息: {result['next_action']['message']}")
        print(f"\n  分析時間: {result['analysis_time_seconds']:.2f} 秒")

    # 統計資訊
    print(f"\n{'='*60}")
    print("統計資訊")
    print(f"{'='*60}")
    stats = analytics.get_statistics()
    print(f"總分析次數: {stats['total_analyses']}")
    print(f"總 API 呼叫: {stats['total_api_calls']}")
    print(f"平均每次分析 API 呼叫: {stats['average_calls_per_analysis']:.1f} 次")


if __name__ == "__main__":
    asyncio.run(test_realtime_analytics())
