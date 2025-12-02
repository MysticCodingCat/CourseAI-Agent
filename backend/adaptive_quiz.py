"""
智慧題目生成器
基於學習科學原理生成個人化測驗
"""
import random
import re
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
import os

from rag_engine import GraphRAG


class AdaptiveQuizGenerator:
    """
    智慧題目生成器

    功能：
    1. 根據記憶狀態生成個人化題目
    2. 多種題型（回憶、應用、關聯、錯誤診斷）
    3. 動態難度調整
    4. 基於 GraphRAG 的上下文檢索
    """

    def __init__(self, rag_engine: GraphRAG = None):
        """
        初始化題目生成器

        Args:
            rag_engine: GraphRAG 引擎（用於檢索課程內容）
        """
        self.rag_engine = rag_engine

        # GPT-OSS-120B 客戶端
        vllm_url = os.getenv("VLLM_BASE_URL", "http://210.61.209.139:45014/v1/")
        self.llm_client = OpenAI(base_url=vllm_url, api_key="NA")
        self.llm_model = "openai/gpt-oss-120b"

        # 題目模板
        self.question_templates = {
            "recall": [
                "請用自己的話解釋「{concept}」。",
                "「{concept}」的定義是什麼？請詳細說明。",
                "什麼是「{concept}」？為什麼它在深度學習中很重要？",
                "請描述「{concept}」的核心概念。"
            ],
            "application": [
                "在什麼情況下應該使用「{concept}」？請舉例說明。",
                "假設你的模型{scenario}，應該考慮使用「{concept}」嗎？為什麼？",
                "請舉一個「{concept}」在實際深度學習專案中的應用案例。",
                "如何在 PyTorch 或 TensorFlow 中實作「{concept}」？"
            ],
            "relational": [
                "請比較「{concept1}」和「{concept2}」的差異與相似之處。",
                "「{concept1}」和「{concept2}」有什麼關聯？它們如何互相影響？",
                "在什麼情況下選擇「{concept1}」而不是「{concept2}」？",
                "如何結合「{concept1}」和「{concept2}」來改進深度學習模型？"
            ],
            "error_analysis": [
                "有同學說『{misconception}』，請指出這個說法的錯誤並解釋正確概念。",
                "以下關於「{concept}」的說法有什麼問題？『{misconception}』請糾正。",
                "『{misconception}』這個觀念哪裡不正確？正確的理解應該是什麼？"
            ]
        }

        # 評分標準模板
        self.rubric_templates = {
            "recall": {
                "excellent": "完整說明定義、用途與重要性，並舉例",
                "good": "正確定義並說明用途",
                "pass": "基本定義正確",
                "fail": "定義錯誤或遺漏關鍵概念"
            },
            "application": {
                "excellent": "準確識別場景、完整解釋原因、提出具體實作方法",
                "good": "識別場景並部分解釋",
                "pass": "基本識別應用場景",
                "fail": "場景判斷錯誤或無法應用"
            },
            "relational": {
                "excellent": "準確比較異同、指出深層聯繫、說明應用差異",
                "good": "準確比較並指出部分聯繫",
                "pass": "基本比較異同",
                "fail": "比較錯誤或遺漏關鍵差異"
            },
            "error_analysis": {
                "excellent": "準確指出錯誤、深入解釋原因、提供正確概念與例子",
                "good": "指出錯誤並部分解釋",
                "pass": "能識別錯誤",
                "fail": "未能識別錯誤或糾正錯誤"
            }
        }

    def generate_question(
        self,
        concept: str,
        memory_strength: float = 0.5,
        question_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成單一題目

        Args:
            concept: 目標概念
            memory_strength: 記憶強度（0-1），用於決定難度和題型
            question_type: 指定題型（若為 None 則自動選擇）

        Returns:
            題目字典
        """
        print(f"[QuizGen] 生成題目: {concept} (記憶強度: {memory_strength:.2f})")

        # 根據記憶強度決定題型
        if question_type is None:
            question_type = self._select_question_type(memory_strength)

        # 根據記憶強度決定難度
        difficulty = self._estimate_difficulty(memory_strength)

        # 從 GraphRAG 獲取上下文
        context = self._get_context(concept)

        # 生成題目
        if question_type == "relational" and context.get("related_concepts"):
            # 關聯題：需要兩個概念
            question_text = self._generate_relational_question(concept, context)
        elif question_type == "error_analysis":
            # 錯誤診斷題：需要生成錯誤概念
            question_text = self._generate_error_question(concept, context)
        else:
            # 回憶題或應用題
            question_text = self._generate_standard_question(concept, question_type, context)

        # 生成標準答案
        answer = self._generate_answer(question_text, concept, context)

        # 獲取評分標準
        rubric = self.rubric_templates.get(question_type, self.rubric_templates["recall"])

        return {
            "question": question_text,
            "concept": concept,
            "type": question_type,
            "difficulty": difficulty,
            "answer": answer,
            "rubric": rubric,
            "memory_strength": memory_strength,
            "context": {
                "vector_matches": len(context.get("vector_results", [])),
                "graph_relations": len(context.get("related_concepts", []))
            }
        }

    def _select_question_type(self, memory_strength: float) -> str:
        """
        根據記憶強度選擇題型

        記憶很弱（<0.3）→ 回憶題（直接回憶）
        記憶中等（0.3-0.6）→ 應用題（情境應用）
        記憶較強（0.6-0.8）→ 關聯題（概念連結）
        記憶很強（>0.8）→ 錯誤診斷題（深度理解）
        """
        if memory_strength < 0.3:
            return "recall"
        elif memory_strength < 0.6:
            return "application"
        elif memory_strength < 0.8:
            return "relational"
        else:
            return "error_analysis"

    def _estimate_difficulty(self, memory_strength: float) -> str:
        """
        根據記憶強度估算難度
        """
        if memory_strength < 0.3:
            return "easy"
        elif memory_strength < 0.7:
            return "medium"
        else:
            return "hard"

    def _get_context(self, concept: str) -> Dict[str, Any]:
        """
        從 GraphRAG 獲取上下文
        """
        if self.rag_engine is None:
            return {"vector_results": [], "related_concepts": []}

        try:
            search_results = self.rag_engine.hybrid_search(concept, top_k=3)
            vector_results = search_results.get("vector_results", [])
            graph_results = search_results.get("graph_results", [])

            # 提取相關概念
            related_concepts = [r["entity"] for r in graph_results[:3]]

            return {
                "vector_results": vector_results,
                "related_concepts": related_concepts,
                "graph_results": graph_results
            }
        except Exception as e:
            print(f"[QuizGen] GraphRAG 檢索失敗: {e}")
            return {"vector_results": [], "related_concepts": []}

    def _generate_standard_question(
        self,
        concept: str,
        question_type: str,
        context: Dict[str, Any]
    ) -> str:
        """
        生成標準題目（回憶題或應用題）
        """
        templates = self.question_templates.get(question_type, self.question_templates["recall"])
        template = random.choice(templates)

        # 應用題需要填入情境
        if "{scenario}" in template:
            scenarios = [
                "訓練集表現好但測試集很差",
                "損失函數持續震盪不收斂",
                "訓練速度非常慢",
                "梯度在反向傳播時消失",
                "需要處理高解析度影像"
            ]
            scenario = random.choice(scenarios)
            return template.format(concept=concept, scenario=scenario)
        else:
            return template.format(concept=concept)

    def _generate_relational_question(
        self,
        concept: str,
        context: Dict[str, Any]
    ) -> str:
        """
        生成關聯題（比較兩個概念）
        """
        related_concepts = context.get("related_concepts", [])

        if not related_concepts:
            # 沒有相關概念，退回到回憶題
            return self._generate_standard_question(concept, "recall", context)

        # 選擇一個相關概念
        related_concept = random.choice(related_concepts)

        templates = self.question_templates["relational"]
        template = random.choice(templates)

        return template.format(concept1=concept, concept2=related_concept)

    def _generate_error_question(
        self,
        concept: str,
        context: Dict[str, Any]
    ) -> str:
        """
        生成錯誤診斷題
        """
        # 使用 LLM 生成常見錯誤概念
        misconception = self._generate_misconception(concept, context)

        if not misconception:
            # 生成失敗，退回到應用題
            return self._generate_standard_question(concept, "application", context)

        templates = self.question_templates["error_analysis"]
        template = random.choice(templates)

        return template.format(concept=concept, misconception=misconception)

    def _generate_misconception(self, concept: str, context: Dict[str, Any]) -> str:
        """
        生成常見錯誤概念
        """
        vector_results = context.get("vector_results", [])
        context_text = vector_results[0]["text"] if vector_results else ""

        prompt = f"""基於以下課程內容，生成一個關於「{concept}」的**常見學生錯誤理解**。

課程內容：
{context_text[:500]}

要求：
1. 這個錯誤要**似是而非**（學生容易犯）
2. 用一句話表達
3. 繁體中文
4. 不要包含引號

範例：
- 概念：梯度下降
- 錯誤：學習率越大，模型訓練越快且效果越好

請生成關於「{concept}」的錯誤理解（只輸出錯誤陳述，不要其他內容）："""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "你是教育專家，擅長識別學生的常見錯誤。只輸出錯誤陳述，不要額外說明。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=256
            )

            content = response.choices[0].message.content.strip()

            # 清理回應
            content = re.sub(r"^.*?assistantfinal", "", content, flags=re.DOTALL)
            content = content.replace("錯誤理解：", "").replace("錯誤：", "").strip()
            content = content.strip('"\'')

            return content if len(content) > 10 else ""

        except Exception as e:
            print(f"[QuizGen] 錯誤概念生成失敗: {e}")
            return ""

    def _generate_answer(
        self,
        question: str,
        concept: str,
        context: Dict[str, Any]
    ) -> str:
        """
        生成標準答案
        """
        vector_results = context.get("vector_results", [])
        context_text = "\n".join([r["text"][:300] for r in vector_results[:2]])

        prompt = f"""根據課程內容，回答以下問題。

課程內容：
{context_text}

問題：{question}

要求：
1. 回答要基於課程內容
2. 清晰、簡潔（150-250字）
3. 結構化（可使用條列）
4. 繁體中文

標準答案："""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "你是專業教師，提供精確且結構化的標準答案。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=512
            )

            content = response.choices[0].message.content.strip()

            # 清理回應
            content = re.sub(r"^.*?assistantfinal", "", content, flags=re.DOTALL)

            return content

        except Exception as e:
            print(f"[QuizGen] 答案生成失敗: {e}")
            return "標準答案生成失敗，請參考課程講義。"

    def generate_quiz_set(
        self,
        concepts_with_strength: List[Dict[str, Any]],
        num_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        生成一組測驗題目

        Args:
            concepts_with_strength: 概念列表 [{"concept": "概念", "strength": 0.5}, ...]
            num_questions: 題目數量

        Returns:
            題目列表
        """
        quiz_set = []

        # 選擇要測驗的概念（優先選擇記憶弱的）
        concepts_with_strength.sort(key=lambda x: x["strength"])
        selected = concepts_with_strength[:num_questions]

        for item in selected:
            try:
                question = self.generate_question(
                    concept=item["concept"],
                    memory_strength=item["strength"]
                )
                quiz_set.append(question)
            except Exception as e:
                print(f"[QuizGen] 生成題目失敗 ({item['concept']}): {e}")

        return quiz_set


# 測試函數
def test_quiz_generator():
    """測試題目生成器"""
    print("=== 測試智慧題目生成器 ===\n")

    # 創建生成器（不使用 RAG，純測試）
    generator = AdaptiveQuizGenerator(rag_engine=None)

    # 測試不同記憶強度的題目
    test_cases = [
        {"concept": "卷積神經網路", "strength": 0.2},
        {"concept": "反向傳播", "strength": 0.5},
        {"concept": "Dropout", "strength": 0.9}
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"{i}. 測試概念：{case['concept']} (記憶強度: {case['strength']})")

        question = generator.generate_question(
            concept=case["concept"],
            memory_strength=case["strength"]
        )

        print(f"   題型: {question['type']}")
        print(f"   難度: {question['difficulty']}")
        print(f"   問題: {question['question']}")
        print(f"   標準答案: {question['answer'][:100]}...")
        print()

    # 測試批量生成
    print("\n4. 測試批量生成（5題）：")
    quiz_set = generator.generate_quiz_set(test_cases, num_questions=3)
    print(f"   生成了 {len(quiz_set)} 題")


if __name__ == "__main__":
    test_quiz_generator()
