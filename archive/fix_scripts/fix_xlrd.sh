#!/bin/bash
# GAIA Level 3 - xlrd 版本修復腳本

echo "🔧 修復 xlrd 版本問題"
echo "================================"

# 方案1: 安裝正確的 xlrd 版本（推薦）
echo ""
echo "📦 方案1: 升級到 xlrd 2.0.1"
echo "pip uninstall xlrd -y"
echo "pip install 'xlrd>=2.0.1'"

# 方案2: 使用 openpyxl（更通用，也支援 .xlsx）
echo ""
echo "📦 方案2: 使用 openpyxl（推薦，支援更多格式）"
echo "pip install openpyxl"

echo ""
echo "================================"
echo "✅ 執行其中一個方案後重新測試"
