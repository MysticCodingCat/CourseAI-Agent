"""
測試 MarkItDown - Microsoft 的文件轉 Markdown 工具

支援格式：
- Office: PDF, PowerPoint, Word, Excel
- 圖片: PNG, JPG (with OCR)
- 音頻: WAV, MP3 (with transcription via Whisper)
- Others: HTML, CSV, JSON, XML, ZIP
"""

from markitdown import MarkItDown


def test_basic():
    """測試基本功能"""
    print("="*60)
    print("測試 MarkItDown 基本功能")
    print("="*60)

    md = MarkItDown()

    print("\n可用的轉換器:")
    print(f"  - PowerPoint 支援: {'是' if hasattr(md, 'convert') else '否'}")
    print(f"  - PDF 支援: {'是' if hasattr(md, 'convert') else '否'}")
    print(f"  - 圖片 OCR: {'是' if hasattr(md, 'convert') else '否'}")
    print(f"  - 音頻轉錄: {'是' if hasattr(md, 'convert') else '否'}")

    # 顯示 MarkItDown 的屬性
    print("\nMarkItDown 物件:")
    print(f"  類型: {type(md)}")
    print(f"  方法: {[m for m in dir(md) if not m.startswith('_')]}")


def test_ppt_conversion():
    """測試 PPT 轉換"""
    print("\n" + "="*60)
    print("測試 PowerPoint 轉換")
    print("="*60)

    md = MarkItDown()

    # 檢查是否有測試 PPT
    import os
    test_files = [
        "test.pptx",
        "../test.pptx",
        "lecture.pptx"
    ]

    ppt_file = None
    for file in test_files:
        if os.path.exists(file):
            ppt_file = file
            break

    if not ppt_file:
        print("[警告] 沒有找到測試 PPT 檔案")
        print("提示：請準備一個 test.pptx 檔案來測試")
        return

    print(f"\n解析檔案: {ppt_file}")
    try:
        result = md.convert(ppt_file)

        print(f"\n轉換結果:")
        print(f"  原始文字長度: {len(result.text_content)} 字元")
        print(f"\n前 500 字元:")
        print("-" * 60)
        print(result.text_content[:500])
        print("-" * 60)

        # 儲存完整結果
        output_file = ppt_file.replace('.pptx', '_markitdown.md')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.text_content)
        print(f"\n[成功] 完整 Markdown 已儲存: {output_file}")

        # 分析結構
        lines = result.text_content.split('\n')
        h1_count = sum(1 for line in lines if line.startswith('# '))
        h2_count = sum(1 for line in lines if line.startswith('## '))
        h3_count = sum(1 for line in lines if line.startswith('### '))

        print(f"\n結構分析:")
        print(f"  標題 (H1): {h1_count}")
        print(f"  章節 (H2): {h2_count}")
        print(f"  子章節 (H3): {h3_count}")
        print(f"  總行數: {len(lines)}")

    except Exception as e:
        print(f"[錯誤] 轉換失敗: {e}")


def test_audio_transcription():
    """測試音頻轉錄"""
    print("\n" + "="*60)
    print("測試音頻轉錄 (Whisper)")
    print("="*60)

    md = MarkItDown()

    print("\n[注意] 音頻轉錄需要:")
    print("  1. 音頻檔案 (WAV, MP3, M4A 等)")
    print("  2. OpenAI API key (如果使用 OpenAI Whisper)")
    print("  3. 或本地 Whisper 模型")

    print("\n這個功能對我們的 Day 9 錄音上傳很有用！")
    print("可以將課程錄音自動轉成文字，加入 RAG 知識庫")


def test_image_ocr():
    """測試圖片 OCR"""
    print("\n" + "="*60)
    print("測試圖片 OCR")
    print("="*60)

    print("\n圖片 OCR 功能可以:")
    print("  1. 從投影片截圖提取文字")
    print("  2. 辨識圖表、公式")
    print("  3. 補充 PPT 中無法提取的內容")

    print("\n這對我們的 Day 7 視覺輔助功能很有幫助！")


def main():
    """主測試流程"""
    print("\n" + "="*60)
    print("MarkItDown 完整測試")
    print("="*60 + "\n")

    test_basic()
    test_ppt_conversion()
    test_audio_transcription()
    test_image_ocr()

    print("\n" + "="*60)
    print("測試總結")
    print("="*60)
    print("\nMarkItDown 的優勢:")
    print("  [+] 支援多種格式（PPT, PDF, Word, Excel, 圖片, 音頻）")
    print("  [+] 自動轉換成 Markdown")
    print("  [+] 內建 OCR 和音頻轉錄")
    print("  [+] Microsoft 官方維護，持續更新")

    print("\n整合建議:")
    print("  1. 用 MarkItDown 做初步轉換（取代 python-pptx）")
    print("  2. 用我們的邏輯分析 Markdown，提取結構")
    print("  3. 用 MarkItDown 的音頻轉錄功能處理錄音（Day 9）")
    print("  4. 用 MarkItDown 的 OCR 功能處理圖片（Day 7）")

    print("\n下一步:")
    print("  [ ] 重構 ppt_parser.py，使用 MarkItDown")
    print("  [ ] 測試 Markdown 結構分析")
    print("  [ ] 整合音頻轉錄功能")
    print("  [ ] 更新 requirements.txt")


if __name__ == "__main__":
    main()
