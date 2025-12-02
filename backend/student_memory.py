"""
學生記憶追蹤系統
基於 SuperMemo SM-2 算法與遺忘曲線
實現個人化的間隔重複學習
"""
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import networkx as nx


class MemoryNode:
    """
    記憶節點：追蹤單一概念的記憶狀態
    """

    def __init__(self, concept: str):
        self.concept = concept

        # SuperMemo SM-2 參數
        self.easiness_factor = 2.5  # 難度係數（E-Factor），範圍 1.3-2.5
        self.interval = 1  # 複習間隔（天）
        self.repetitions = 0  # 成功複習次數

        # 時間追蹤
        self.last_review: Optional[datetime] = None  # 最後複習時間
        self.next_review: Optional[datetime] = None  # 下次複習時間
        self.created_at = datetime.now()

        # 記憶強度（0-1）
        self.memory_strength = 0.0

        # 歷史記錄
        self.review_history: List[Dict] = []  # {time, score, strength}

    def to_dict(self) -> Dict[str, Any]:
        """序列化為字典"""
        return {
            "concept": self.concept,
            "easiness_factor": self.easiness_factor,
            "interval": self.interval,
            "repetitions": self.repetitions,
            "last_review": self.last_review.isoformat() if self.last_review else None,
            "next_review": self.next_review.isoformat() if self.next_review else None,
            "memory_strength": self.memory_strength,
            "review_history": self.review_history,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryNode':
        """從字典反序列化"""
        node = cls(data["concept"])
        node.easiness_factor = data.get("easiness_factor", 2.5)
        node.interval = data.get("interval", 1)
        node.repetitions = data.get("repetitions", 0)
        node.memory_strength = data.get("memory_strength", 0.0)
        node.review_history = data.get("review_history", [])

        if data.get("last_review"):
            node.last_review = datetime.fromisoformat(data["last_review"])
        if data.get("next_review"):
            node.next_review = datetime.fromisoformat(data["next_review"])
        if data.get("created_at"):
            node.created_at = datetime.fromisoformat(data["created_at"])

        return node


class StudentMemoryTracker:
    """
    學生記憶追蹤系統

    功能：
    1. 追蹤每個概念的記憶狀態
    2. 實作 SuperMemo SM-2 間隔重複算法
    3. 計算遺忘曲線與記憶強度
    4. 推薦複習內容
    """

    def __init__(self, student_id: str):
        self.student_id = student_id
        self.knowledge_nodes: Dict[str, MemoryNode] = {}  # {concept: MemoryNode}
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

    def record_quiz_result(self, concept: str, score: int) -> Dict[str, Any]:
        """
        記錄測驗結果並更新記憶參數

        Args:
            concept: 概念名稱
            score: 0-5 的評分
                   5 = 完美回憶
                   4 = 正確但稍有猶豫
                   3 = 正確但困難
                   2 = 錯誤但記得一些
                   1 = 錯誤且幾乎不記得
                   0 = 完全忘記

        Returns:
            更新後的記憶狀態
        """
        # 獲取或創建節點
        if concept not in self.knowledge_nodes:
            self.knowledge_nodes[concept] = MemoryNode(concept)

        node = self.knowledge_nodes[concept]

        # SuperMemo SM-2 算法
        if score >= 3:
            # 回憶成功
            if node.repetitions == 0:
                node.interval = 1
            elif node.repetitions == 1:
                node.interval = 6
            else:
                node.interval = round(node.interval * node.easiness_factor)

            node.repetitions += 1
        else:
            # 回憶失敗，重置
            node.repetitions = 0
            node.interval = 1

        # 更新難度係數（E-Factor）
        # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        # q 是評分（0-5）
        node.easiness_factor = max(
            1.3,
            node.easiness_factor + (0.1 - (5 - score) * (0.08 + (5 - score) * 0.02))
        )

        # 更新時間
        node.last_review = datetime.now()
        node.next_review = node.last_review + timedelta(days=node.interval)

        # 計算記憶強度
        node.memory_strength = self._calculate_memory_strength(node)

        # 記錄歷史
        node.review_history.append({
            "time": node.last_review.isoformat(),
            "score": score,
            "strength": node.memory_strength,
            "interval": node.interval
        })

        self.last_activity = datetime.now()

        return {
            "concept": concept,
            "new_strength": node.memory_strength,
            "next_review": node.next_review.isoformat(),
            "interval_days": node.interval,
            "total_reviews": len(node.review_history)
        }

    def _calculate_memory_strength(self, node: MemoryNode) -> float:
        """
        計算記憶強度（基於 Ebbinghaus 遺忘曲線）

        公式：R = e^(-t/S)
        R: 記憶保留率
        t: 距離上次複習的時間（天）
        S: 記憶穩定性（stability），取決於間隔和難度係數

        Returns:
            記憶強度（0-1）
        """
        if node.last_review is None:
            return 0.0

        # 計算經過的時間（天）
        elapsed = datetime.now() - node.last_review
        elapsed_days = elapsed.total_seconds() / 86400  # 秒轉天

        # 記憶穩定性（結合間隔和難度係數）
        stability = node.interval * node.easiness_factor

        # 遺忘曲線
        retention = math.exp(-elapsed_days / stability)

        # 限制在 0-1 範圍
        return max(0.0, min(1.0, retention))

    def get_concepts_to_review(
        self,
        threshold: float = 0.3,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        獲取需要複習的概念

        Args:
            threshold: 記憶強度閾值（低於此值需要複習）
            limit: 返回數量上限

        Returns:
            需要複習的概念列表，按優先級排序
        """
        weak_concepts = []

        for concept, node in self.knowledge_nodes.items():
            # 更新記憶強度
            strength = self._calculate_memory_strength(node)
            node.memory_strength = strength

            if strength < threshold or (node.next_review and datetime.now() >= node.next_review):
                weak_concepts.append({
                    "concept": concept,
                    "strength": strength,
                    "priority": 1.0 - strength,  # 越弱優先級越高
                    "next_review": node.next_review.isoformat() if node.next_review else None,
                    "days_since_review": (datetime.now() - node.last_review).days if node.last_review else 999
                })

        # 按優先級排序
        weak_concepts.sort(key=lambda x: (x["priority"], x["days_since_review"]), reverse=True)

        return weak_concepts[:limit]

    def get_mastered_concepts(self, threshold: float = 0.8) -> List[str]:
        """
        獲取已掌握的概念

        Args:
            threshold: 記憶強度閾值（高於此值視為已掌握）

        Returns:
            已掌握的概念列表
        """
        mastered = []

        for concept, node in self.knowledge_nodes.items():
            strength = self._calculate_memory_strength(node)
            node.memory_strength = strength

            if strength >= threshold:
                mastered.append(concept)

        return mastered

    def get_learning_progress(self) -> Dict[str, Any]:
        """
        獲取整體學習進度

        Returns:
            學習統計資訊
        """
        if not self.knowledge_nodes:
            return {
                "total_concepts": 0,
                "average_strength": 0.0,
                "mastered_count": 0,
                "weak_count": 0,
                "needs_review": 0
            }

        total = len(self.knowledge_nodes)
        strengths = []
        mastered = 0
        weak = 0
        needs_review = 0

        for concept, node in self.knowledge_nodes.items():
            strength = self._calculate_memory_strength(node)
            node.memory_strength = strength
            strengths.append(strength)

            if strength >= 0.8:
                mastered += 1
            elif strength < 0.3:
                weak += 1

            if node.next_review and datetime.now() >= node.next_review:
                needs_review += 1

        return {
            "total_concepts": total,
            "average_strength": sum(strengths) / total,
            "mastered_count": mastered,
            "mastered_percentage": (mastered / total) * 100,
            "weak_count": weak,
            "weak_percentage": (weak / total) * 100,
            "needs_review": needs_review
        }

    def export_knowledge_graph(self) -> nx.DiGraph:
        """
        匯出個人知識圖譜（可視覺化）

        Returns:
            NetworkX 有向圖
        """
        G = nx.DiGraph()

        for concept, node in self.knowledge_nodes.items():
            strength = self._calculate_memory_strength(node)
            node.memory_strength = strength

            G.add_node(
                concept,
                strength=strength,
                interval=node.interval,
                next_review=node.next_review.isoformat() if node.next_review else None,
                repetitions=node.repetitions,
                easiness=node.easiness_factor
            )

        return G

    def to_dict(self) -> Dict[str, Any]:
        """序列化整個追蹤器"""
        return {
            "student_id": self.student_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "knowledge_nodes": {
                concept: node.to_dict()
                for concept, node in self.knowledge_nodes.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudentMemoryTracker':
        """從字典反序列化"""
        tracker = cls(data["student_id"])
        tracker.created_at = datetime.fromisoformat(data["created_at"])
        tracker.last_activity = datetime.fromisoformat(data["last_activity"])

        for concept, node_data in data.get("knowledge_nodes", {}).items():
            tracker.knowledge_nodes[concept] = MemoryNode.from_dict(node_data)

        return tracker

    def save_to_file(self, filepath: str):
        """儲存到 JSON 檔案"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'StudentMemoryTracker':
        """從 JSON 檔案載入"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)


# 測試函數
def test_memory_tracker():
    """測試記憶追蹤系統"""
    print("=== 測試學生記憶追蹤系統 ===\n")

    # 創建追蹤器
    tracker = StudentMemoryTracker(student_id="student_001")

    # 模擬學習過程
    print("1. 學習新概念：卷積神經網路")
    result = tracker.record_quiz_result("卷積神經網路", score=4)
    print(f"   記憶強度: {result['new_strength']:.2f}")
    print(f"   下次複習: {result['next_review']}")
    print(f"   複習間隔: {result['interval_days']} 天\n")

    print("2. 學習新概念：反向傳播")
    result = tracker.record_quiz_result("反向傳播", score=3)
    print(f"   記憶強度: {result['new_strength']:.2f}\n")

    print("3. 學習新概念：Dropout")
    result = tracker.record_quiz_result("Dropout", score=5)
    print(f"   記憶強度: {result['new_strength']:.2f}\n")

    # 模擬時間流逝（3天後）
    print("--- 3天後 ---\n")
    for concept, node in tracker.knowledge_nodes.items():
        node.last_review = datetime.now() - timedelta(days=3)

    # 檢查需要複習的概念
    print("4. 檢查需要複習的概念：")
    to_review = tracker.get_concepts_to_review(threshold=0.5)
    for item in to_review:
        print(f"   - {item['concept']}: 記憶強度 {item['strength']:.2f}")

    # 查看整體進度
    print("\n5. 整體學習進度：")
    progress = tracker.get_learning_progress()
    print(f"   總概念數: {progress['total_concepts']}")
    print(f"   平均記憶強度: {progress['average_strength']:.2f}")
    print(f"   已掌握: {progress['mastered_count']} ({progress['mastered_percentage']:.1f}%)")
    print(f"   需加強: {progress['weak_count']} ({progress['weak_percentage']:.1f}%)")

    # 測試序列化
    print("\n6. 測試儲存與載入：")
    tracker.save_to_file("test_student_memory.json")
    print("   已儲存到 test_student_memory.json")

    loaded_tracker = StudentMemoryTracker.load_from_file("test_student_memory.json")
    print(f"   載入成功，學生 ID: {loaded_tracker.student_id}")
    print(f"   概念數: {len(loaded_tracker.knowledge_nodes)}")


if __name__ == "__main__":
    test_memory_tracker()
