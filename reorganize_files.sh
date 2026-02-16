#!/bin/bash
# Delta_GAIA 資料夾重組腳本
# 日期：2026-02-09
#
# 使用方式：
#   1. 先檢查腳本內容：cat reorganize_files.sh
#   2. 執行腳本：bash reorganize_files.sh
#   3. 如有問題，可以隨時中止（Ctrl+C）

set -e  # 遇到錯誤時停止

echo "=== Delta_GAIA 資料夾重組 ==="
echo "開始時間：$(date)"
echo ""

# 取得當前目錄
DELTA_GAIA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DELTA_GAIA_DIR"

echo "工作目錄：$DELTA_GAIA_DIR"
echo ""

# 確認是否在正確的目錄
if [ ! -f "parser_v5.py" ]; then
    echo "錯誤：找不到 parser_v5.py，請確認您在 Delta_GAIA 資料夾中"
    exit 1
fi

echo "✓ 確認在正確的目錄"
echo ""

# ============================================================
# 步驟 1：建立資料夾結構
# ============================================================
echo "[1/8] 建立資料夾結構..."

# 資料夾已經透過 README.md 建立完成
# 只需要確認它們存在

for dir in v5_original ta_99_tasks integrated_109 tools data_synthesis docs archive; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir/ 已存在"
    else
        echo "  ✗ $dir/ 不存在（應該已透過 README.md 建立）"
    fi
done

echo ""

# ============================================================
# 步驟 2：移動檔案到 v5_original/
# ============================================================
echo "[2/8] 移動檔案到 v5_original/..."

files_to_v5=(
    "gaia_level3_tasks.json"
    "plans_v3_executable.json"
    "validation_results.json"
    "analysis_report.json"
    "run_executor_v5.py"
    "answer_validator_v5.py"
    "test_all_10_tasks.py"
    "analyze_results.py"
)

for file in "${files_to_v5[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" v5_original/
        echo "  ✓ 移動 $file"
    else
        echo "  - $file 不存在，跳過"
    fi
done

echo ""

# ============================================================
# 步驟 3：移動檔案到 integrated_109/
# ============================================================
echo "[3/8] 移動檔案到 integrated_109/..."

files_to_109=(
    "gaia_109_tasks.json"
    "validation_results_109.json"
    "analysis_report_109.json"
    "integrate_109_tasks.py"
    "run_109_pipeline.py"
    "109_題總結報告.md"
    "PARSER_PARAMETER_CHECK.md"
    "analyze_tools_overlap.py"
)

for file in "${files_to_109[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" integrated_109/
        echo "  ✓ 移動 $file"
    else
        echo "  - $file 不存在，跳過"
    fi
done

echo ""

# ============================================================
# 步驟 4：移動檔案到 data_synthesis/
# ============================================================
echo "[4/8] 移動檔案到 data_synthesis/..."

files_to_synthesis=(
    "chain_to_dag.py"
    "data_augmentation.py"
    "dags.json"
    "augmented_dags.json"
    "toolscale_dataset.json"
    "toolscale_generator.py"
    "chain_to_dag_optimized.log"
)

for file in "${files_to_synthesis[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" data_synthesis/
        echo "  ✓ 移動 $file"
    else
        echo "  - $file 不存在，跳過"
    fi
done

echo ""

# ============================================================
# 步驟 5：移動檔案到 docs/
# ============================================================
echo "[5/8] 移動檔案到 docs/..."

files_to_docs=(
    "IMPROVEMENT_REPORT.md"
    "OPTIMIZATION_LOG.md"
    "白話說明_昨天的優化.md"
    "GAIA_L3_ANALYSIS.md"
)

for file in "${files_to_docs[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" docs/
        echo "  ✓ 移動 $file"
    else
        echo "  - $file 不存在，跳過"
    fi
done

echo ""

# ============================================================
# 步驟 6：移動檔案到 archive/
# ============================================================
echo "[6/8] 移動檔案到 archive/..."

files_to_archive=(
    "parser_v2.1.py"
    "parser_v3_1_bugfix.py"
    "parser_v3_executable.py"
    "parser_v5_old.py"
    "run_executor_v3.py"
    "run_executor_v3.2.py"
    "plans_v2_1.json"
    "plans_v3_executable.json.backup"
    "evaluation_report.json"
    "check_executor.py"
    "verify_v32_output.py"
)

for file in "${files_to_archive[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" archive/
        echo "  ✓ 移動 $file"
    else
        echo "  - $file 不存在，跳過"
    fi
done

echo ""

# ============================================================
# 步驟 7：移動工具相關到 tools/
# ============================================================
echo "[7/8] 移動檔案到 tools/..."

# 複製（不是移動）tools_schema.json，因為可能還有其他檔案在用
if [ -f "tools_schema.json" ]; then
    cp "tools_schema.json" "tools/our_tools_schema.json"
    echo "  ✓ 複製 tools_schema.json → tools/our_tools_schema.json"
    # 保留原檔案，稍後決定是否刪除
fi

if [ -f "tools_mapping.json" ]; then
    mv "tools_mapping.json" tools/
    echo "  ✓ 移動 tools_mapping.json"
fi

if [ -f "extract_tools_schema.py" ]; then
    mv "extract_tools_schema.py" tools/
    echo "  ✓ 移動 extract_tools_schema.py"
fi

echo ""

# ============================================================
# 步驟 8：清理和總結
# ============================================================
echo "[8/8] 清理和總結..."

# 刪除一些明確不需要的檔案
files_to_delete=(
    "重組計劃.md"  # 已經執行，不需要保留
)

for file in "${files_to_delete[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "  ✓ 刪除 $file"
    fi
done

echo ""

# ============================================================
# 總結
# ============================================================
echo "======================================================================="
echo "重組完成！"
echo "======================================================================="
echo ""
echo "資料夾結構："
echo "  v5_original/      - $(ls v5_original/ | wc -l | tr -d ' ') 個檔案"
echo "  ta_99_tasks/      - $(ls ta_99_tasks/ | wc -l | tr -d ' ') 個檔案"
echo "  integrated_109/   - $(ls integrated_109/ | wc -l | tr -d ' ') 個檔案"
echo "  tools/            - $(ls tools/ | wc -l | tr -d ' ') 個檔案"
echo "  data_synthesis/   - $(ls data_synthesis/ | wc -l | tr -d ' ') 個檔案"
echo "  docs/             - $(ls docs/ | wc -l | tr -d ' ') 個檔案"
echo "  archive/          - $(ls archive/ | wc -l | tr -d ' ') 個檔案"
echo ""

echo "保留在根目錄的核心檔案："
ls -1 *.py *.json 2>/dev/null | head -10

echo ""
echo "結束時間：$(date)"
echo ""
echo "下一步："
echo "1. 檢查各資料夾的內容是否正確"
echo "2. 從助教資料夾提取 ta_tools_schema.json"
echo "3. 合併工具 schema，建立 unified_tools_schema.json"
echo ""
