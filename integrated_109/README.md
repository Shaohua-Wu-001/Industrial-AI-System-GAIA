# 整合後的 109 題

這個資料夾包含整合後的 109 題（99 題助教 + 10 題 GAIA L3）及相關分析。

## 檔案說明

### 核心資料
- `gaia_109_tasks.json` (2860 KB) - 整合後的 109 題，統一格式
- `validation_results_109.json` - 109 題的驗證結果
- `analysis_report_109.json` - 109 題的分析報告

### 腳本
- `integrate_109_tasks.py` - 整合腳本（含工具對應規則）
- `run_109_pipeline.py` - Pipeline 執行腳本（驗證 + 分析）

### 報告
- `109_題總結報告.md` - 完整總結報告
- `PARSER_PARAMETER_CHECK.md` - Parser 參數檢查報告

## 統計資料

- **總題數**：109 題
  - Level 1: 38 題
  - Level 2: 50 題
  - Level 3: 21 題

- **總步驟數**：17,661 步
  - 工具步驟：426 步（2.4%）
  - 推理步驟：17,235 步（97.6%）

- **整體驗證率**：100%

## 使用方式

```bash
# 重新整合資料（如果需要）
python3 integrate_109_tasks.py

# 執行 Pipeline（驗證 + 分析）
python3 run_109_pipeline.py
```

**最後更新**：2026-02-09
