"""
智慧講義生成器
課程進行時增量更新講義內容
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json
import re


class LectureNoteGenerator:
    """
    智慧講義生成器

    功能：
    1. 從 PPT 生成初步大綱（空白模板）
    2. 課程進行時增量填充內容
    3. 記錄 Q&A 對話
    4. 補充概念說明
    5. 生成完整版講義
    """

    def __init__(self, course_id: str, session_id: str):
        """
        初始化講義生成器

        Args:
            course_id: 課程 ID
            session_id: 會話 ID
        """
        self.course_id = course_id
        self.session_id = session_id

        # 講義結構
        self.title = ""
        self.chapters: List[Dict[str, Any]] = []

        # 增量內容記錄
        self.qa_pairs: List[Dict[str, Any]] = []  # Q&A 對話
        self.concept_explanations: List[Dict[str, Any]] = []  # 概念補充
        self.timestamps: List[Dict[str, Any]] = []  # 時間戳記錄

        # 當前章節追蹤
        self.current_chapter_index = 0
        self.current_slide_number = 1

        # 元數據
        self.metadata = {
            "course_id": course_id,
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }

    def initialize_from_ppt(
        self,
        ppt_data: Dict[str, Any],
        structure: Dict[str, Any]
    ):
        """
        從 PPT 解析結果初始化講義大綱

        Args:
            ppt_data: PPT 解析資料（來自 PPTParser）
            structure: PPT 結構資料
        """
        print(f"[LectureNote] 初始化講義大綱...")

        self.title = structure.get("title", "課程講義")

        # 為每個章節創建空白模板
        for chapter in structure.get("chapters", []):
            chapter_data = {
                "title": chapter["title"],
                "slides": [],
                "qa_section": [],  # 本章節的 Q&A
                "supplementary": []  # 本章節的補充說明
            }

            # 為每張投影片創建佔位符
            for slide_info in chapter.get("slides", []):
                slide_data = {
                    "slide_number": slide_info["slide_number"],
                    "title": slide_info["title"],
                    "slide_type": slide_info["type"],
                    "content_filled": False,  # 是否已填充內容
                    "fill_timestamp": None,
                    "questions_asked": []  # 此投影片相關的問題
                }
                chapter_data["slides"].append(slide_data)

            self.chapters.append(chapter_data)

        print(f"[LectureNote] 大綱初始化完成 - {len(self.chapters)} 個章節")

    def set_current_slide(self, slide_number: int):
        """
        設置當前投影片（追蹤課程進度）

        Args:
            slide_number: 投影片編號
        """
        self.current_slide_number = slide_number

        # 找到對應的章節
        for i, chapter in enumerate(self.chapters):
            for slide in chapter["slides"]:
                if slide["slide_number"] == slide_number:
                    self.current_chapter_index = i
                    break

        # 記錄時間戳
        self.timestamps.append({
            "slide_number": slide_number,
            "timestamp": datetime.now().isoformat(),
            "event": "slide_changed"
        })

    def append_qa_pair(
        self,
        question: str,
        answer: str,
        concept: Optional[str] = None,
        slide_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        記錄 Q&A 對話到講義

        Args:
            question: 學生問題
            answer: AI 回答
            concept: 相關概念（可選）
            slide_number: 投影片編號（可選，預設為當前投影片）

        Returns:
            記錄結果
        """
        if slide_number is None:
            slide_number = self.current_slide_number

        qa_entry = {
            "question": question,
            "answer": answer,
            "concept": concept,
            "slide_number": slide_number,
            "chapter_index": self.current_chapter_index,
            "timestamp": datetime.now().isoformat()
        }

        self.qa_pairs.append(qa_entry)

        # 加到對應章節
        if 0 <= self.current_chapter_index < len(self.chapters):
            self.chapters[self.current_chapter_index]["qa_section"].append(qa_entry)

            # 標記投影片有問題被問
            for slide in self.chapters[self.current_chapter_index]["slides"]:
                if slide["slide_number"] == slide_number:
                    slide["questions_asked"].append(question)
                    break

        self.metadata["last_updated"] = datetime.now().isoformat()

        print(f"[LectureNote] 記錄 Q&A: {question[:30]}...")

        return qa_entry

    def append_concept_explanation(
        self,
        concept: str,
        explanation: str,
        source: str = "web_search",
        slide_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        補充概念說明到講義

        Args:
            concept: 概念名稱
            explanation: 說明內容
            source: 來源（web_search, rag, manual）
            slide_number: 投影片編號（可選）

        Returns:
            記錄結果
        """
        if slide_number is None:
            slide_number = self.current_slide_number

        explanation_entry = {
            "concept": concept,
            "explanation": explanation,
            "source": source,
            "slide_number": slide_number,
            "chapter_index": self.current_chapter_index,
            "timestamp": datetime.now().isoformat()
        }

        self.concept_explanations.append(explanation_entry)

        # 加到對應章節
        if 0 <= self.current_chapter_index < len(self.chapters):
            self.chapters[self.current_chapter_index]["supplementary"].append(explanation_entry)

        self.metadata["last_updated"] = datetime.now().isoformat()

        print(f"[LectureNote] 補充說明: {concept}")

        return explanation_entry

    def mark_slide_filled(self, slide_number: int):
        """
        標記投影片內容已填充

        Args:
            slide_number: 投影片編號
        """
        for chapter in self.chapters:
            for slide in chapter["slides"]:
                if slide["slide_number"] == slide_number:
                    slide["content_filled"] = True
                    slide["fill_timestamp"] = datetime.now().isoformat()
                    break

    def generate_markdown(
        self,
        include_qa: bool = True,
        include_supplementary: bool = True,
        include_metadata: bool = True
    ) -> str:
        """
        生成 Markdown 講義

        Args:
            include_qa: 是否包含 Q&A 區塊
            include_supplementary: 是否包含補充說明
            include_metadata: 是否包含元數據

        Returns:
            Markdown 文本
        """
        print(f"[LectureNote] 生成 Markdown 講義...")

        lines = []

        # 標題
        lines.append(f"# {self.title}\n")

        if include_metadata:
            lines.append(f"*課程 ID: {self.course_id}*\n")
            lines.append(f"*會話 ID: {self.session_id}*\n")
            lines.append(f"*最後更新: {self.metadata['last_updated']}*\n")

        lines.append("\n---\n")

        # 各章節
        for chapter in self.chapters:
            lines.append(f"\n## {chapter['title']}\n")

            # 投影片內容
            for slide in chapter["slides"]:
                lines.append(f"\n### {slide['title']}\n")
                lines.append(f"*投影片 {slide['slide_number']}*\n")

                # 如果有問題被問
                if slide["questions_asked"]:
                    lines.append(f"\n**討論問題數: {len(slide['questions_asked'])}**\n")

                lines.append("\n---\n")

            # Q&A 區塊
            if include_qa and chapter["qa_section"]:
                lines.append(f"\n### 💬 本章節 Q&A\n")

                for i, qa in enumerate(chapter["qa_section"], 1):
                    lines.append(f"\n#### Q{i}: {qa['question']}\n")

                    if qa.get("concept"):
                        lines.append(f"*相關概念: {qa['concept']}*\n")

                    lines.append(f"\n**A{i}:** {qa['answer']}\n")
                    lines.append("\n---\n")

            # 補充說明區塊
            if include_supplementary and chapter["supplementary"]:
                lines.append(f"\n### 📚 補充資料\n")

                for i, supp in enumerate(chapter["supplementary"], 1):
                    lines.append(f"\n#### {supp['concept']}\n")
                    lines.append(f"*來源: {supp['source']}*\n")
                    lines.append(f"\n{supp['explanation']}\n")
                    lines.append("\n---\n")

        # 統計資訊
        if include_metadata:
            lines.append(f"\n## 📊 課程統計\n")
            lines.append(f"- 總問題數: {len(self.qa_pairs)}\n")
            lines.append(f"- 補充概念數: {len(self.concept_explanations)}\n")
            lines.append(f"- 章節數: {len(self.chapters)}\n")

        markdown_text = "".join(lines)

        print(f"[LectureNote] Markdown 生成完成 - {len(markdown_text)} 字元")

        return markdown_text

    def save_to_file(self, output_path: str):
        """
        儲存講義到檔案

        Args:
            output_path: 輸出檔案路徑
        """
        markdown_text = self.generate_markdown()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)

        print(f"[LectureNote] 講義已儲存: {output_path}")

    def save_state(self, state_path: str):
        """
        儲存生成器狀態（用於恢復會話）

        Args:
            state_path: 狀態檔案路徑
        """
        state = {
            "title": self.title,
            "chapters": self.chapters,
            "qa_pairs": self.qa_pairs,
            "concept_explanations": self.concept_explanations,
            "timestamps": self.timestamps,
            "current_chapter_index": self.current_chapter_index,
            "current_slide_number": self.current_slide_number,
            "metadata": self.metadata
        }

        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        print(f"[LectureNote] 狀態已儲存: {state_path}")

    @classmethod
    def load_state(cls, state_path: str) -> 'LectureNoteGenerator':
        """
        從狀態檔案恢復生成器

        Args:
            state_path: 狀態檔案路徑

        Returns:
            LectureNoteGenerator 實例
        """
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)

        instance = cls(
            course_id=state["metadata"]["course_id"],
            session_id=state["metadata"]["session_id"]
        )

        instance.title = state["title"]
        instance.chapters = state["chapters"]
        instance.qa_pairs = state["qa_pairs"]
        instance.concept_explanations = state["concept_explanations"]
        instance.timestamps = state["timestamps"]
        instance.current_chapter_index = state["current_chapter_index"]
        instance.current_slide_number = state["current_slide_number"]
        instance.metadata = state["metadata"]

        print(f"[LectureNote] 狀態已載入: {state_path}")

        return instance

    def get_statistics(self) -> Dict[str, Any]:
        """
        獲取講義統計資訊

        Returns:
            統計資料
        """
        total_slides = sum(len(chapter["slides"]) for chapter in self.chapters)
        filled_slides = sum(
            1 for chapter in self.chapters
            for slide in chapter["slides"]
            if slide["content_filled"]
        )

        return {
            "title": self.title,
            "total_chapters": len(self.chapters),
            "total_slides": total_slides,
            "filled_slides": filled_slides,
            "fill_percentage": (filled_slides / total_slides * 100) if total_slides > 0 else 0,
            "total_qa": len(self.qa_pairs),
            "total_supplementary": len(self.concept_explanations),
            "current_slide": self.current_slide_number,
            "last_updated": self.metadata["last_updated"]
        }


# 測試函數
def test_lecture_note_generator():
    """測試講義生成器"""
    print("="*60)
    print("測試智慧講義生成器")
    print("="*60 + "\n")

    # 創建生成器
    generator = LectureNoteGenerator(
        course_id="deep_learning_101",
        session_id="2025-12-03-14:00"
    )

    # 模擬 PPT 結構
    mock_structure = {
        "title": "深度學習基礎",
        "chapters": [
            {
                "title": "第一章：卷積神經網路",
                "slides": [
                    {"slide_number": 1, "title": "什麼是 CNN？", "type": "content"},
                    {"slide_number": 2, "title": "卷積層", "type": "content"}
                ]
            },
            {
                "title": "第二章：正則化技術",
                "slides": [
                    {"slide_number": 3, "title": "Dropout", "type": "content"},
                    {"slide_number": 4, "title": "批次標準化", "type": "content"}
                ]
            }
        ]
    }

    # 初始化大綱
    print("步驟 1: 初始化講義大綱")
    generator.initialize_from_ppt({}, mock_structure)

    # 模擬課程進行
    print("\n步驟 2: 模擬課程進行...\n")

    # 第 1 張投影片
    generator.set_current_slide(1)
    generator.append_qa_pair(
        question="CNN 的全名是什麼？",
        answer="CNN 的全名是 Convolutional Neural Network（卷積神經網路）。",
        concept="CNN"
    )

    # 第 2 張投影片
    generator.set_current_slide(2)
    generator.append_concept_explanation(
        concept="卷積層運作原理",
        explanation="卷積層使用可學習的濾波器在輸入上滑動，提取局部特徵。",
        source="web_search"
    )

    # 第 3 張投影片
    generator.set_current_slide(3)
    generator.append_qa_pair(
        question="Dropout 的作用是什麼？",
        answer="Dropout 是一種正則化技術，隨機丟棄神經元以防止過擬合。",
        concept="Dropout"
    )

    # 查看統計
    print("\n步驟 3: 查看統計資訊")
    stats = generator.get_statistics()
    print(f"  總章節數: {stats['total_chapters']}")
    print(f"  總投影片數: {stats['total_slides']}")
    print(f"  Q&A 數量: {stats['total_qa']}")
    print(f"  補充說明數: {stats['total_supplementary']}")

    # 生成 Markdown
    print("\n步驟 4: 生成 Markdown 講義")
    markdown = generator.generate_markdown()

    # 儲存
    output_path = "test_lecture_note.md"
    generator.save_to_file(output_path)

    # 儲存狀態
    state_path = "test_lecture_note_state.json"
    generator.save_state(state_path)

    print("\n" + "="*60)
    print("測試完成")
    print("="*60)
    print(f"生成的講義: {output_path}")
    print(f"狀態檔案: {state_path}")


if __name__ == "__main__":
    test_lecture_note_generator()
