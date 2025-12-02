"""
Web Search Agent - 網路搜尋代理
負責搜尋相關資料並補充到 RAG 知識庫
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import time
import re
from urllib.parse import quote_plus, urlparse
import os


class WebSearchAgent:
    """
    網路搜尋代理

    功能：
    1. 使用 Google 搜尋（優先用套件抓取，必要時用 API）
    2. 抓取網頁內容
    3. 清理與提取有用資訊
    """

    def __init__(self, google_api_key: Optional[str] = None, google_cx: Optional[str] = None):
        """
        初始化搜尋代理

        Args:
            google_api_key: Google Custom Search API Key（可選）
            google_cx: Google Custom Search Engine ID（可選）
        """
        self.google_api_key = google_api_key
        self.google_cx = google_cx
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def search(
        self,
        query: str,
        num_results: int = 5,
        use_api: bool = False
    ) -> List[Dict[str, str]]:
        """
        搜尋相關網頁

        Args:
            query: 搜尋關鍵字
            num_results: 返回結果數量
            use_api: 是否使用 API（False = 用套件抓取）

        Returns:
            搜尋結果列表 [{"title": ..., "url": ..., "snippet": ...}, ...]
        """
        print(f"[WebSearch] 搜尋: {query}")

        if use_api and self.google_api_key:
            return self._search_via_api(query, num_results)
        else:
            return self._search_via_scraping(query, num_results)

    def _search_via_api(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """
        使用 Google Custom Search API 搜尋
        """
        if not self.google_api_key or not self.google_cx:
            print("[WebSearch] 警告：缺少 API key 或 CX，改用爬蟲")
            return self._search_via_scraping(query, num_results)

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.google_api_key,
            "cx": self.google_cx,
            "q": query,
            "num": min(num_results, 10)  # API 限制最多 10
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })

            print(f"[WebSearch] API 搜尋完成 - {len(results)} 個結果")
            return results

        except Exception as e:
            print(f"[WebSearch] API 搜尋失敗: {e}")
            return self._search_via_scraping(query, num_results)

    def _search_via_scraping(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """
        使用爬蟲抓取 Google 搜尋結果
        """
        search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={num_results}"

        try:
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            # 解析 Google 搜尋結果
            for g in soup.find_all('div', class_='g'):
                # 標題與連結
                title_element = g.find('h3')
                link_element = g.find('a')

                if not title_element or not link_element:
                    continue

                title = title_element.get_text()
                url = link_element.get('href', '')

                # 清理 URL
                if url.startswith('/url?q='):
                    url = url.split('/url?q=')[1].split('&')[0]

                # 摘要
                snippet_element = g.find('div', class_='VwiC3b')
                snippet = snippet_element.get_text() if snippet_element else ""

                # 過濾無效結果
                if not url.startswith('http'):
                    continue

                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet
                })

                if len(results) >= num_results:
                    break

            print(f"[WebSearch] 爬蟲搜尋完成 - {len(results)} 個結果")
            return results

        except Exception as e:
            print(f"[WebSearch] 爬蟲搜尋失敗: {e}")
            return []

    def fetch_webpage_content(self, url: str) -> Optional[Dict[str, Any]]:
        """
        抓取網頁內容

        Args:
            url: 網頁 URL

        Returns:
            網頁內容 {"url": ..., "title": ..., "text": ..., "paragraphs": [...]}
        """
        print(f"[WebSearch] 抓取網頁: {url}")

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            # 偵測編碼
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.content, 'html.parser')

            # 移除不需要的元素
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
                element.decompose()

            # 提取標題
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""

            # 提取主要內容
            # 優先尋找 article, main 標籤
            main_content = soup.find('article') or soup.find('main') or soup.find('body')

            if not main_content:
                return None

            # 提取段落
            paragraphs = []
            for p in main_content.find_all(['p', 'h1', 'h2', 'h3', 'li']):
                text = p.get_text().strip()
                if len(text) > 30:  # 過濾過短的段落
                    paragraphs.append(text)

            # 完整文字
            full_text = "\n\n".join(paragraphs)

            return {
                "url": url,
                "title": title_text,
                "text": full_text,
                "paragraphs": paragraphs,
                "word_count": len(full_text)
            }

        except Exception as e:
            print(f"[WebSearch] 抓取失敗 ({url}): {e}")
            return None

    def search_and_fetch(
        self,
        query: str,
        num_results: int = 3,
        use_api: bool = False
    ) -> List[Dict[str, Any]]:
        """
        搜尋並抓取網頁內容（一步完成）

        Args:
            query: 搜尋關鍵字
            num_results: 抓取結果數量
            use_api: 是否使用 API

        Returns:
            網頁內容列表
        """
        # 1. 搜尋
        search_results = self.search(query, num_results=num_results * 2, use_api=use_api)

        if not search_results:
            return []

        # 2. 抓取內容
        fetched_contents = []

        for result in search_results:
            # 過濾不想要的網站
            if self._should_skip_url(result["url"]):
                continue

            content = self.fetch_webpage_content(result["url"])

            if content and content["word_count"] > 200:
                # 加入搜尋結果的 snippet
                content["search_snippet"] = result.get("snippet", "")
                fetched_contents.append(content)

            if len(fetched_contents) >= num_results:
                break

            # 禮貌延遲
            time.sleep(1)

        print(f"[WebSearch] 完成 - 抓取了 {len(fetched_contents)} 個網頁")
        return fetched_contents

    def _should_skip_url(self, url: str) -> bool:
        """
        判斷是否應該跳過此 URL

        Returns:
            True = 跳過
        """
        # 跳過的網站類型
        skip_domains = [
            'youtube.com',
            'facebook.com',
            'twitter.com',
            'instagram.com',
            'pinterest.com',
            'reddit.com'  # 可視情況調整
        ]

        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        for skip_domain in skip_domains:
            if skip_domain in domain:
                return True

        # 跳過 PDF（需要特殊處理）
        if url.endswith('.pdf'):
            return True

        return False


class ContentFilterAgent:
    """
    內容過濾代理

    功能：
    1. 分析網頁內容品質
    2. 挑選有用的段落
    3. 過濾廣告、無關內容
    """

    def __init__(self, llm_client=None):
        """
        初始化過濾代理

        Args:
            llm_client: LLM 客戶端（用於智慧過濾）
        """
        self.llm_client = llm_client

    def filter_content(
        self,
        content: Dict[str, Any],
        target_keyword: str
    ) -> Dict[str, Any]:
        """
        過濾網頁內容，只保留相關段落

        Args:
            content: 網頁內容
            target_keyword: 目標關鍵詞

        Returns:
            過濾後的內容
        """
        print(f"[ContentFilter] 過濾內容: {content['title']}")

        paragraphs = content.get("paragraphs", [])

        # 1. 基於關鍵詞的簡單過濾
        relevant_paragraphs = []

        for para in paragraphs:
            # 計算相關性分數
            score = self._calculate_relevance(para, target_keyword)

            if score > 0.3:  # 閾值
                relevant_paragraphs.append({
                    "text": para,
                    "relevance_score": score
                })

        # 按相關性排序
        relevant_paragraphs.sort(key=lambda x: x["relevance_score"], reverse=True)

        # 2. 品質過濾
        quality_paragraphs = []

        for item in relevant_paragraphs[:10]:  # 最多 10 個
            if self._check_quality(item["text"]):
                quality_paragraphs.append(item)

        return {
            "url": content["url"],
            "title": content["title"],
            "filtered_paragraphs": quality_paragraphs,
            "original_count": len(paragraphs),
            "filtered_count": len(quality_paragraphs)
        }

    def _calculate_relevance(self, text: str, keyword: str) -> float:
        """
        計算段落與關鍵詞的相關性

        Returns:
            相關性分數（0-1）
        """
        text_lower = text.lower()
        keyword_lower = keyword.lower()

        # 簡單的 TF 計算
        keyword_count = text_lower.count(keyword_lower)

        if keyword_count == 0:
            return 0.0

        # 歸一化
        score = min(keyword_count / 5, 1.0)  # 最多 5 次就算滿分

        # 加分：如果關鍵詞出現在段落開頭
        if text_lower.startswith(keyword_lower):
            score += 0.2

        return min(score, 1.0)

    def _check_quality(self, text: str) -> bool:
        """
        檢查段落品質

        Returns:
            True = 高品質
        """
        # 過濾規則

        # 1. 長度檢查
        if len(text) < 50 or len(text) > 1000:
            return False

        # 2. 過濾廣告常見詞
        spam_keywords = [
            "點擊",
            "購買",
            "立即",
            "免費",
            "優惠",
            "廣告",
            "贊助",
            "訂閱",
            "關注"
        ]

        spam_count = sum(1 for kw in spam_keywords if kw in text)
        if spam_count >= 3:
            return False

        # 3. 檢查是否有實質內容（不只是連結或導航）
        if text.count("http") > 3:
            return False

        # 4. 檢查是否太多特殊字符
        special_char_count = sum(1 for char in text if not char.isalnum() and char not in "，。、！？；：（）「」")
        if special_char_count / len(text) > 0.3:
            return False

        return True

    def select_best_content(
        self,
        filtered_contents: List[Dict[str, Any]],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        從多個過濾後的內容中選擇最佳的幾個

        Args:
            filtered_contents: 過濾後的內容列表
            top_k: 選擇數量

        Returns:
            最佳內容列表
        """
        print(f"[ContentFilter] 選擇最佳內容 (top {top_k})")

        # 計算每個來源的分數
        scored_contents = []

        for content in filtered_contents:
            score = 0.0

            # 1. 段落數量
            para_count = len(content.get("filtered_paragraphs", []))
            score += min(para_count / 5, 1.0) * 0.4

            # 2. 平均相關性
            paragraphs = content.get("filtered_paragraphs", [])
            if paragraphs:
                avg_relevance = sum(p["relevance_score"] for p in paragraphs) / len(paragraphs)
                score += avg_relevance * 0.6

            scored_contents.append({
                "content": content,
                "score": score
            })

        # 排序
        scored_contents.sort(key=lambda x: x["score"], reverse=True)

        # 返回前 top_k
        return [item["content"] for item in scored_contents[:top_k]]


