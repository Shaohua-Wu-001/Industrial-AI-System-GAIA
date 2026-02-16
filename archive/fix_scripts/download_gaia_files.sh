#!/bin/bash
# GAIA Level 3 檔案下載腳本
# 自動下載所有需要的檔案

set -e  # 遇到錯誤就停止

echo "=========================================="
echo "GAIA Level 3 檔案下載器"
echo "=========================================="
echo ""

# Hugging Face 基礎 URL
BASE_URL="https://huggingface.co/datasets/gaia-benchmark/GAIA/resolve/main/2023/validation"

# 需要下載的檔案清單
declare -a FILES=(
    "bec74516-02fc-48dc-b202-55e78d0e17cf.jsonld"
    "9b54f9d9-35ee-4a14-b62f-d130ea00317f.zip"
)

# 檢查當前目錄
if [ ! -f "gaia_level3_tasks.json" ]; then
    echo "❌ 錯誤：請在 Delta_GAIA 專案資料夾中執行此腳本"
    exit 1
fi

echo "📂 當前目錄：$(pwd)"
echo ""

# 下載每個檔案
for FILE in "${FILES[@]}"; do
    echo "----------------------------------------"
    echo "📥 正在下載: $FILE"
    
    # 檢查檔案是否已存在
    if [ -f "$FILE" ]; then
        echo "   ✅ 檔案已存在，跳過下載"
        FILE_SIZE=$(ls -lh "$FILE" | awk '{print $5}')
        echo "   📦 檔案大小: $FILE_SIZE"
    else
        echo "   🌐 從 Hugging Face 下載..."
        
        # 使用 curl 下載（macOS 預設有）
        if command -v curl &> /dev/null; then
            curl -L -o "$FILE" "$BASE_URL/$FILE" --progress-bar
            
            if [ $? -eq 0 ]; then
                FILE_SIZE=$(ls -lh "$FILE" | awk '{print $5}')
                echo "   ✅ 下載成功！檔案大小: $FILE_SIZE"
            else
                echo "   ❌ 下載失敗"
                exit 1
            fi
        else
            echo "   ❌ 找不到 curl 命令"
            exit 1
        fi
    fi
    echo ""
done

echo "=========================================="
echo "✅ 所有檔案下載完成！"
echo "=========================================="
echo ""

# 顯示檔案清單
echo "📋 檔案清單："
ls -lh *.jsonld *.zip 2>/dev/null || echo "   (無檔案)"
echo ""

# 建立 data 資料夾（如果不存在）
if [ ! -d "data" ]; then
    mkdir -p data
    echo "📁 已建立 data/ 資料夾"
fi

echo ""
echo "🎯 下一步："
echo "   1. 測試檔案讀取: python3 -c 'import gaia_function as gf; print(gf.read_json(\"bec74516-02fc-48dc-b202-55e78d0e17cf.jsonld\"))'"
echo "   2. 解壓 ZIP: python3 -c 'import gaia_function as gf; print(gf.extract_zip(\"9b54f9d9-35ee-4a14-b62f-d130ea00317f.zip\", \"data/\"))'"
echo "   3. 執行評估: python3 evaluate_system_verified.py"
echo ""
