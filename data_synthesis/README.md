# Data Synthesis - 資料合成

這個資料夾包含 Data Synthesis（資料合成）相關的腳本和資料。

**注意**：根據用戶要求，目前暫不處理 Data Synthesis，先專注於 109 題的整合和驗證。

## 檔案說明

### 腳本
- `chain_to_dag.py` - 將線性工具序列轉換成 DAG
- `data_augmentation.py` - 資料增強（10 種策略）
- `toolscale_generator.py` - 生成 ToolScale 格式的資料集

### 資料
- `dags.json` - 7 個原始 DAG
- `augmented_dags.json` - 77 個增強後的 DAG（7 原始 + 70 變體）
- `toolscale_dataset.json` - 最終的 ToolScale 格式訓練資料集

### 日誌
- `chain_to_dag_optimized.log` - DAG 轉換日誌

## 技術細節

### Chain-to-DAG 轉換
- **依賴推斷規則**：4 層（Placeholder > 參數 > 語義 > 順序）
- **孤立節點**：從 20% 降至 2.6%
- **邊數**：從 26 增至 31

### 資料增強策略（10 種）
1. Add reasoning step - 插入推理步驟
2. Remove optional step - 移除可選步驟
3. Simplify description - 簡化描述
4. Add subgoal - 加入子目標
5. Permute parallel steps - 重排平行步驟
6. Tool substitution - 工具替換
7. Reorder - 順序重排
8. Decompose - 分解步驟
9. Merge steps - 合併步驟
10. Add intermediate output - 標記中間輸出

### 成果
- **樣本數**：從 42 增至 77（+83%）
- **多樣性**：從 21.4% 提升至 26.0%（+22%）

## 使用方式

```bash
# 1. 轉換 Chain 到 DAG
python3 chain_to_dag.py

# 2. 資料增強
python3 data_augmentation.py

# 3. 生成 ToolScale 格式
python3 toolscale_generator.py
```

**最後更新**：2026-02-09