# 測試函數
def test_web_search():
    """測試網路搜尋"""
    print("=== 測試 Web Search Agent ===\n")

    # 創建代理
    agent = WebSearchAgent()

    # 測試搜尋
    query = "深度學習 卷積神經網路"
    results = agent.search(query, num_results=3)

    print(f"\n搜尋結果（{len(results)}）：")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   摘要: {result['snippet'][:100]}...")
        print()

    # 測試抓取
    if results:
        print("\n測試抓取第一個結果...")
        content = agent.fetch_webpage_content(results[0]["url"])

        if content:
            print(f"標題: {content['title']}")
            print(f"字數: {content['word_count']}")
            print(f"段落數: {len(content['paragraphs'])}")
            print(f"\n前 200 字：")
            print(content['text'][:200])


def test_content_filter():
    """測試內容過濾"""
    print("\n=== 測試 Content Filter Agent ===\n")

    # 創建代理
    filter_agent = ContentFilterAgent()

    # 模擬網頁內容
    mock_content = {
        "url": "https://example.com",
        "title": "深度學習教學",
        "paragraphs": [
            "卷積神經網路（CNN）是深度學習中用於處理影像的重要架構。",
            "點擊購買最新課程！限時優惠！",  # 廣告
            "CNN 使用卷積層來自動提取特徵，相比傳統方法更加高效。",
            "這是一個很短的段落。",  # 太短
            "卷積層透過濾波器在影像上滑動，檢測邊緣、紋理等特徵。CNN 的這種特性使其特別適合影像辨識任務。"
        ]
    }

    # 過濾
    filtered = filter_agent.filter_content(mock_content, "卷積神經網路")

    print(f"原始段落: {filtered['original_count']}")
    print(f"過濾後: {filtered['filtered_count']}")
    print("\n過濾後的段落:")
    for i, para in enumerate(filtered['filtered_paragraphs'], 1):
        print(f"{i}. (相關性 {para['relevance_score']:.2f}) {para['text'][:100]}...")


if __name__ == "__main__":
    # test_web_search()
    test_content_filter()
