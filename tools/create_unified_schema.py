#!/usr/bin/env python3
"""
建立統一的工具 Schema
合併助教的工具和我們的工具，確保參數精準對應
"""

import json
from pathlib import Path

def convert_ta_tool_to_openai_format(ta_tool):
    """將助教的工具格式轉換成 OpenAI Function Calling 格式"""

    # 跳過特殊工具
    if ta_tool['tool_id'] in ['reasoning', 'submit_final_answer']:
        return None

    # 建立參數定義
    properties = {}
    required = []

    for arg in ta_tool['arguments_schema']:
        arg_name = arg['name']
        arg_type = arg['type']
        is_required = arg.get('required', False)

        # 建立參數
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
            "name": ta_tool['tool_id'],
            "description": ta_tool['description'],
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }

    return tool_def


def main():
    print("=== 建立統一的工具 Schema ===\n")

    # 讀取助教的工具
    print("[1/4] 讀取助教的工具 schema...")
    with open('ta_tools_schema.json', 'r') as f:
        ta_tools = json.load(f)
    print(f"  ✓ 讀取了 {len(ta_tools)} 個工具\n")

    # 讀取我們的工具
    print("[2/4] 讀取我們的工具 schema...")
    with open('our_tools_schema.json', 'r') as f:
        our_tools = json.load(f)
    print(f"  ✓ 讀取了 {len(our_tools)} 個工具\n")

    # 轉換助教的工具
    print("[3/4] 轉換助教的工具格式...")
    ta_tools_converted = []
    for tool in ta_tools:
        converted = convert_ta_tool_to_openai_format(tool)
        if converted:
            ta_tools_converted.append(converted)
    print(f"  ✓ 轉換了 {len(ta_tools_converted)} 個工具（排除特殊工具）\n")

    # 建立工具名稱對應表
    # 找出重複的工具（優先使用助教的）
    ta_tool_names = {tool['function']['name'] for tool in ta_tools_converted}
    our_tool_names = {tool['function']['name'] for tool in our_tools}

    # 定義精準的對應關係
    tool_mapping = {
        # 助教的 -> 我們的（如果名稱不同但功能相同）
        'calculator': 'calculate',
        'pdf_reader': 'read_pdf',
        'excel_reader': 'read_excel',
        'zip_extractor': 'extract_zip',
        'file_reader': 'read_text_file',
    }

    # 找出我們獨有的工具（排除與助教重複的）
    overlapping_tools = set()
    for ta_name in ta_tool_names:
        # 檢查是否有直接對應
        if ta_name in our_tool_names:
            overlapping_tools.add(ta_name)
        # 檢查是否有映射對應
        elif ta_name in tool_mapping:
            mapped_name = tool_mapping[ta_name]
            if mapped_name in our_tool_names:
                overlapping_tools.add(mapped_name)

    print(f"  重複的工具：{len(overlapping_tools)} 個")
    print(f"  重複列表：{sorted(overlapping_tools)}\n")

    # 保留我們獨有的工具
    our_unique_tools = [
        tool for tool in our_tools
        if tool['function']['name'] not in overlapping_tools
    ]

    print(f"  我們獨有的工具：{len(our_unique_tools)} 個\n")

    # 合併：助教的工具 + 我們獨有的工具
    print("[4/4] 合併工具...")
    unified_tools = ta_tools_converted + our_unique_tools

    print(f"  ✓ 合併完成")
    print(f"  統一後的工具總數：{len(unified_tools)} 個\n")

    # 儲存統一的 schema
    with open('unified_tools_schema.json', 'w', encoding='utf-8') as f:
        json.dump(unified_tools, f, indent=2, ensure_ascii=False)

    print(f"  ✓ 已儲存至：unified_tools_schema.json\n")

    # 顯示統計
    print("=" * 70)
    print("統一後的工具列表")
    print("=" * 70)
    print()

    print("【助教的工具】（14 個）")
    for i, tool in enumerate(ta_tools_converted, 1):
        name = tool['function']['name']
        params = list(tool['function']['parameters']['properties'].keys())
        print(f"  {i:2d}. {name:25s} - 參數：{params}")

    print()
    print("【我們獨有的工具】（{} 個）".format(len(our_unique_tools)))
    for i, tool in enumerate(our_unique_tools, 1):
        name = tool['function']['name']
        params = list(tool['function']['parameters']['properties'].keys())
        params_str = ', '.join(params[:3])
        if len(params) > 3:
            params_str += f', ... ({len(params)} 個)'
        print(f"  {i:2d}. {name:25s} - 參數：{params_str}")

    print()
    print("=" * 70)
    print(f"總計：{len(unified_tools)} 個工具")
    print("=" * 70)

    # 建立參數對應表（用於整合腳本）
    param_mapping = {
        'web_search': {
            'max_results': 'num_results'  # 助教用 max_results，我們用 num_results
        },
        'pdf_reader': {
            'page': 'page_numbers'  # 助教用 page，我們用 page_numbers
        },
        'excel_reader': {
            'sheet': 'sheet_name'  # 助教用 sheet，我們用 sheet_name
        },
        'calculator': {
            'expression': 'expression'  # 相同
        },
        'python_executor': {
            'code': 'code'  # 保持原樣
        }
    }

    # 儲存參數對應表
    with open('parameter_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(param_mapping, f, indent=2, ensure_ascii=False)

    print("\n✓ 已建立參數對應表：parameter_mapping.json")
    print("\n完成！")


if __name__ == "__main__":
    main()
