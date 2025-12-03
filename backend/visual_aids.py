"""
視覺輔助功能
圖片搜尋 + 概念圖生成
"""
from typing import Dict, List, Optional, Any, Tuple
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse
import networkx as nx
import json
import base64
from pathlib import Path


class ImageSearchAgent:
    """
    圖片搜尋代理

    功能：
    1. 搜尋教學相關圖片
    2. 過濾低品質圖片
    3. 下載並快取圖片
    """

    def __init__(self, cache_dir: str = "./image_cache"):
        """
        初始化圖片搜尋代理

        Args:
            cache_dir: 圖片快取目錄
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def search_images(
        self,
        query: str,
        num_results: int = 5,
        image_type: str = "diagram"  # diagram, photo, illustration
    ) -> List[Dict[str, Any]]:
        """
        搜尋圖片

        Args:
            query: 搜尋關鍵字
            num_results: 返回結果數量
            image_type: 圖片類型

        Returns:
            圖片資訊列表
        """
        print(f"[ImageSearch] 搜尋圖片: {query}")

        # 根據類型調整搜尋詞
        search_query = self._enhance_query(query, image_type)

        # 使用 Google Images 搜尋
        search_url = f"https://www.google.com/search?q={quote_plus(search_query)}&tbm=isch"

        try:
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 解析圖片結果
            images = []
            img_tags = soup.find_all('img')

            for img in img_tags[:num_results * 2]:  # 多抓一些，之後過濾
                src = img.get('src') or img.get('data-src')

                if not src or not src.startswith('http'):
                    continue

                # 基本資訊
                image_info = {
                    "url": src,
                    "alt": img.get('alt', ''),
                    "width": img.get('width'),
                    "height": img.get('height'),
                    "source_page": search_url
                }

                # 簡單過濾
                if self._is_valid_image(image_info):
                    images.append(image_info)

                if len(images) >= num_results:
                    break

            print(f"[ImageSearch] 找到 {len(images)} 張圖片")
            return images

        except Exception as e:
            print(f"[ImageSearch] 搜尋失敗: {e}")
            return []

    def _enhance_query(self, query: str, image_type: str) -> str:
        """
        增強搜尋詞

        Args:
            query: 原始查詢
            image_type: 圖片類型

        Returns:
            增強後的查詢
        """
        enhancements = {
            "diagram": f"{query} diagram explanation",
            "photo": f"{query} photo",
            "illustration": f"{query} illustration infographic"
        }

        return enhancements.get(image_type, query)

    def _is_valid_image(self, image_info: Dict[str, Any]) -> bool:
        """
        檢查圖片是否有效

        Args:
            image_info: 圖片資訊

        Returns:
            True = 有效
        """
        url = image_info.get("url", "")

        # 過濾 Google logo 等
        if any(skip in url.lower() for skip in ['logo', 'icon', 'avatar', 'button']):
            return False

        # 檢查尺寸（如果有的話）
        try:
            width = int(image_info.get("width", 0))
            height = int(image_info.get("height", 0))

            # 過濾太小的圖片
            if width > 0 and height > 0:
                if width < 200 or height < 200:
                    return False
        except:
            pass

        return True

    def download_image(
        self,
        url: str,
        filename: Optional[str] = None
    ) -> Optional[str]:
        """
        下載圖片到快取

        Args:
            url: 圖片 URL
            filename: 檔案名稱（可選）

        Returns:
            本地檔案路徑（如果成功）
        """
        if not filename:
            # 從 URL 生成檔名
            filename = f"{hash(url)}.jpg"

        local_path = self.cache_dir / filename

        # 如果已存在，直接返回
        if local_path.exists():
            return str(local_path)

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            with open(local_path, 'wb') as f:
                f.write(response.content)

            print(f"[ImageSearch] 圖片已下載: {filename}")
            return str(local_path)

        except Exception as e:
            print(f"[ImageSearch] 下載失敗 ({url}): {e}")
            return None


class ConceptMapGenerator:
    """
    概念圖生成器

    功能：
    1. 從知識圖譜生成概念關係圖
    2. 導出為多種格式（JSON, DOT, 圖片）
    """

    def __init__(self):
        """初始化概念圖生成器"""
        pass

    def generate_from_knowledge_graph(
        self,
        knowledge_graph: nx.DiGraph,
        central_concept: str,
        max_depth: int = 2
    ) -> nx.DiGraph:
        """
        從知識圖譜生成概念圖

        Args:
            knowledge_graph: 知識圖譜（來自 GraphRAG）
            central_concept: 中心概念
            max_depth: 最大深度（幾跳以內）

        Returns:
            概念圖（子圖）
        """
        print(f"[ConceptMap] 生成概念圖: {central_concept} (深度 {max_depth})")

        # 如果中心概念不在圖中，返回空圖
        if central_concept not in knowledge_graph.nodes():
            print(f"[ConceptMap] 警告：'{central_concept}' 不在知識圖譜中")
            return nx.DiGraph()

        # BFS 找出指定深度內的所有節點
        nodes_to_include = {central_concept}
        current_level = {central_concept}

        for depth in range(max_depth):
            next_level = set()

            for node in current_level:
                # 後繼節點
                successors = set(knowledge_graph.successors(node))
                next_level.update(successors)

                # 前驅節點
                predecessors = set(knowledge_graph.predecessors(node))
                next_level.update(predecessors)

            nodes_to_include.update(next_level)
            current_level = next_level

        # 創建子圖
        concept_map = knowledge_graph.subgraph(nodes_to_include).copy()

        # 添加元數據
        concept_map.graph['central_concept'] = central_concept
        concept_map.graph['max_depth'] = max_depth

        print(f"[ConceptMap] 生成完成 - {len(concept_map.nodes())} 個概念, {len(concept_map.edges())} 個關係")

        return concept_map

    def generate_from_concepts(
        self,
        concepts: List[str],
        relationships: Optional[List[Tuple[str, str, str]]] = None
    ) -> nx.DiGraph:
        """
        從概念列表手動生成概念圖

        Args:
            concepts: 概念列表
            relationships: 關係列表 [(from, to, relation), ...]

        Returns:
            概念圖
        """
        print(f"[ConceptMap] 從 {len(concepts)} 個概念生成概念圖")

        concept_map = nx.DiGraph()

        # 添加節點
        for concept in concepts:
            concept_map.add_node(concept)

        # 添加邊
        if relationships:
            for from_node, to_node, relation in relationships:
                if from_node in concept_map.nodes() and to_node in concept_map.nodes():
                    concept_map.add_edge(from_node, to_node, relation=relation)

        return concept_map

    def export_to_json(self, concept_map: nx.DiGraph) -> Dict[str, Any]:
        """
        導出為 JSON 格式

        Args:
            concept_map: 概念圖

        Returns:
            JSON 資料
        """
        data = {
            "nodes": [],
            "edges": [],
            "metadata": concept_map.graph
        }

        # 節點
        for node in concept_map.nodes():
            data["nodes"].append({
                "id": node,
                "label": node
            })

        # 邊
        for from_node, to_node, edge_data in concept_map.edges(data=True):
            data["edges"].append({
                "from": from_node,
                "to": to_node,
                "relation": edge_data.get("relation", "related_to")
            })

        return data

    def export_to_dot(self, concept_map: nx.DiGraph) -> str:
        """
        導出為 DOT 格式（Graphviz）

        Args:
            concept_map: 概念圖

        Returns:
            DOT 字符串
        """
        lines = ["digraph ConceptMap {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box, style=rounded];")

        # 節點
        for node in concept_map.nodes():
            lines.append(f'  "{node}";')

        # 邊
        for from_node, to_node, edge_data in concept_map.edges(data=True):
            relation = edge_data.get("relation", "related_to")
            lines.append(f'  "{from_node}" -> "{to_node}" [label="{relation}"];')

        lines.append("}")

        return "\n".join(lines)

    def save_to_file(
        self,
        concept_map: nx.DiGraph,
        output_path: str,
        format: str = "json"
    ):
        """
        儲存概念圖到檔案

        Args:
            concept_map: 概念圖
            output_path: 輸出檔案路徑
            format: 格式（json, dot）
        """
        if format == "json":
            data = self.export_to_json(concept_map)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        elif format == "dot":
            dot_text = self.export_to_dot(concept_map)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(dot_text)

        print(f"[ConceptMap] 概念圖已儲存: {output_path}")


# 測試函數
def test_visual_aids():
    """測試視覺輔助功能"""
    print("="*60)
    print("測試視覺輔助功能")
    print("="*60 + "\n")

    # 測試 1: 圖片搜尋
    print("[測試 1] 圖片搜尋")
    image_search = ImageSearchAgent()

    images = image_search.search_images("卷積神經網路", num_results=3)
    print(f"  找到 {len(images)} 張圖片")

    if images:
        print("\n  前 2 張圖片:")
        for i, img in enumerate(images[:2], 1):
            print(f"    {i}. URL: {img['url'][:60]}...")
            print(f"       Alt: {img['alt']}")

    # 測試 2: 概念圖生成（手動）
    print("\n[測試 2] 概念圖生成（手動）")
    concept_gen = ConceptMapGenerator()

    concepts = ["深度學習", "CNN", "卷積層", "池化層", "全連接層"]
    relationships = [
        ("深度學習", "CNN", "包含"),
        ("CNN", "卷積層", "組成部分"),
        ("CNN", "池化層", "組成部分"),
        ("CNN", "全連接層", "組成部分")
    ]

    concept_map = concept_gen.generate_from_concepts(concepts, relationships)
    print(f"  概念數: {len(concept_map.nodes())}")
    print(f"  關係數: {len(concept_map.edges())}")

    # 導出 JSON
    json_data = concept_gen.export_to_json(concept_map)
    print(f"\n  JSON 格式:")
    print(f"    節點: {len(json_data['nodes'])}")
    print(f"    邊: {len(json_data['edges'])}")

    # 儲存
    concept_gen.save_to_file(concept_map, "test_concept_map.json", format="json")
    concept_gen.save_to_file(concept_map, "test_concept_map.dot", format="dot")

    # 測試 3: 從知識圖譜生成（需要 GraphRAG）
    print("\n[測試 3] 從知識圖譜生成概念圖")
    print("  （需要先運行 GraphRAG 建立知識圖譜）")

    # 模擬一個小的知識圖譜
    mock_kg = nx.DiGraph()
    mock_kg.add_edge("梯度下降", "優化演算法", relation="是一種")
    mock_kg.add_edge("梯度下降", "SGD", relation="包含")
    mock_kg.add_edge("梯度下降", "Adam", relation="包含")
    mock_kg.add_edge("SGD", "Mini-batch", relation="變種")

    concept_map_from_kg = concept_gen.generate_from_knowledge_graph(
        mock_kg,
        central_concept="梯度下降",
        max_depth=1
    )

    print(f"  從知識圖譜提取:")
    print(f"    概念數: {len(concept_map_from_kg.nodes())}")
    print(f"    關係數: {len(concept_map_from_kg.edges())}")

    print("\n" + "="*60)
    print("測試完成")
    print("="*60)
    print("\n生成的檔案:")
    print("  - test_concept_map.json")
    print("  - test_concept_map.dot (可用 Graphviz 渲染)")


if __name__ == "__main__":
    test_visual_aids()
