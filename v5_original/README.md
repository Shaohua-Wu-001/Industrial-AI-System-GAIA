# V5 Original - GAIA Level 3 原始 10 題

這個資料夾包含最初的 10 題 GAIA Level 3 任務及相關檔案。

## 檔案說明

- `gaia_level3_tasks.json` - 10 題原始資料
- `plans_v3_executable.json` - Parser v5 輸出
- `validation_results.json` - 驗證結果
- `analysis_report.json` - 分析報告
- `parser_v5.py` - Parser v5（已移到根目錄）
- `run_executor_v5.py` - 執行器 v5
- `answer_validator_v5.py` - 答案驗證器 v5
- `test_all_10_tasks.py` - 測試腳本
- `analyze_results.py` - 結果分析腳本

## 使用方式

```bash
# 執行 Parser v5
python3 ../parser_v5.py

# 驗證答案
python3 answer_validator_v5.py

# 分析結果
python3 analyze_results.py
```

**最後更新**：2026-02-09
