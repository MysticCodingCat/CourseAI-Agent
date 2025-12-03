"""
課堂會話管理器
管理單一學生的資料載入、快取與卸載生命週期
"""
import json
import os
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path

from student_memory import StudentMemoryTracker
from rag_engine import GraphRAG


class CourseSession:
    """
    課堂會話（單一學生）

    負責：
    1. 課程開始時載入資料到記憶體
    2. 課程進行中維護快取
    3. 課程結束時儲存並清空記憶體
    """

    def __init__(
        self,
        session_id: str,
        course_id: str,
        student_id: str,
        data_dir: str = "./data"
    ):
        """
        初始化課堂會話

        Args:
            session_id: 會話 ID（例如："2025-12-03-14:00"）
            course_id: 課程 ID
            student_id: 學生 ID
            data_dir: 資料目錄
        """
        self.session_id = session_id
        self.course_id = course_id
        self.student_id = student_id
        self.data_dir = Path(data_dir)

        # 確保資料目錄存在
        self.students_dir = self.data_dir / "students"
        self.courses_dir = self.data_dir / "courses"
        self.students_dir.mkdir(parents=True, exist_ok=True)
        self.courses_dir.mkdir(parents=True, exist_ok=True)

        # 記憶體快取
        self.rag_engine: Optional[GraphRAG] = None
        self.student_tracker: Optional[StudentMemoryTracker] = None

        # 會話狀態
        self.is_active = False
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        # 統計資訊
        self.stats = {
            "queries": 0,
            "memory_updates": 0,
            "cache_hits": 0
        }

    def start_session(self, pdf_path: Optional[str] = None):
        """
        開始課堂會話（載入資料到記憶體）

        Args:
            pdf_path: 課程講義 PDF 路徑（若有）
        """
        print(f"\n{'='*60}")
        print(f"開始課堂會話: {self.session_id}")
        print(f"課程 ID: {self.course_id}")
        print(f"學生 ID: {self.student_id}")
        print(f"{'='*60}\n")

        self.start_time = datetime.now()

        # 1. 載入 GraphRAG 引擎
        print("步驟 1/3: 載入 GraphRAG 引擎...")
        self.rag_engine = GraphRAG()

        if pdf_path and os.path.exists(pdf_path):
            print(f"  解析課程講義: {pdf_path}")
            self.rag_engine.ingest_pdf(pdf_path)
        else:
            # 嘗試從快取載入
            cache_path = self.courses_dir / f"{self.course_id}_rag_cache.json"
            if cache_path.exists():
                print(f"  從快取載入: {cache_path}")
                # TODO: 實作 RAG 快取載入
            else:
                print("  ⚠️  警告：沒有課程講義，RAG 功能將受限")

        # 2. 載入學生記憶追蹤器
        print("\n步驟 2/3: 載入學生記憶追蹤器...")
        student_file = self.students_dir / f"{self.student_id}.json"

        if student_file.exists():
            # 從硬碟載入
            print(f"  載入學生資料: {self.student_id} (從硬碟)")
            self.student_tracker = StudentMemoryTracker.load_from_file(str(student_file))
        else:
            # 新學生
            print(f"  建立新追蹤器: {self.student_id}")
            self.student_tracker = StudentMemoryTracker(student_id=self.student_id)

        # 3. 標記會話為活躍
        self.is_active = True

        # 估算記憶體使用
        memory_usage = self._estimate_memory_usage()

        print("\n步驟 3/3: 會話啟動完成")
        print(f"  估計記憶體使用: {memory_usage['total_mb']:.1f} MB")
        print(f"    - GraphRAG: {memory_usage['rag_mb']:.1f} MB")
        print(f"    - 學生追蹤: {memory_usage['student_mb']:.2f} MB")
        print(f"\n✓ 課堂會話已啟動，可以開始學習\n")

    def end_session(self):
        """
        結束課堂會話（儲存資料並清空記憶體）
        """
        if not self.is_active:
            print("⚠️  會話未啟動，無需結束")
            return

        print(f"\n{'='*60}")
        print(f"結束課堂會話: {self.session_id}")
        print(f"{'='*60}\n")

        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds() / 60  # 分鐘

        # 1. 儲存學生資料
        print("步驟 1/3: 儲存學生資料到硬碟...")
        if self.student_tracker:
            student_file = self.students_dir / f"{self.student_id}.json"
            self.student_tracker.save_to_file(str(student_file))
            print(f"  儲存 {self.student_id}")

        # 2. 儲存 GraphRAG 快取（可選）
        print("\n步驟 2/3: 儲存 GraphRAG 快取...")
        cache_path = self.courses_dir / f"{self.course_id}_rag_cache.json"
        # TODO: 實作 RAG 快取儲存
        print("  （暫時跳過）")

        # 3. 清空記憶體
        print("\n步驟 3/3: 清空記憶體...")
        self.rag_engine = None
        self.student_tracker = None
        self.is_active = False

        # 輸出統計
        print(f"\n會話統計：")
        print(f"  課程時長: {duration:.1f} 分鐘")
        print(f"  查詢次數: {self.stats['queries']}")
        print(f"  記憶更新: {self.stats['memory_updates']}")
        print(f"  快取命中: {self.stats['cache_hits']}")
        print(f"  平均查詢頻率: {self.stats['queries'] / max(duration, 1):.1f} 次/分鐘")
        print(f"\n✓ 課堂會話已結束，記憶體已清空\n")

    def query_knowledge(self, query: str) -> Dict[str, Any]:
        """
        查詢知識（從記憶體快取）

        Args:
            query: 查詢字串

        Returns:
            查詢結果
        """
        if not self.is_active:
            raise RuntimeError("會話未啟動，請先呼叫 start_session()")

        self.stats["queries"] += 1

        # 從記憶體查詢（快！）
        if self.rag_engine:
            results = self.rag_engine.hybrid_search(query, top_k=3)
            self.stats["cache_hits"] += 1
        else:
            results = {"vector_results": [], "graph_results": []}

        # 獲取學生的記憶狀態
        if self.student_tracker:
            progress = self.student_tracker.get_learning_progress()
        else:
            progress = None

        return {
            "query": query,
            "rag_results": results,
            "student_progress": progress,
            "from_cache": True
        }

    def update_student_memory(
        self,
        concept: str,
        score: int
    ) -> Dict[str, Any]:
        """
        更新學生記憶狀態

        Args:
            concept: 概念
            score: 評分（0-5）

        Returns:
            更新結果
        """
        if not self.is_active:
            raise RuntimeError("會話未啟動")

        if not self.student_tracker:
            raise RuntimeError("學生追蹤器未初始化")

        result = self.student_tracker.record_quiz_result(concept, score)
        self.stats["memory_updates"] += 1

        return result

    def get_student_progress(self) -> Dict[str, Any]:
        """
        獲取學生學習進度

        Returns:
            學習進度資訊
        """
        if not self.is_active or not self.student_tracker:
            raise RuntimeError("會話未啟動或追蹤器未初始化")

        return self.student_tracker.get_learning_progress()

    def _estimate_memory_usage(self) -> Dict[str, float]:
        """
        估算記憶體使用量（MB）
        """
        # GraphRAG（粗略估算）
        rag_mb = 1000.0  # 約 1GB（向量索引 + 知識圖譜）

        # 學生追蹤器
        # 假設 500 個概念 × 200 bytes = 100KB
        student_mb = 0.1

        total_mb = rag_mb + student_mb

        return {
            "rag_mb": rag_mb,
            "student_mb": student_mb,
            "total_mb": total_mb
        }

    def get_session_info(self) -> Dict[str, Any]:
        """
        獲取會話資訊
        """
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
        else:
            duration = 0

        return {
            "session_id": self.session_id,
            "course_id": self.course_id,
            "student_id": self.student_id,
            "is_active": self.is_active,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_minutes": duration / 60,
            "stats": self.stats
        }


