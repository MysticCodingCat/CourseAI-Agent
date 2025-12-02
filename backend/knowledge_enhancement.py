"""
知識增強系統
整合 PPT 解析、Web 搜尋、內容過濾與 RAG 更新
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from ppt_parser import PPTParser
from agents.web_search import WebSearchAgent, ContentFilterAgent
from rag_engine import GraphRAG


class KnowledgeEnhancementSystem:
    """
    知識增強系統

    完整流程：
    1. 解析 PPT，生成講義大綱
    2. 識別需要補充的主題
    3. 網路搜尋相關資料
    4. 過濾與挑選內容
    5. 加入 RAG 知識庫
    """

    def __init__(
        self,
        google_api_key: Optional[str] = None,
        google_cx: Optional[str] = None
    ):
        """
        初始化系統

        Args:
            google_api_key: Google API Key（可選）
            google_cx: Google Custom Search Engine ID（可選）
        """
        self.ppt_parser = PPTParser()
        self.web_search_agent = WebSearchAgent(google_api_key, google_cx)
        self.content_filter = ContentFilterAgent()
        self.rag_engine: Optional[GraphRAG] = None

        self.enhancement_log = []  # 記錄增強過程

    def process_ppt(
        self,
        ppt_path: str,
        enable_web_enhancement: bool = True,
        use_api: bool = False
    ) -> Dict[str, Any]:
        """
        完整處理 PPT

        Args:
            ppt_path: PPT 檔案路徑
            enable_web_enhancement: 是否啟用網路增強
            use_api: 是否使用 API（False = 用套件）

        Returns:
            處理結果
        """
        print(f"\n{'='*60}")
        print(f"知識增強系統 - 處理 PPT")
        print(f"{'='*60}\n")

        # 步驟 1：解析 PPT
        print("[步驟 1/5] 解析 PPT...")
        slides_data = self.ppt_parser.parse_ppt(ppt_path)

        # 步驟 2：預測結構
        print("\n[步驟 2/5] 預測結構...")
        structure = self.ppt_parser.predict_structure()

        # 步驟 3：生成 Markdown 大綱
        print("\n[步驟 3/5] 生成講義大綱...")
        markdown_outline = self.ppt_parser.generate_outline_markdown()

        # 儲存大綱
        outline_path = ppt_path.replace('.pptx', '_outline.md')
        with open(outline_path, 'w', encoding='utf-8') as f:
            f.write(markdown_outline)
        print(f"  → 大綱已儲存: {outline_path}")

        # 步驟 4：識別需要增強的主題
        print("\n[步驟 4/5] 識別需要增強的主題...")
        topics = self.ppt_parser.identify_topics_for_enhancement()

        enhanced_topics = []

        if enable_web_enhancement and topics:
            print(f"  → 找到 {len(topics)} 個主題")

            # 步驟 5：網路增強
            print("\n[步驟 5/5] 網路搜尋與增強...")

            for i, topic in enumerate(topics[:10], 1):  # 最多處理 10 個主題
                print(f"\n  處理主題 {i}/{min(len(topics), 10)}: {topic['keyword']}")

                # 搜尋並抓取
                search_results = self.web_search_agent.search_and_fetch(
                    query=f"{topic['keyword']} 教學 說明",
                    num_results=3,
                    use_api=use_api
                )

                if not search_results:
                    print(f"    → 未找到相關資料")
                    continue

                # 過濾內容
                filtered_results = []
                for content in search_results:
                    filtered = self.content_filter.filter_content(
                        content,
                        target_keyword=topic['keyword']
                    )
                    filtered_results.append(filtered)

                # 選擇最佳內容
                best_contents = self.content_filter.select_best_content(
                    filtered_results,
                    top_k=2
                )

                # 記錄
                enhanced_topics.append({
                    "topic": topic,
                    "enhanced_content": best_contents
                })

                print(f"    → 找到 {len(best_contents)} 個高品質來源")

        else:
            print("\n[步驟 5/5] 網路增強已跳過")

        # 整理結果
        result = {
            "ppt_path": ppt_path,
            "slides_count": len(slides_data),
            "structure": structure,
            "markdown_outline": markdown_outline,
            "outline_path": outline_path,
            "topics_identified": len(topics),
            "topics_enhanced": len(enhanced_topics),
            "enhanced_topics": enhanced_topics
        }

        print(f"\n{'='*60}")
        print("處理完成")
        print(f"{'='*60}")
        print(f"投影片數: {result['slides_count']}")
        print(f"章節數: {len(structure['chapters'])}")
        print(f"識別主題: {result['topics_identified']}")
        print(f"增強主題: {result['topics_enhanced']}")
        print(f"講義大綱: {result['outline_path']}")

        return result

    def add_to_rag(self, enhanced_topics: List[Dict[str, Any]]):
        """
        將增強的內容加入 RAG 知識庫

        Args:
            enhanced_topics: 增強的主題列表
        """
        if not self.rag_engine:
            self.rag_engine = GraphRAG()

        print(f"\n[RAG] 加入 {len(enhanced_topics)} 個增強主題到知識庫...")

        # 準備文本塊
        chunks = []

        for item in enhanced_topics:
            topic = item["topic"]
            keyword = topic["keyword"]

            for content in item["enhanced_content"]:
                for para in content.get("filtered_paragraphs", []):
                    chunks.append({
                        "text": para["text"],
                        "source": content["url"],
                        "keyword": keyword,
                        "relevance_score": para["relevance_score"]
                    })

        if not chunks:
            print("[RAG] 沒有內容可加入")
            return

        # 建立向量索引
        print(f"[RAG] 建立向量索引（{len(chunks)} 個文本塊）...")
        self.rag_engine.build_vector_index(chunks)

        # 建立知識圖譜
        print(f"[RAG] 建立知識圖譜...")
        self.rag_engine.build_knowledge_graph(chunks, sample_rate=0.5)

        print(f"[RAG] 完成")

    def generate_enhanced_markdown(
        self,
        result: Dict[str, Any],
        output_path: str
    ):
        """
        生成增強版 Markdown 講義

        Args:
            result: process_ppt 的返回結果
            output_path: 輸出檔案路徑
        """
        print(f"\n[Markdown] 生成增強版講義...")

        lines = []

        # 標題
        structure = result["structure"]
        lines.append(f"# {structure.get('title', '課程講義')}\n")
        lines.append("*由 CourseAI 自動生成*\n")
        lines.append("\n---\n")

        # 各章節
        enhanced_topics_dict = {
            item["topic"]["keyword"]: item["enhanced_content"]
            for item in result["enhanced_topics"]
        }

        for chapter in structure["chapters"]:
            lines.append(f"\n## {chapter['title']}\n")

            for slide_info in chapter["slides"]:
                slide_num = slide_info["slide_number"]
                slide_data = self.ppt_parser.slides_data[slide_num - 1]

                lines.append(f"\n### {slide_data['title']}\n")
                lines.append(f"*投影片 {slide_num}*\n")

                # 原始內容
                if slide_data["content"]:
                    lines.append("\n**投影片內容：**\n")
                    for line in slide_data["content"][:5]:
                        lines.append(f"- {line}\n")

                # 關鍵詞
                keywords = self.ppt_parser.extract_keywords(slide_data)
                if keywords:
                    lines.append(f"\n**關鍵詞：** {', '.join(keywords[:5])}\n")

                # 增強內容
                for keyword in keywords[:3]:  # 最多 3 個關鍵詞
                    if keyword in enhanced_topics_dict:
                        lines.append(f"\n#### 補充資料：{keyword}\n")

                        for content in enhanced_topics_dict[keyword][:2]:  # 最多 2 個來源
                            lines.append(f"\n**來源：** [{content['title']}]({content['url']})\n")

                            for para in content.get("filtered_paragraphs", [])[:3]:
                                lines.append(f"\n{para['text']}\n")

                lines.append("\n---\n")

        # 寫入檔案
        markdown_text = "".join(lines)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)

        print(f"[Markdown] 增強版講義已儲存: {output_path}")
        print(f"           總長度: {len(markdown_text)} 字元")


# 測試函數
def test_knowledge_enhancement():
    """測試知識增強系統"""
    print("=== 測試知識增強系統 ===\n")

    # 創建系統
    system = KnowledgeEnhancementSystem()

    print("提示：")
    print("1. 準備一個測試用的 PPT 檔案")
    print("2. 使用：")
    print("   result = system.process_ppt('test.pptx', enable_web_enhancement=True)")
    print("   system.add_to_rag(result['enhanced_topics'])")
    print("   system.generate_enhanced_markdown(result, 'enhanced_lecture.md')")
    print("\n3. （可選）如果要使用 Google API：")
    print("   system = KnowledgeEnhancementSystem(")
    print("       google_api_key='YOUR_KEY',")
    print("       google_cx='YOUR_CX'")
    print("   )")


if __name__ == "__main__":
    test_knowledge_enhancement()
