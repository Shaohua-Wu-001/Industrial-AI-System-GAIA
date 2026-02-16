# 🎓 Delta_GAIA 專案完整改進報告

## 📋 目錄
1. [專案流程圖](#專案流程圖)
2. [方向一：GAIA Level 3 的 10 題](#方向一gaia-level-3-的-10-題)
3. [方向二：Data Synthesis](#方向二data-synthesis)
4. [問題優先級總結](#問題優先級總結)
5. [詳細改進計畫](#詳細改進計畫)

---

## 🔄 專案流程圖

```
┌─────────────────────────────────────────────────────────────────┐
│  階段 1: 資料來源                                                  │
├─────────────────────────────────────────────────────────────────┤
│  GAIA Level 3 原始資料 (gaia_level3_tasks.json)                   │
│  • 10 題最高難度問題                                               │
│  • 包含 Question, Final Answer, 部分題目有檔案                     │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  階段 2: Parser (parser_v5.py)                                    │
├─────────────────────────────────────────────────────────────────┤
│  輸入：人工標註的步驟文字                                           │
│  處理：                                                            │
│   1. Regex 規則匹配工具名稱                                        │
│   2. 提取參數                                                      │
│   3. 識別推理步驟 vs 工具步驟                                      │
│  輸出：plans_v3_executable.json                                   │
│   • 10 個計畫, 138 步驟 (60 工具 + 78 推理)                       │
│                                                                   │
│  ⚠️  問題：                                                        │
│   - 推理步驟 (56.5%) 無法執行                                     │
│   - 大量 placeholder (<from_context>, <iterate:*>)               │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  階段 3: Executor (可選，用於驗證)                                 │
├─────────────────────────────────────────────────────────────────┤
│  執行工具呼叫，生成實際結果                                         │
│                                                                   │
│  結果：validation_results.json                                    │
│   • 答對：1/10 (10%)                                              │
│   • 答錯：2/10 (20%)                                              │
│   • 未執行：7/10 (70%)                                            │
│                                                                   │
│  🔴 問題：執行成功率極低                                           │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  階段 4: Chain-to-DAG (chain_to_dag.py)                           │
├─────────────────────────────────────────────────────────────────┤
│  輸入：plans_v3_executable.json                                   │
│  處理：                                                            │
│   1. 過濾推理步驟（tool_name=None）                                │
│   2. 建立工具節點                                                  │
│   3. 推斷依賴關係（啟發式規則）                                     │
│   4. 計算 DAG 統計（深度、平行化）                                 │
│  輸出：dags.json                                                  │
│   • 7 個有效 DAG (過濾掉 l3_007)                                  │
│   • 38 個工具節點                                                  │
│                                                                   │
│  🟡 問題：                                                         │
│   - 依賴關係推斷不準確                                             │
│   - 有孤立節點                                                     │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  階段 5: Data Augmentation (data_augmentation.py)                │
├─────────────────────────────────────────────────────────────────┤
│  輸入：dags.json                                                  │
│  處理：對每個 DAG 生成 5 個變體                                    │
│   • v0: original (原始)                                           │
│   • v1: parameter_tweak (參數微調)                                │
│   • v2: add_verification (增加驗證)                               │
│   • v3: change_description (改變描述)                             │
│   • v4: add_retry (增加重試)                                      │
│   • v5: simplify (簡化)                                           │
│  輸出：augmented_dags.json                                        │
│   • 42 個 DAG (7×6)                                               │
│                                                                   │
│  🟡 問題：                                                         │
│   - 增強策略變化不大                                               │
│   - 多樣性只有 21.4%                                              │
└────────────────────┬────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│  階段 6: ToolScale Generator (toolscale_generator.py)            │
├─────────────────────────────────────────────────────────────────┤
│  輸入：augmented_dags.json                                        │
│  處理：轉換成 ToolScale 格式                                       │
│   • 重建 planning steps                                           │
│   • 加入 metadata (工具序列、依賴類型)                             │
│   • 保留完整 DAG 結構                                             │
│  輸出：toolscale_dataset.json                                     │
│   • 42 筆訓練樣本                                                  │
│   • 230 個 planning 步驟                                          │
│   • 平均 5.48 步/任務                                             │
│                                                                   │
│  🔴 問題：樣本數量太少（建議 500-1000 筆）                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 方向一：GAIA Level 3 的 10 題

### 問題清單

#### 🔴 問題 1：執行成功率極低 (10%)

**嚴重度：高**

**現況：**
- 答對：1/10 (gaia_val_l3_001)
- 答錯：2/10 (gaia_val_l3_004, gaia_val_l3_009)
- 未執行：7/10 (70%)

**根本原因：**
1. **大量 Placeholder** 導致無法執行：
   - `<from_context>`: 需要前面步驟的輸出
   - `<iterate:ORCID>`: 需要迴圈迭代
   - `<from_previous_web_fetch>`: 需要前一步的結果
   
2. **Executor 能力不足**：
   - 無法處理複雜依賴
   - 無法維護執行狀態
   - 無法處理迴圈

3. **缺少實際資料**：
   - 沒有中間結果的 ground truth
   - 只有最終答案

**詳細案例：**

```
gaia_val_l3_000 (未執行):
  - 18 步驟，只有 3/18 可執行 (16.7%)
  - 跳過原因：
    • step_5: URL 包含 placeholder <from_previous_web_search>
    • step_11: data 包含 placeholder <from_context>
    • step_16: expression 包含 placeholder round(<from_previous>)

gaia_val_l3_004 (答錯: 0 vs 22):
  - 9 步驟，5/9 可執行 (55.6%)
  - 跳過 4 步驟後，計算結果錯誤
  
gaia_val_l3_009 (答錯: 3 vs 55):
  - 26 步驟，12/26 可執行 (46.2%)
  - 跳過 14 步驟後，計算結果錯誤
```

**影響：**
- 無法驗證 Parser 的正確性
- 無法提供執行 trace 作為訓練資料
- 限制了資料品質

**是否需要處理：**
- ✅ **需要**，但**不影響訓練**
- 未執行的題目仍有完整 plan，可用於訓練
- 主要影響：無法驗證正確性

---

#### 🟡 問題 2：工具覆蓋率低 (37.2%)

**嚴重度：中**

**現況：**
- 使用 16/43 種工具
- 覆蓋率：37.2%
- 高頻工具：
  1. web_search: 17 次
  2. web_fetch: 14 次
  3. calculate: 6 次
  4. extract_information: 5 次

**未使用的工具 (27 種)：**
- aggregate_data, analyze_image, compare_data
- correlation_analysis, create_csv, create_markdown
- currency_converter, date_calculator, encode_decode
- fill_missing, geocoding, image_to_text
- join_data, list_operations, moving_average
- pivot_table, read_csv, read_docx, read_image
- regex_search, sample_data, sort_data
- split_join_text, statistical_analysis, string_transform
- ... 等

**根本原因：**
- GAIA Level 3 題目**類型偏重**：
  - 網路搜尋類（web_search, web_fetch）
  - 文件處理類（read_pdf, read_json）
  - 計算類（calculate, unit_converter）
  
**影響：**
- 訓練的模型對某些工具缺乏經驗
- 無法學習複雜的資料處理任務

**是否需要處理：**
- ✅ **需要**，通過擴充資料集解決

---

#### 🟡 問題 3：極端案例

**嚴重度：中**

**現況：**
- **gaia_val_l3_007**：39 個步驟，0 個工具（全是推理）
- **gaia_val_l3_008**：1 個步驟，1 個工具

**詳細分析：**

**gaia_val_l3_007：**
- 問題：「The following numbers function similarly to ISBN 13 numbers...」
- 39 個步驟全部是推理和計算過程
- 沒有任何工具呼叫
- 處理：在 DAG 階段被過濾掉（正確）

**gaia_val_l3_008：**
- 問題：「I was trying to remember how well the Cheater Beater performed...」
- 只有 1 個 compare_values 工具
- 缺少前置步驟（如何獲得資料）
- 可能是標註不完整

**影響：**
- 減少可用樣本數（從 8 降到 7）
- gaia_val_l3_008 的 plan 過於簡單

**是否需要處理：**
- ⚠️ **可選**
- l3_007 正確過濾
- l3_008 可以保留（儘管簡單）

---

#### 🟡 問題 4：資料不平衡

**嚴重度：中**

**步驟數分布：**
```
最少：1 步  (gaia_val_l3_008)
最多：39 步 (gaia_val_l3_007)
平均：13.8 步
中位數：14 步
```

**工具步驟數分布：**
```
最少：0 步  (gaia_val_l3_007)
最多：13 步 (gaia_val_l3_009)
平均：6.0 步
```

**問題：**
- 步驟數差異巨大（1-39）
- 簡單任務和複雜任務混在一起
- 可能影響模型學習

**是否需要處理：**
- ⚠️ **低優先級**
- 資料擴充後會自然平衡

---

## 🔧 方向二：Data Synthesis

### 問題清單

#### 🔴 問題 5：樣本數量嚴重不足

**嚴重度：高**

**現況：**
- 最終訓練樣本：**42 筆**
- 原始任務：7 個
- 增強倍數：6x

**問題：**
- **42 筆對於 LLM fine-tuning 來說太少**
- 業界建議：
  - 最少：500-1000 筆
  - 理想：5000-10000 筆
  - 高品質：1000-3000 筆
  
**根本原因：**
- 只有 10 題 GAIA Level 3
- 其中 1 題被過濾（l3_007）
- 2 題答錯但保留（l3_004, l3_009）
- 有效樣本只來自 7 個原始任務

**影響：**
- 模型容易 overfitting
- 泛化能力差
- 無法學習多樣化的模式

**是否需要處理：**
- ✅ **必須處理** - 最高優先級

**解決方案：**
1. **短期（1-2 週）：**
   - 擴充到完整 GAIA Level 3（約 50 題）
   - 目標：50 × 6 = 300 筆
   
2. **中期（1 個月）：**
   - 加入 GAIA Level 2（約 150 題）
   - 目標：200 × 6 = 1200 筆
   
3. **長期（2-3 個月）：**
   - 加入 GAIA Level 1（約 150 題）
   - 自動生成合成任務
   - 目標：500+ × 6 = 3000+ 筆

---

#### 🟡 問題 6：增強策略變化不大

**嚴重度：中**

**現況：**
- 5 種增強策略，每種對 7 個任務各產生 1 個變體
- 總共 42 個 DAG

**各策略效果分析：**

以 `gaia_val_l3_001` 為例：
- **v0 (original)**: 4 節點，基準版本
- **v1 (parameter_tweak)**: 4 節點，只改變 1 個節點的參數
  - 效果：變化極小
- **v2 (add_verification)**: 5 節點，增加 1 個驗證節點
  - 效果：結構改變，但只加 1 個節點
- **v3 (change_description)**: 4 節點，只改描述
  - 效果：結構完全不變
- **v4 (add_retry)**: 4 節點，加 retry metadata
  - 效果：結構不變，只加 metadata
- **v5 (simplify)**: 4 節點，加 explicit_output
  - 效果：結構不變，只加 metadata

**統計：**
- 唯一工具序列：9 種
- 總序列數：42 個
- **多樣性：21.4%** ← 很低！

**問題：**
- 增強策略過於保守
- 主要改變 metadata 或描述
- 結構變化不大
- 同一個任務的 6 個變體過於相似

**影響：**
- 降低訓練資料的有效多樣性
- 模型可能學到重複的模式

**是否需要處理：**
- ✅ **需要處理** - 中優先級

**解決方案：**
1. **新增激進策略：**
   - **工具替換**：web_search → wikipedia_search
   - **順序重排**：在不違反依賴的前提下
   - **子目標分解**：拆分複雜步驟
   - **工具組合**：合併連續的相同類型工具
   
2. **增加變體數量：**
   - 從 6 個增加到 10 個
   - 組合多種策略

3. **參數範圍擴大：**
   - parameter_tweak 不只加括號，改變數值
   - add_verification 增加多種驗證類型

---

#### 🟡 問題 7：DAG 依賴關係不準確

**嚴重度：中**

**現況：**
- 依賴關係由啟發式規則推斷
- 發現多個**孤立節點**（沒有入邊也沒有出邊）

**案例：**

```
gaia_val_l3_001:
  節點：4, 邊：1
  孤立節點：step_1, step_3
  
  實際情況：
    step_1 (read_json) → 應該是 step_2 的輸入
    step_2 (web_fetch) → step_4
    step_3 (count_occurrences) → 應該連接到某處
    step_4 (calculate)
  
  問題：
    - step_1 和 step_3 沒有被連接
    - 依賴推斷規則過於簡化
```

```
gaia_val_l3_002:
  節點：2, 邊：0
  孤立節點：step_1, step_3
  
  實際情況：
    step_1 (web_search)
    step_3 (web_search)
  
  問題：
    - 兩個 web_search 完全獨立
    - 應該有某種依賴（例如第二次搜尋用到第一次的結果）
```

**根本原因：**

`chain_to_dag.py` 中的依賴推斷規則過於簡單：

```python
# 規則 1：檔案路徑依賴 extract_zip
# 規則 2：calculate 依賴最近的 read_* 或 web_fetch
# 規則 3：web_fetch 依賴 web_search
# 規則 4：順序依賴（保守估計）
```

這些規則**不夠精確**，容易遺漏真實的依賴關係。

**影響：**
- DAG 結構不正確
- 可能誤導模型學習錯誤的依賴關係
- 平行化分析不準確

**是否需要處理：**
- ✅ **需要處理** - 中優先級

**解決方案：**
1. **短期：人工驗證**
   - 檢查前 10 個 DAG 的依賴是否合理
   - 手動修正明顯錯誤
   
2. **中期：改進規則**
   - 增加更多啟發式規則
   - 基於參數名稱推斷（如 `file_path` 參數）
   - 基於 placeholder 推斷（如 `<from_previous_X>`）
   
3. **長期：使用 LLM**
   - 用 GPT-4 分析依賴關係
   - 生成更準確的 DAG

---

#### 🟡 問題 8：訓練資料多樣性不足

**嚴重度：中**

**現況：**
- 唯一工具序列：9 種
- 總樣本數：42 個
- **多樣性：21.4%**

**步驟數分布：**
```
 1 步： 6 個樣本 (14.3%)
 2 步： 6 個樣本 (14.3%)
 4 步： 5 個樣本 (11.9%)
 5 步： 7 個樣本 (16.7%)
 7 步： 5 個樣本 (11.9%)
 8 步： 7 個樣本 (16.7%)
11 步： 6 個樣本 (14.3%)
```

**工具序列統計：**
- 最常見：web_search → web_fetch (多個變體)
- 第二常見：read_json → web_fetch → count_occurrences → calculate

**問題：**
- 每個原始任務的 6 個變體過於相似
- 工具序列重複率高（78.6%）
- 步驟數集中在幾個特定長度

**根本原因：**
- 原始任務只有 7 個
- 增強策略主要改變細節，不改變結構
- 缺少跨任務的組合

**影響：**
- 模型可能學到的是記憶特定序列
- 而不是理解工具編排的邏輯

**是否需要處理：**
- ✅ **需要處理** - 與問題 5, 6 相關

**解決方案：**
1. **增加原始任務**（最重要）
   - 從 7 個擴充到 50+ 個
   
2. **改進增強策略**
   - 使用更激進的策略
   - 組合多種策略
   
3. **跨任務混合**
   - 將不同任務的子圖組合
   - 生成新的合成任務

---

#### 🟢 問題 9：ToolScale 格式完整性

**嚴重度：低**

**現況：**
- 所有條目結構完整 ✓
- 符合 ToolScale 標準 ✓
- metadata 欄位完整 ✓

**檢查結果：**
- id, source_task_id, variant_id: ✓
- question, final_answer: ✓
- planning (total_steps, steps, dag_structure): ✓
- dag (nodes, edges): ✓
- metadata (source, tool_sequence, 依賴標記): ✓

**是否需要處理：**
- ❌ **不需要** - 已經很好

---

#### 🟢 問題 10：Pipeline 可重現性

**嚴重度：低**

**現況：**
- 所有腳本存在 ✓
- 資料檔案完整 ✓
- 可以重新執行 ✓

**建議改進：**
- 寫自動化腳本 `run_pipeline.sh`
- 加入版本控制（git）
- 寫詳細的 README

**是否需要處理：**
- ⚠️ **建議處理** - 但不緊急

---

## 📊 問題優先級總結

### 🔴 必須立即處理（P0）

| 問題 | 嚴重度 | 處理難度 | 預期效果 | 建議時程 |
|------|--------|---------|---------|---------|
| **問題 5：樣本數量不足** | 🔴 高 | 中 | +++++ | 1-2 週 |
| **問題 1：執行成功率低** | 🔴 高 | 高 | ++（不影響訓練）| 可延後 |

### 🟡 應該處理（P1）

| 問題 | 嚴重度 | 處理難度 | 預期效果 | 建議時程 |
|------|--------|---------|---------|---------|
| **問題 6：增強策略弱** | 🟡 中 | 低 | ++++ | 1 週 |
| **問題 7：依賴不準確** | 🟡 中 | 中 | +++ | 2 週 |
| **問題 2：工具覆蓋低** | 🟡 中 | 中 | +++（隨資料擴充）| 2 週 |
| **問題 8：多樣性不足** | 🟡 中 | 低 | +++（隨上述改進）| 1 週 |

### 🟢 可選處理（P2）

| 問題 | 嚴重度 | 處理難度 | 預期效果 | 建議時程 |
|------|--------|---------|---------|---------|
| **問題 3：極端案例** | 🟡 中 | 低 | ++ | 1 天 |
| **問題 4：資料不平衡** | 🟡 中 | 低 | +（自然解決）| - |
| **問題 10：可重現性** | 🟢 低 | 低 | ++ | 2 天 |

### ✅ 無需處理（已完成）

| 問題 | 狀態 |
|------|------|
| **問題 9：格式完整性** | ✅ 已完美 |

---

## 🎯 詳細改進計畫

### 階段 1：資料擴充（最高優先級）

**目標：從 7 個任務擴充到 50+ 個任務**

#### Step 1.1：準備完整的 GAIA 資料集

```bash
# 1. 下載完整的 GAIA benchmark
# 包含 Level 1 (~150 題), Level 2 (~150 題), Level 3 (~50 題)

# 2. 組織檔案結構
data/
  ├── gaia_level1_tasks.json
  ├── gaia_level2_tasks.json
  ├── gaia_level3_tasks.json  # 現有
  └── files/
      ├── level1/
      ├── level2/
      └── level3/
```

**時程：1 天**

#### Step 1.2：批次執行 Parser

```bash
# 修改 parser_v5.py 支援批次處理
python parser_v5.py --input gaia_level3_tasks.json --output plans_l3.json
python parser_v5.py --input gaia_level2_tasks.json --output plans_l2.json
# ... 依需求
```

**時程：2-3 天**
**預期輸出：**
- Level 3: 50 個 plans → 300 筆樣本
- Level 2: 100 個 plans → 600 筆樣本
- **總計：900+ 筆訓練樣本**

#### Step 1.3：品質檢查

```bash
# 檢查 Parser 輸出品質
python check_plans_quality.py --input plans_l3.json
```

**檢查項目：**
- [ ] 工具識別率 > 40%
- [ ] 平均步驟數 > 3
- [ ] 無 critical errors

**時程：1 天**

---

### 階段 2：改進增強策略（高優先級）

**目標：提高資料多樣性從 21.4% 到 50%+**

#### Step 2.1：設計新的增強策略

在 `data_augmentation.py` 中新增：

**策略 6：工具替換（Tool Substitution）**
```python
def _variant_tool_substitution(self, dag: Dict, variant_id: int) -> Dict:
    """
    替換可替換的工具：
    - web_search → wikipedia_search
    - read_json → read_csv (如果可行)
    - calculate → unit_converter (數值轉換)
    """
    pass
```

**策略 7：順序重排（Reordering）**
```python
def _variant_reorder(self, dag: Dict, variant_id: int) -> Dict:
    """
    在不違反依賴的前提下，重新排列步驟
    - 使用拓撲排序找出可平行的步驟
    - 隨機選擇一種合法的排列
    """
    pass
```

**策略 8：子目標分解（Subgoal Decomposition）**
```python
def _variant_decompose(self, dag: Dict, variant_id: int) -> Dict:
    """
    將複雜步驟拆分成多個子步驟
    - web_fetch → web_search + web_fetch
    - calculate → extract_information + calculate
    """
    pass
```

**策略 9：步驟合併（Step Merging）**
```python
def _variant_merge(self, dag: Dict, variant_id: int) -> Dict:
    """
    合併連續的相同類型操作
    - 3× web_fetch → 1× batch_web_fetch
    """
    pass
```

**策略 10：錯誤注入（Error Injection）**
```python
def _variant_error_injection(self, dag: Dict, variant_id: int) -> Dict:
    """
    模擬可能的錯誤並加入恢復步驟
    - web_fetch 失敗 → retry with different URL
    - read_pdf 失敗 → fallback to web_fetch
    """
    pass
```

**時程：3-5 天**
**預期效果：多樣性提升至 50%+**

#### Step 2.2：增加變體數量

```python
# 從每個任務 6 個變體增加到 10 個
# 900 個原始任務 × 10 = 9000 筆訓練樣本
```

**時程：1 天（修改參數）**

---

### 階段 3：改進 DAG 依賴推斷（中優先級）

**目標：減少孤立節點，提高依賴準確性**

#### Step 3.1：人工驗證前 10 個 DAG

```bash
# 建立驗證腳本
python verify_dag.py --dag_id gaia_val_l3_001 --visualize
```

**檢查項目：**
- [ ] 孤立節點是否合理
- [ ] 依賴方向是否正確
- [ ] 是否有遺漏的依賴

**時程：1 天**

#### Step 3.2：改進依賴推斷規則

在 `chain_to_dag.py` 中改進 `_find_dependencies`：

```python
def _find_dependencies(self, current_id, args, previous_nodes, node_outputs):
    """
    改進的依賴推斷規則：
    
    1. 參數名稱規則：
       - file_path 參數 → 依賴 read_* 或 extract_zip
       - url 參數 → 依賴 web_search
       - data 參數 → 依賴最近的資料源
    
    2. Placeholder 規則：
       - <from_previous_X> → 依賴前一個 X 類型工具
       - <from_context> → 依賴所有前面的工具
       - <iterate:field> → 依賴包含該 field 的工具
    
    3. 語義規則：
       - calculate 依賴所有前面的資料提取工具
       - compare_values 依賴前面的 calculate
       - filter_data 依賴前面的 read_*
    
    4. 順序規則（最後採用）：
       - 如果無法判斷，依賴前一個工具
    """
    pass
```

**時程：2-3 天**

#### Step 3.3：使用 LLM 輔助（可選）

```python
def _use_llm_for_dependencies(self, nodes):
    """
    使用 GPT-4 分析依賴關係
    
    Prompt:
    "Given the following tool sequence, identify the dependencies:
     1. read_json: Read JSONLD file
     2. web_fetch: Fetch ORCID pages
     3. count_occurrences: Count pre-2020 works
     4. calculate: Take average
     
     Which steps depend on which previous steps?"
    """
    pass
```

**時程：2 天（需要 API key）**

---

### 階段 4：改進 Executor（低優先級，不影響訓練）

**目標：提高執行成功率從 10% 到 50%+**

**注意：這不影響訓練，但可以提供更好的驗證**

#### Step 4.1：實作狀態管理

```python
class StatefulExecutor:
    def __init__(self):
        self.state = {}  # 儲存中間結果
        
    def execute_step(self, step):
        # 解析 placeholder
        args = self.resolve_placeholders(step['arguments'])
        
        # 執行工具
        result = self.execute_tool(step['tool_name'], args)
        
        # 儲存結果
        self.state[step['step_id']] = result
```

**時程：3-5 天**

#### Step 4.2：實作迴圈處理

```python
def handle_iterate(self, placeholder):
    """
    處理 <iterate:field> placeholder
    
    例如：<iterate:ORCID>
    1. 從 state 中找出包含 ORCID 的結果
    2. 提取所有 ORCID 值
    3. 對每個值執行後續步驟
    4. 合併結果
    """
    pass
```

**時程：2-3 天**

---

### 階段 5：自動化與文件（低優先級）

#### Step 5.1：撰寫自動化腳本

```bash
# run_pipeline.sh
#!/bin/bash

echo "開始執行 Delta_GAIA Pipeline..."

# 1. Parser
echo "[1/4] 執行 Parser..."
python parser_v5.py --input gaia_level3_tasks.json

# 2. Chain-to-DAG
echo "[2/4] 生成 DAG..."
python chain_to_dag.py

# 3. Data Augmentation
echo "[3/4] 資料增強..."
python data_augmentation.py --variants 10

# 4. ToolScale Generator
echo "[4/4] 生成 ToolScale 資料集..."
python toolscale_generator.py

echo "✓ Pipeline 完成！"
echo "輸出：toolscale_dataset.json"
```

**時程：1 天**

#### Step 5.2：撰寫 README

**內容：**
- 專案簡介
- 安裝指南
- 使用方法
- Pipeline 流程圖
- 常見問題
- 資料格式說明

**時程：1 天**

---

## 📅 建議時程表

### 第 1 週：資料擴充（最重要）
- [ ] Day 1: 準備完整 GAIA 資料集
- [ ] Day 2-4: 批次執行 Parser
- [ ] Day 5: 品質檢查與修正

### 第 2 週：增強策略改進
- [ ] Day 1-3: 設計並實作新的增強策略（策略 6-10）
- [ ] Day 4: 測試新策略
- [ ] Day 5: 重新生成 augmented_dags.json

### 第 3 週：DAG 依賴改進
- [ ] Day 1: 人工驗證前 10 個 DAG
- [ ] Day 2-3: 改進依賴推斷規則
- [ ] Day 4: 測試改進效果
- [ ] Day 5: 重新生成 dags.json

### 第 4 週：整合與驗證
- [ ] Day 1-2: 重新執行完整 Pipeline
- [ ] Day 3: 品質檢查與統計
- [ ] Day 4: 撰寫文件
- [ ] Day 5: 最終驗證與交付

**總時程：4 週**

---

## 🎯 預期成果

完成所有改進後：

| 指標 | 當前 | 目標 | 改進 |
|------|------|------|------|
| 訓練樣本數 | 42 | 3000+ | +7042% |
| 原始任務數 | 7 | 200+ | +2757% |
| 工具覆蓋率 | 37.2% | 70%+ | +88% |
| 資料多樣性 | 21.4% | 50%+ | +134% |
| 孤立節點 | 較多 | < 5% | - |
| 執行成功率 | 10% | 50%+ | +400% |

**最終資料集：**
- 3000+ 筆高品質訓練樣本
- 覆蓋 30+ 種工具
- 多樣化的任務類型
- 準確的 DAG 結構
- 符合 ToolScale 標準

---

## ✅ Check List

### 立即開始（P0）
- [ ] 問題 5：擴充資料集到 50+ 原始任務
- [ ] 問題 6：設計並實作 5 個新增強策略

### 本週完成（P1）
- [ ] 問題 7：改進 DAG 依賴推斷規則
- [ ] 問題 2：增加工具覆蓋率（隨資料擴充自然改善）
- [ ] 問題 8：提高訓練資料多樣性

### 可選處理（P2）
- [ ] 問題 3：處理極端案例
- [ ] 問題 10：撰寫自動化腳本與文件
- [ ] 問題 1：改進 Executor（不影響訓練）

### 無需處理
- [x] 問題 9：ToolScale 格式（已完美）