# 測試函數
def test_session_manager():
    """測試會話管理器"""
    print("=== 測試課堂會話管理器（單一學生）===\n")

    # 創建會話
    session = CourseSession(
        session_id="2025-12-03-14:00",
        course_id="deep_learning_101",
        student_id="student_001"
    )

    # 開始會話
    session.start_session()

    # 模擬課程進行
    print("模擬課程進行中...\n")

    # 學生答題
    print("學生答題：卷積神經網路")
    result = session.update_student_memory("卷積神經網路", score=4)
    print(f"  記憶強度: {result['new_strength']:.2f}")

    # 學生查詢
    print("\n學生查詢：反向傳播")
    query_result = session.query_knowledge("反向傳播")
    print(f"  查詢結果: {len(query_result['rag_results'].get('vector_results', []))} 個向量匹配")

    # 更多答題
    print("\n繼續答題...")
    session.update_student_memory("Dropout", score=5)
    session.update_student_memory("反向傳播", score=2)  # 較弱
    session.update_student_memory("批次標準化", score=4)

    # 查看學習進度
    print("\n學生學習進度：")
    progress = session.get_student_progress()
    print(f"  總概念數: {progress['total_concepts']}")
    print(f"  平均記憶強度: {progress['average_memory_strength']:.2f}")
    print(f"  需要複習的概念: {len(progress['need_review'])}")

    if progress['need_review']:
        print("\n  需要複習：")
        for concept in progress['need_review'][:3]:
            print(f"    - {concept['name']}: 強度 {concept['memory_strength']:.2f}")

    # 查看會話資訊
    print("\n會話資訊：")
    info = session.get_session_info()
    print(f"  進行時長: {info['duration_minutes']:.2f} 分鐘")
    print(f"  查詢次數: {info['stats']['queries']}")
    print(f"  記憶更新: {info['stats']['memory_updates']}")

    # 結束會話
    import time
    time.sleep(1)  # 模擬課程時間
    session.end_session()

    print("\n=== 測試完成 ===")


if __name__ == "__main__":
    test_session_manager()
