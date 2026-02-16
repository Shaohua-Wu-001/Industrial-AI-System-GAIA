# 統一的工具定義

這個資料夾包含合併後的工具 schema 和對應規則。

## 檔案說明

- `our_tools_schema.json` - 我們原本的 43 個工具 schema
- `ta_tools_schema.json` - 助教的 16 個工具 schema（待建立）
- `unified_tools_schema.json` - 合併後的統一 schema（待建立）
- `tools_mapping.json` - 工具對應表
- `extract_tools_schema.py` - 提取工具 schema 的腳本

## 工具整合策略

### 1. 直接使用助教的工具（10 個）
- web_search, calculator, pdf_reader, excel_reader, zip_extractor
- file_reader, python_executor, code_interpreter, audio_transcription
- image_recognition

### 2. 保留我們的工具（35+ 個）
- 資料處理：aggregate_data, filter_data, sort_data, join_data, pivot_table
- 統計分析：correlation_analysis, statistical_analysis, moving_average
- 其他讀取：read_json, read_xml, read_docx, read_csv
- 工具：unit_converter, date_calculator, currency_converter
- 文字處理：extract_information, find_in_text, regex_search

### 3. 合併的工具（5 個）
- web_browser + web_fetch → web_fetch（增強版）
- download_file + web_fetch → web_fetch（增強版）
- pptx_reader + read_docx → read_pptx（新增）
- image_recognition + image_to_text → image_recognition（使用助教的）
- video_analysis + analyze_image → video_analysis（使用助教的）

**預估最終工具數**：約 50 個

## 下一步

1. 從助教的 gaia.infer.jsonl 提取工具 schema
2. 合併兩邊的工具，建立 unified_tools_schema.json
3. 更新 Parser v5 以使用統一的 schema

**最後更新**：2026-02-09
