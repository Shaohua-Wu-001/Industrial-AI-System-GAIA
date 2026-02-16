# 助教的 99 題 GAIA 資料

這個資料夾包含助教提供的 99 題 GAIA 任務（Level 1: 38, Level 2: 50, Level 3: 11）。

## 資料來源

原始資料來自：
```
../../LLM-planning-main/data/GAIA/gaia.infer/gaia.infer.jsonl
```

## 檔案說明

- `gaia_infer.jsonl` - 99 題的原始資料（JSONL 格式，每行一個任務）
- `ta_tools_schema.json` - 助教的工具 schema（從第一題中提取）
- `README.md` - 本說明文件

## 資料格式

每個任務包含：
- `meta` - 元資料（dataset, subset, split, id, difficulty等）
- `query` - 問題描述（user_query, attachments等）
- `tool_environment` - 可用的工具列表（含完整的 arguments_schema）
- `gold` - 黃金答案（plan_dag, tool_calls, final_answer）

## 工具列表（16 個）

1. web_search - 搜尋網頁
2. web_browser - 瀏覽網頁
3. download_file - 下載檔案
4. calculator - 計算器
5. python_executor - 執行 Python 程式碼
6. code_interpreter - 執行其他語言程式碼
7. pdf_reader - 讀取 PDF
8. excel_reader - 讀取 Excel/CSV
9. file_reader - 讀取一般檔案
10. pptx_reader - 讀取 PowerPoint
11. zip_extractor - 解壓縮
12. image_recognition - 圖像識別（OCR）
13. audio_transcription - 音訊轉錄
14. video_analysis - 影片分析
15. reasoning - 推理步驟
16. submit_final_answer - 提交答案

**最後更新**：2026-02-09
