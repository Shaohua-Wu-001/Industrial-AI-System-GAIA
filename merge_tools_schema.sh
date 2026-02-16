#!/bin/bash
# 提取助教的工具 schema 並合併
# 日期：2026-02-09
#
# 使用方式：
#   bash merge_tools_schema.sh

set -e

echo "=== 提取並合併工具 Schema ==="
echo ""

# 取得當前目錄
DELTA_GAIA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DELTA_GAIA_DIR"

# ============================================================
# 步驟 1：從助教的資料中提取工具 schema
# ============================================================
echo "[1/2] 從助教的資料中提取工具 schema..."

python3 << 'PYTHON_SCRIPT'
import json
import sys

# 讀取助教的第一題，提取工具環境
ta_jsonl_path = "../LLM-planning-main/data/GAIA/gaia.infer/gaia.infer.jsonl"

try:
    with open(ta_jsonl_path, 'r') as f:
        first_task = json.loads(f.readline())
        ta_tools = first_task['tool_environment']

    # 儲存助教的工具 schema
    with open('tools/ta_tools_schema.json', 'w', encoding='utf-8') as f:
        json.dump(ta_tools, f, indent=2, ensure_ascii=False)

    print(f"  ✓ 提取了 {len(ta_tools)} 個工具")
    print(f"  ✓ 已儲存至：tools/ta_tools_schema.json")

    # 顯示工具列表
    print(f"\n  工具列表：")
    for tool in ta_tools:
        print(f"    - {tool['tool_id']}")

except FileNotFoundError:
    print(f"  ✗ 找不到檔案：{ta_jsonl_path}")
    print(f"  請確認助教的資料位置是否正確")
    sys.exit(1)
except Exception as e:
    print(f"  ✗ 錯誤：{e}")
    sys.exit(1)

PYTHON_SCRIPT

echo ""

# ============================================================
# 步驟 2：合併兩邊的工具 schema
# ============================================================
echo "[2/2] 合併工具 schema..."

python3 << 'PYTHON_SCRIPT'
import json

# 讀取助教的工具
with open('tools/ta_tools_schema.json', 'r') as f:
    ta_tools = json.load(f)

# 讀取我們的工具
with open('tools/our_tools_schema.json', 'r') as f:
    our_tools = json.load(f)

print(f"  助教的工具：{len(ta_tools)} 個")
print(f"  我們的工具：{len(our_tools)} 個")
print()

# 建立統一的 schema
# 策略：
# 1. 助教的工具轉換成我們的格式
# 2. 去除重複的工具（優先使用助教的）
# 3. 保留我們獨有的工具

# 轉換助教的工具格式
ta_tools_converted = []
for tool in ta_tools:
    # 跳過特殊工具
    if tool['tool_id'] in ['reasoning', 'submit_final_answer']:
        continue

    # 轉換成我們的格式
    properties = {}
    required = []

    for arg in tool['arguments_schema']:
        arg_name = arg['name']
        arg_type = arg['type']
        is_required = arg.get('required', False)

        # 建立參數定義
        properties[arg_name] = {
            "type": arg_type,
            "description": f"The {arg_name} parameter"
        }

        if is_required:
            required.append(arg_name)

    # 建立工具定義
    tool_def = {
        "type": "function",
        "function": {
            "name": tool['tool_id'],
            "description": tool['description'],
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }

    ta_tools_converted.append(tool_def)

print(f"  助教的工具（轉換後）：{len(ta_tools_converted)} 個")

# 建立工具名稱對應
# 助教的工具名稱 -> 我們的工具名稱（如果雷同）
tool_mapping = {
    'web_search': 'web_search',
    'calculator': 'calculate',
    'pdf_reader': 'read_pdf',
    'excel_reader': 'read_excel',
    'zip_extractor': 'extract_zip',
    'file_reader': 'read_text_file',
}

# 去除我們工具中與助教重複的部分
our_tool_names = {tool['function']['name'] for tool in our_tools}
ta_mapped_names = set(tool_mapping.values())

# 保留我們獨有的工具
our_unique_tools = [
    tool for tool in our_tools
    if tool['function']['name'] not in ta_mapped_names
]

print(f"  我們獨有的工具：{len(our_unique_tools)} 個")
print()

# 合併
unified_tools = ta_tools_converted + our_unique_tools

print(f"  ✓ 合併完成")
print(f"  統一後的工具總數：{len(unified_tools)} 個")
print()

# 儲存統一的 schema
with open('tools/unified_tools_schema.json', 'w', encoding='utf-8') as f:
    json.dump(unified_tools, f, indent=2, ensure_ascii=False)

print(f"  ✓ 已儲存至：tools/unified_tools_schema.json")
print()

# 顯示工具列表
print("  統一後的工具列表：")
for i, tool in enumerate(unified_tools, 1):
    name = tool['function']['name']
    desc = tool['function']['description'][:50]
    source = "助教" if i <= len(ta_tools_converted) else "我們"
    print(f"    {i:2d}. {name:30s} - {desc}... [{source}]")

PYTHON_SCRIPT

echo ""
echo "======================================================================="
echo "工具 Schema 合併完成！"
echo "======================================================================="
echo ""
echo "生成的檔案："
echo "  tools/ta_tools_schema.json       - 助教的工具 schema"
echo "  tools/our_tools_schema.json      - 我們的工具 schema（已存在）"
echo "  tools/unified_tools_schema.json  - 合併後的統一 schema"
echo ""
echo "下一步："
echo "1. 檢查 unified_tools_schema.json 的內容"
echo "2. 更新 Parser v5 以使用統一的 schema"
echo "3. 重新執行 109 題的 Pipeline"
echo ""
